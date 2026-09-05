"""Offline Stage 2 request policy and explicit transport boundary.

This module deliberately contains no network client. Planning is non-executable;
execution is possible only when a caller supplies both an authorization capability
and a transport fixture/adapter.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping

ALLOWED_METHOD = "HEAD"
ALLOWED_HOST = "www.ris.ripe.net"
ALLOWED_PATH = "/dumps-per-rrc-rest/prototype/"
MAX_SELECTOR_HOURS = 744
MAX_WALL_CLOCK_SECONDS = 30 * 60
PROPOSED_EXPIRY = "2026-09-05T10:17:20Z"
REVIEWER_ROLE = "independent-review"
RUNTIME_CAPABILITY = "stage2-head-2026-09-05-60m"


class RequestRefusal(ValueError):
    """Raised when a request cannot be safely planned or explicitly executed."""


@dataclass(frozen=True)
class Stage2Request:
    method: str
    host: str
    path: str
    selector_start: datetime | None = None
    selector_end: datetime | None = None
    allow_redirects: bool = False
    read_response_body: bool = False


@dataclass(frozen=True)
class RequestPlan:
    method: str
    host: str
    path: str
    selector_start: datetime | None
    selector_end: datetime | None
    allow_redirects: bool
    read_response_body: bool
    timeout_seconds: int
    execute: bool
    evidence: Mapping[str, str | int]


class RuntimeAuthorization:
    """Explicit, short-lived local capability required by the transport boundary."""

    def __init__(self, capability: str, *, clock: Callable[[], datetime] | None = None):
        self._valid = capability == RUNTIME_CAPABILITY
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    @property
    def valid(self) -> bool:
        current_time = self._clock()
        return self._valid and current_time < datetime.fromisoformat(PROPOSED_EXPIRY.replace("Z", "+00:00"))


def _require_utc(value: datetime, label: str, *, allow_exclusive_end: bool = False) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise RequestRefusal(f"{label} must be timezone-aware UTC")
    if allow_exclusive_end and value == datetime(2025, 8, 1, tzinfo=timezone.utc):
        return
    if value.year != 2025 or value.month != 7:
        raise RequestRefusal("selector must be inside July 2025 UTC")


def _validate(request: Stage2Request) -> None:
    if request.method != ALLOWED_METHOD:
        raise RequestRefusal("only HEAD is permitted")
    if request.host != ALLOWED_HOST:
        raise RequestRefusal("host is outside the approved RIS boundary")
    if request.path != ALLOWED_PATH:
        raise RequestRefusal("path is outside the approved RIS boundary")
    if request.allow_redirects:
        raise RequestRefusal("redirects are prohibited")
    if request.read_response_body:
        raise RequestRefusal("response bodies are prohibited")
    if request.selector_start is None and request.selector_end is None:
        raise RequestRefusal("selector is required")
    if (request.selector_start is None) != (request.selector_end is None):
        raise RequestRefusal("selector start and end must be supplied together")
    if request.selector_start is not None and request.selector_end is not None:
        _require_utc(request.selector_start, "selector start")
        _require_utc(request.selector_end, "selector end", allow_exclusive_end=True)
        if request.selector_end <= request.selector_start:
            raise RequestRefusal("selector must have positive duration")
        if request.selector_end - request.selector_start > timedelta(hours=MAX_SELECTOR_HOURS):
            raise RequestRefusal("selector exceeds 744 UTC hours")


def plan_request(request: Stage2Request) -> RequestPlan:
    """Validate and return a refusal-by-default plan without performing I/O."""
    _validate(request)
    evidence: Mapping[str, str | int] = {
        "reviewer_role": REVIEWER_ROLE,
        "proposed_expiry": PROPOSED_EXPIRY,
        "max_wall_clock_seconds": MAX_WALL_CLOCK_SECONDS,
        "execution": "refused-by-default",
    }
    return RequestPlan(
        method=request.method,
        host=request.host,
        path=request.path,
        selector_start=request.selector_start,
        selector_end=request.selector_end,
        allow_redirects=request.allow_redirects,
        read_response_body=request.read_response_body,
        timeout_seconds=MAX_WALL_CLOCK_SECONDS,
        execute=False,
        evidence=evidence,
    )


class Stage2TransportAdapter:
    """Fail-closed boundary for an explicitly supplied local transport."""

    def __init__(self, transport: Callable[..., Any]):
        if not callable(transport):
            raise RequestRefusal("explicit transport is required")
        self._transport = transport

    def execute(
        self,
        plan: RequestPlan,
        *,
        authorization: RuntimeAuthorization | None = None,
    ) -> str:
        if not isinstance(plan, RequestPlan):
            raise RequestRefusal("validated request plan is required")
        if plan.execute:
            raise RequestRefusal("execution must remain refused-by-default")
        if authorization is None or not authorization.valid:
            raise RequestRefusal("explicit runtime authorization is required")
        try:
            _validate(
                Stage2Request(
                    method=plan.method,
                    host=plan.host,
                    path=plan.path,
                    selector_start=plan.selector_start,
                    selector_end=plan.selector_end,
                    allow_redirects=plan.allow_redirects,
                    read_response_body=plan.read_response_body,
                )
            )
            if plan.timeout_seconds != MAX_WALL_CLOCK_SECONDS:
                raise RequestRefusal("timeout must be 1800 seconds")
        except RequestRefusal:
            raise
        except Exception as error:
            raise RequestRefusal("invalid request plan") from error

        try:
            transport_result = self._transport(
                scheme="https",
                method=ALLOWED_METHOD,
                host=ALLOWED_HOST,
                path=ALLOWED_PATH,
                selector_start=plan.selector_start,
                selector_end=plan.selector_end,
                allow_redirects=False,
                proxy=None,
                cookies=None,
                automatic_compression=False,
                read_response_body=False,
                timeout_seconds=MAX_WALL_CLOCK_SECONDS,
            )
        except Exception:
            return "transport-failure"

        try:
            if not isinstance(transport_result, Mapping) or set(transport_result) != {"status"}:
                raise RequestRefusal("unexpected transport result")
            status = transport_result["status"]
            if isinstance(status, bool) or not isinstance(status, int):
                raise RequestRefusal("unexpected transport result")
            if 200 <= status < 300:
                return "success"
            if status == 404:
                return "not-found"
            if 300 <= status < 400:
                return "redirect-rejected"
            if 400 <= status < 500:
                return "remote-rejected"
            if 500 <= status < 600:
                return "transport-failure"
            raise RequestRefusal("unexpected transport result")
        except RequestRefusal:
            raise
        except Exception:
            raise RequestRefusal("unexpected transport result")
