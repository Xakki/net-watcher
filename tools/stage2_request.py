"""Synthetic-only Stage 2 policy planner and protected SQLite broker core.

No issuer, key, socket, network client, or default database path exists here.
The verifier and transport are injected test boundaries; neither is authority.
"""

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import sqlite3
from pathlib import Path
from typing import Any, Callable, Mapping

ALLOWED_SCHEME = "https"
ALLOWED_METHOD = "HEAD"
ALLOWED_HOST = "www.ris.ripe.net"
ALLOWED_PATH = "/dumps-per-rrc-rest/prototype/"
MAX_SELECTOR_HOURS = 744
MAX_WALL_CLOCK_SECONDS = 30 * 60
SAFETY_MARGIN_SECONDS = 10
MAX_LEASE_TTL_SECONDS = MAX_WALL_CLOCK_SECONDS + SAFETY_MARGIN_SECONDS
OUTCOMES = frozenset({"success", "transport-failure", "not-found", "redirect-rejected", "remote-rejected"})
VALID_STATUSES = frozenset({"issued", "consumed", "revoked"})
PROPOSED_EXPIRY = "2026-09-05T10:17:20Z"
RUNTIME_CAPABILITY = "stage2-head-2026-09-05-60m"


class RequestRefusal(ValueError):
    """Raised for any invalid boundary input or durable transition."""


class RuntimeAuthorization:
    """Synthetic compatibility capability; it never grants network authority."""

    def __init__(self, capability: str, *, clock: Callable[[], datetime] | None = None):
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._valid = type(capability) is str and capability == RUNTIME_CAPABILITY

    @property
    def valid(self) -> bool:
        now = self._clock()
        return self._valid and type(now) is datetime and now.tzinfo is timezone.utc and now < datetime.fromisoformat(PROPOSED_EXPIRY.replace("Z", "+00:00"))


@dataclass(frozen=True)
class Stage2Request:
    method: str
    host: str
    path: str
    selector_start: datetime | None = None
    selector_end: datetime | None = None
    allow_redirects: bool = False
    read_response_body: bool = False
    scheme: str = ALLOWED_SCHEME


@dataclass(frozen=True)
class RequestPlan:
    scheme: str
    method: str
    host: str
    path: str
    selector_start: datetime
    selector_end: datetime
    allow_redirects: bool
    read_response_body: bool
    timeout_seconds: int
    execute: bool
    evidence: Mapping[str, str]
    request_digest: str

    def __post_init__(self):
        _validate_plan(self)


def _exact_text(value: Any, label: str, maximum: int = 256) -> None:
    if type(value) is not str or not value or len(value) > maximum:
        raise RequestRefusal(f"invalid {label}")


def _utc(value: Any, label: str) -> None:
    if type(value) is not datetime or value.tzinfo is not timezone.utc:
        raise RequestRefusal(f"{label} must be timezone-aware UTC")


def _validate_request(request: Any) -> None:
    if type(request) is not Stage2Request:
        raise RequestRefusal("exact request model is required")
    for value, label in ((request.scheme, "scheme"), (request.method, "method"),
                         (request.host, "host"), (request.path, "path")):
        _exact_text(value, label)
    if (request.scheme, request.method, request.host, request.path) != (
            ALLOWED_SCHEME, ALLOWED_METHOD, ALLOWED_HOST, ALLOWED_PATH):
        raise RequestRefusal("request is outside the approved boundary")
    if type(request.allow_redirects) is not bool or request.allow_redirects:
        raise RequestRefusal("redirects are prohibited")
    if type(request.read_response_body) is not bool or request.read_response_body:
        raise RequestRefusal("response bodies are prohibited")
    if request.selector_start is None or request.selector_end is None:
        raise RequestRefusal("selector is required")
    _utc(request.selector_start, "selector start")
    _utc(request.selector_end, "selector end")
    if request.selector_start.year != 2025 or request.selector_start.month != 7:
        raise RequestRefusal("selector must be inside July 2025 UTC")
    if request.selector_end != datetime(2025, 8, 1, tzinfo=timezone.utc) and (
            request.selector_end.year != 2025 or request.selector_end.month != 7):
        raise RequestRefusal("selector must be inside July 2025 UTC")
    if request.selector_end <= request.selector_start:
        raise RequestRefusal("selector must have positive duration")
    if request.selector_end - request.selector_start > timedelta(hours=MAX_SELECTOR_HOURS):
        raise RequestRefusal("selector exceeds 744 UTC hours")


def _plan_values(request: Stage2Request, timeout: int) -> list[Any]:
    return [request.scheme, request.method, request.host, request.path,
            request.selector_start.isoformat(), request.selector_end.isoformat(),
            request.allow_redirects, request.read_response_body, False, timeout]


def _digest(values: Any) -> str:
    return hashlib.sha256(json.dumps(values, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest()


def plan_request(request: Stage2Request) -> RequestPlan:
    _validate_request(request)
    timeout = MAX_WALL_CLOCK_SECONDS
    return RequestPlan(
        scheme=request.scheme, method=request.method, host=request.host, path=request.path,
        selector_start=request.selector_start, selector_end=request.selector_end,
        allow_redirects=False, read_response_body=False, timeout_seconds=timeout,
        execute=False, evidence={"execution": "refused-by-default"},
        request_digest=_digest(_plan_values(request, timeout)),
    )


def _validate_plan(plan: Any) -> None:
    if type(plan) is not RequestPlan:
        raise RequestRefusal("validated refusal-by-default plan is required")
    try:
        if plan.execute is not False or type(plan.timeout_seconds) is not int or plan.timeout_seconds != MAX_WALL_CLOCK_SECONDS:
            raise RequestRefusal("validated refusal-by-default plan is required")
        request = Stage2Request(plan.method, plan.host, plan.path, plan.selector_start,
                               plan.selector_end, plan.allow_redirects, plan.read_response_body, plan.scheme)
        _validate_request(request)
        if type(plan.evidence) is not dict or plan.evidence != {"execution": "refused-by-default"}:
            raise RequestRefusal("invalid request plan")
        if type(plan.request_digest) is not str or plan.request_digest != _digest(_plan_values(request, plan.timeout_seconds)):
            raise RequestRefusal("invalid request plan")
    except RequestRefusal:
        raise
    except Exception:
        raise RequestRefusal("invalid request plan")


@dataclass(frozen=True)
class ApprovalEnvelope:
    version: int
    request_digest: str
    nonce: str
    issued_at: datetime
    not_before: datetime
    expires_at: datetime
    max_transport_deadline: timedelta
    operator_approval_ref: str
    reviewer_approval_ref: str
    policy_version: str
    signature: str

    def __post_init__(self):
        if type(self.version) is not int or self.version != 1:
            raise RequestRefusal("invalid approval version")
        _exact_text(self.request_digest, "approval digest", 64)
        if len(self.request_digest) != 64 or any(c not in "0123456789abcdef" for c in self.request_digest):
            raise RequestRefusal("invalid approval digest")
        for value, label in ((self.nonce, "nonce"), (self.operator_approval_ref, "operator approval"),
                             (self.reviewer_approval_ref, "reviewer approval"),
                             (self.policy_version, "policy version"), (self.signature, "signature")):
            _exact_text(value, label)
        for value, label in ((self.issued_at, "issued_at"), (self.not_before, "not_before"), (self.expires_at, "expires_at")):
            _utc(value, label)
        if self.issued_at > self.not_before or self.not_before >= self.expires_at:
            raise RequestRefusal("invalid approval time ordering")
        if self.expires_at - self.issued_at > timedelta(seconds=MAX_LEASE_TTL_SECONDS):
            raise RequestRefusal("approval lifetime exceeds local maximum")
        if type(self.max_transport_deadline) is not timedelta or self.max_transport_deadline != timedelta(seconds=MAX_WALL_CLOCK_SECONDS):
            raise RequestRefusal("invalid transport deadline")

    def _fields(self, include_signature: bool = True) -> dict[str, Any]:
        fields = {"version": self.version, "request_digest": self.request_digest, "nonce": self.nonce,
                  "issued_at": self.issued_at.isoformat(), "not_before": self.not_before.isoformat(),
                  "expires_at": self.expires_at.isoformat(), "max_transport_deadline_seconds": MAX_WALL_CLOCK_SECONDS,
                  "operator_approval_ref": self.operator_approval_ref, "reviewer_approval_ref": self.reviewer_approval_ref,
                  "policy_version": self.policy_version}
        if include_signature:
            fields["signature"] = self.signature
        return fields

    def canonical_bytes(self) -> bytes:
        return json.dumps(self._fields(), sort_keys=True, separators=(",", ":")).encode("ascii")

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


@dataclass(frozen=True)
class TrustedPrincipal:
    role: str
    name: str

    def __post_init__(self):
        if type(self.role) is not str or self.role not in {"operator", "reviewer"}:
            raise RequestRefusal("invalid trusted principal")
        _exact_text(self.name, "principal name")


@dataclass(frozen=True)
class VerifiedApproval:
    envelope: ApprovalEnvelope
    operator: TrustedPrincipal
    reviewer: TrustedPrincipal
    approved: bool

    def __post_init__(self):
        if type(self.envelope) is not ApprovalEnvelope or type(self.operator) is not TrustedPrincipal or type(self.reviewer) is not TrustedPrincipal:
            raise RequestRefusal("invalid verifier result")
        if self.operator.role != "operator" or self.reviewer.role != "reviewer" or self.operator.name == self.reviewer.name:
            raise RequestRefusal("operator and reviewer separation is required")
        if type(self.approved) is not bool or not self.approved:
            raise RequestRefusal("approval was not granted")


class ApprovalLedger:
    """Durable lease state; its path is always supplied by the caller."""

    def __init__(self, path: str | Path | None = None):
        if path is None or not isinstance(path, (str, Path)):
            raise RequestRefusal("caller-provided SQLite path is required")
        self.path = Path(path)
        try:
            with closing(self._connect()) as db:
                db.execute("CREATE TABLE IF NOT EXISTS leases (nonce PRIMARY KEY, request_digest, issued_us, not_before_us, expires_us, deadline_seconds, status, operator_name, reviewer_name, envelope_digest)")
        except (sqlite3.Error, OSError):
            raise RequestRefusal("ledger unavailable")

    def _connect(self):
        return sqlite3.connect(str(self.path), timeout=1.0, isolation_level=None)

    @staticmethod
    def _us(value: datetime) -> int:
        return int(value.timestamp() * 1_000_000)

    def issue(self, approval: VerifiedApproval) -> None:
        if type(approval) is not VerifiedApproval:
            raise RequestRefusal("invalid verifier result")
        try:
            approval = VerifiedApproval(**approval.__dict__)
            envelope = ApprovalEnvelope(**approval.envelope.__dict__)
        except Exception:
            raise RequestRefusal("invalid verifier result")
        try:
            with closing(self._connect()) as db:
                db.execute("INSERT INTO leases VALUES (?, ?, ?, ?, ?, ?, 'issued', ?, ?, ?)",
                           (envelope.nonce, envelope.request_digest, self._us(envelope.issued_at),
                            self._us(envelope.not_before), self._us(envelope.expires_at),
                            MAX_WALL_CLOCK_SECONDS, approval.operator.name, approval.reviewer.name,
                            envelope.digest()))
        except sqlite3.IntegrityError:
            raise RequestRefusal("nonce already exists")
        except (sqlite3.Error, OSError):
            raise RequestRefusal("ledger unavailable")

    def issue_and_consume(self, approval: VerifiedApproval, now: datetime) -> None:
        """Atomically validate, insert, and consume one approval.

        The issued state exists only inside this transaction; rollback removes it
        on every refusal or SQLite failure.
        """
        if type(approval) is not VerifiedApproval:
            raise RequestRefusal("invalid verifier result")
        try:
            approval = VerifiedApproval(**approval.__dict__)
            envelope = ApprovalEnvelope(**approval.envelope.__dict__)
            _utc(now, "clock")
        except RequestRefusal:
            raise
        except Exception:
            raise RequestRefusal("invalid verifier result")
        db = None
        try:
            db = self._connect()
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO leases VALUES (?, ?, ?, ?, ?, ?, 'issued', ?, ?, ?)",
                       (envelope.nonce, envelope.request_digest, self._us(envelope.issued_at),
                        self._us(envelope.not_before), self._us(envelope.expires_at),
                        MAX_WALL_CLOCK_SECONDS, approval.operator.name, approval.reviewer.name,
                        envelope.digest()))
            row = db.execute("SELECT nonce, request_digest, issued_us, not_before_us, expires_us, deadline_seconds, status, operator_name, reviewer_name, envelope_digest FROM leases WHERE nonce=?", (envelope.nonce,)).fetchone()
            if row is None or len(row) != 10:
                raise RequestRefusal("lease is unavailable")
            if type(row[0]) is not str or not row[0] or row[0] != envelope.nonce:
                raise RequestRefusal("lease is unavailable")
            if type(row[1]) is not str or len(row[1]) != 64 or any(c not in "0123456789abcdef" for c in row[1]) or row[1] != envelope.request_digest:
                raise RequestRefusal("lease is unavailable")
            for value in row[2:6]:
                if type(value) is not int or value < 0:
                    raise RequestRefusal("malformed ledger row")
            if not (row[2] <= row[3] < row[4]) or row[4] - row[2] > MAX_LEASE_TTL_SECONDS * 1_000_000:
                raise RequestRefusal("malformed ledger row")
            if type(row[6]) is not str or row[6] != "issued":
                raise RequestRefusal("malformed ledger row")
            if any(type(value) is not str or not value for value in row[7:9]):
                raise RequestRefusal("malformed ledger row")
            if type(row[9]) is not str or len(row[9]) != 64 or any(c not in "0123456789abcdef" for c in row[9]):
                raise RequestRefusal("malformed ledger row")
            if row[9] != envelope.digest() or row[2] != self._us(envelope.issued_at) or row[3] != self._us(envelope.not_before) or row[4] != self._us(envelope.expires_at) or row[5] != MAX_WALL_CLOCK_SECONDS:
                raise RequestRefusal("lease is unavailable")
            now_us = self._us(now)
            if now_us < row[3] or now_us >= row[4] or row[4] - now_us < (MAX_WALL_CLOCK_SECONDS + SAFETY_MARGIN_SECONDS) * 1_000_000:
                raise RequestRefusal("lease is outside its validity window")
            if db.execute("UPDATE leases SET status='consumed' WHERE nonce=? AND status='issued'", (envelope.nonce,)).rowcount != 1:
                raise RequestRefusal("lease is unavailable")
            db.execute("COMMIT")
        except RequestRefusal:
            if db is not None:
                db.rollback()
            raise
        except sqlite3.IntegrityError:
            if db is not None:
                db.rollback()
            raise RequestRefusal("nonce already exists")
        except (sqlite3.Error, OSError):
            if db is not None:
                db.rollback()
            raise RequestRefusal("ledger unavailable")
        finally:
            if db is not None:
                db.close()

    def consume(self, envelope: ApprovalEnvelope, now: datetime) -> None:
        if type(envelope) is not ApprovalEnvelope:
            raise RequestRefusal("invalid approval envelope")
        try:
            envelope = ApprovalEnvelope(**envelope.__dict__)
        except Exception:
            raise RequestRefusal("invalid approval envelope")
        _utc(now, "clock")
        try:
            with closing(self._connect()) as db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT nonce, request_digest, issued_us, not_before_us, expires_us, deadline_seconds, status, operator_name, reviewer_name, envelope_digest FROM leases WHERE nonce = ?", (envelope.nonce,)).fetchone()
                if row is None or len(row) != 10:
                    raise RequestRefusal("lease is unavailable")
                if type(row[0]) is not str or not row[0] or row[0] != envelope.nonce:
                    raise RequestRefusal("lease is unavailable")
                if type(row[1]) is not str or len(row[1]) != 64 or any(c not in "0123456789abcdef" for c in row[1]) or row[1] != envelope.request_digest:
                    raise RequestRefusal("lease is unavailable")
                for value in row[2:6]:
                    if type(value) is not int or value < 0:
                        raise RequestRefusal("malformed ledger row")
                if not (row[2] <= row[3] < row[4]) or row[4] - row[2] > MAX_LEASE_TTL_SECONDS * 1_000_000:
                    raise RequestRefusal("malformed ledger row")
                if type(row[6]) is not str or row[6] not in VALID_STATUSES:
                    raise RequestRefusal("malformed ledger row")
                for value in row[7:9]:
                    if type(value) is not str or not value:
                        raise RequestRefusal("malformed ledger row")
                if type(row[9]) is not str or len(row[9]) != 64 or any(c not in "0123456789abcdef" for c in row[9]):
                    raise RequestRefusal("malformed ledger row")
                if row[9] != envelope.digest() or row[2] != self._us(envelope.issued_at) or row[3] != self._us(envelope.not_before) or row[4] != self._us(envelope.expires_at) or row[5] != MAX_WALL_CLOCK_SECONDS:
                    raise RequestRefusal("lease is unavailable")
                if row[6] != "issued":
                    raise RequestRefusal("lease is unavailable")
                now_us = self._us(now)
                if now_us < row[3] or now_us >= row[4] or row[4] - now_us < (MAX_WALL_CLOCK_SECONDS + SAFETY_MARGIN_SECONDS) * 1_000_000:
                    raise RequestRefusal("lease is outside its validity window")
                changed = db.execute("UPDATE leases SET status='consumed' WHERE nonce=? AND status='issued'", (envelope.nonce,)).rowcount
                if changed != 1:
                    raise RequestRefusal("lease is unavailable")
                db.execute("COMMIT")
        except RequestRefusal:
            raise
        except (sqlite3.Error, OSError):
            raise RequestRefusal("ledger unavailable")

    def revoke(self, nonce: str) -> None:
        _exact_text(nonce, "nonce")
        try:
            with closing(self._connect()) as db:
                if db.execute("UPDATE leases SET status='revoked' WHERE nonce=? AND status='issued'", (nonce,)).rowcount != 1:
                    raise RequestRefusal("lease is unavailable")
        except RequestRefusal: raise
        except (sqlite3.Error, OSError): raise RequestRefusal("ledger unavailable")

    def status(self, nonce: str) -> str | None:
        _exact_text(nonce, "nonce")
        try:
            with closing(self._connect()) as db:
                row = db.execute("SELECT status FROM leases WHERE nonce=?", (nonce,)).fetchone()
                if row is None: return None
                if type(row[0]) is not str or row[0] not in {"issued", "consumed", "revoked"}:
                    raise RequestRefusal("malformed ledger row")
                return row[0]
        except RequestRefusal: raise
        except (sqlite3.Error, OSError): raise RequestRefusal("ledger unavailable")


@dataclass(frozen=True)
class TransportResult:
    """Synthetic result; a real runtime adapter must enforce the timeout."""
    outcome: str
    timed_out: bool

    def __post_init__(self):
        if type(self.outcome) is not str or self.outcome not in OUTCOMES or type(self.timed_out) is not bool:
            raise RequestRefusal("unexpected transport result")


@dataclass(frozen=True)
class BrokerReceipt:
    outcome: str
    overrun: bool

    def __post_init__(self):
        if type(self.outcome) is not str or self.outcome not in OUTCOMES or type(self.overrun) is not bool:
            raise RequestRefusal("invalid broker receipt")


def _read_monotonic(monotonic: Callable[[], float]) -> float:
    try:
        value = monotonic()
    except Exception:
        raise RequestRefusal("invalid monotonic clock")
    if type(value) not in (int, float) or isinstance(value, bool) or not math.isfinite(value):
        raise RequestRefusal("invalid monotonic clock")
    return value


class ProtectedBroker:
    """Consumes a verified approval durably before one injected synthetic call."""

    def __init__(self, ledger: ApprovalLedger, verifier: Any, transport: Callable[[RequestPlan, int], Any], *, clock: Callable[[], datetime], monotonic: Callable[[], float]):
        if type(ledger) is not ApprovalLedger or not callable(getattr(verifier, "verify", None)) or not callable(transport) or not callable(clock) or not callable(monotonic):
            raise RequestRefusal("invalid broker dependencies")
        self.ledger, self.verifier, self.transport, self.clock, self.monotonic = ledger, verifier, transport, clock, monotonic

    def execute(self, plan: RequestPlan, envelope: ApprovalEnvelope) -> BrokerReceipt:
        _validate_plan(plan)
        if type(envelope) is not ApprovalEnvelope:
            raise RequestRefusal("approval does not bind to request plan")
        try:
            ApprovalEnvelope(**envelope.__dict__)
            digest = envelope.request_digest
        except Exception:
            raise RequestRefusal("invalid approval envelope")
        if digest != plan.request_digest:
            raise RequestRefusal("approval does not bind to request plan")
        try:
            verified = self.verifier.verify(envelope)
        except Exception:
            raise RequestRefusal("approval verification failed")
        if type(verified) is not VerifiedApproval or verified.envelope is not envelope:
            raise RequestRefusal("invalid verifier result")
        now = self.clock()
        _utc(now, "clock")
        if now < envelope.not_before or now >= envelope.expires_at:
            raise RequestRefusal("lease is outside its validity window")
        if envelope.expires_at - now < envelope.max_transport_deadline + timedelta(seconds=SAFETY_MARGIN_SECONDS):
            raise RequestRefusal("lease does not cover transport safety margin")
        preflight_start = _read_monotonic(self.monotonic)
        preflight_end = _read_monotonic(self.monotonic)
        if preflight_end < preflight_start:
            raise RequestRefusal("invalid monotonic clock")
        self.ledger.issue_and_consume(verified, now)
        try:
            raw = self.transport(plan, MAX_WALL_CLOCK_SECONDS)
            if type(raw) is not TransportResult:
                return BrokerReceipt("transport-failure", False)
            return BrokerReceipt("transport-failure", True) if raw.timed_out else BrokerReceipt(raw.outcome, False)
        except Exception:
            return BrokerReceipt("transport-failure", False)


class Stage2TransportAdapter:
    """Validated synthetic transport boundary retained for the stage-two plan."""

    def __init__(self, transport: Callable[..., Any]):
        if not callable(transport):
            raise RequestRefusal("explicit transport is required")
        self._transport = transport

    def __call__(self, plan: RequestPlan, timeout_seconds: int = MAX_WALL_CLOCK_SECONDS) -> TransportResult:
        _validate_plan(plan)
        if type(timeout_seconds) is not int or timeout_seconds != MAX_WALL_CLOCK_SECONDS:
            raise RequestRefusal("invalid transport budget")
        try:
            result = self._transport(
                scheme=ALLOWED_SCHEME, method=ALLOWED_METHOD, host=ALLOWED_HOST, path=ALLOWED_PATH,
                selector_start=plan.selector_start, selector_end=plan.selector_end,
                allow_redirects=False, proxy=None, cookies=None, automatic_compression=False,
                read_response_body=False, timeout_seconds=timeout_seconds,
            )
            if type(result) is not dict or len(result) != 1 or "status" not in result:
                raise RequestRefusal("unexpected transport result")
            status = result["status"]
            if type(status) is not int or not 200 <= status <= 599:
                raise RequestRefusal("unexpected transport result")
            if 200 <= status < 300: outcome = "success"
            elif status == 404: outcome = "not-found"
            elif 300 <= status < 400: outcome = "redirect-rejected"
            elif 400 <= status < 500: outcome = "remote-rejected"
            else: outcome = "transport-failure"
            return TransportResult(outcome, False)
        except RequestRefusal:
            raise
        except Exception:
            return TransportResult("transport-failure", False)

    def execute(self, plan: RequestPlan, *, authorization: RuntimeAuthorization | None = None) -> str:
        if type(authorization) is not RuntimeAuthorization or not authorization.valid:
            raise RequestRefusal("explicit runtime authorization is required")
        return self(plan).outcome
