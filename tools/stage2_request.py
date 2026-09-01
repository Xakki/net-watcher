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
PROPOSED_EXPIRY = "2026-09-02T10:51:28Z"
REVIEWER_ROLE = "independent-review"
_RUNTIME_CAPABILITY = "stage2-head-2026-09-02"


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
        self._valid = capability == _RUNTIME_CAPABILITY
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


def execute_head(
    plan: RequestPlan,
    *,
    authorization: RuntimeAuthorization | None = None,
    transport: Callable[..., Any] | None = None,
) -> Any:
    """Invoke only an explicitly injected transport; never create one implicitly."""
    if authorization is None or not authorization.valid:
        raise RequestRefusal("explicit runtime authorization is required")
    if transport is None or not callable(transport):
        raise RequestRefusal("explicit transport is required")
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
    return transport(
        method=plan.method,
        host=plan.host,
        path=plan.path,
        allow_redirects=False,
        read_response_body=False,
        timeout_seconds=MAX_WALL_CLOCK_SECONDS,
    )
