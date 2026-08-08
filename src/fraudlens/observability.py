"""Minimal privacy-safe request observability for the HTTP boundary."""

import json
import logging
from typing import Any, Mapping


REQUEST_LOGGER = logging.getLogger("fraudlens.request")


def request_log_event(
    *,
    request_id: str,
    method: str,
    route: str,
    status_code: int,
) -> Mapping[str, Any]:
    """Return the deliberately small request log schema.

    Query strings, bodies, headers, client addresses, and concrete path
    parameters are intentionally not accepted by this function.
    """

    return {
        "event": "http_request",
        "method": method,
        "request_id": request_id,
        "route": route,
        "status_code": status_code,
    }


def write_request_log(**values: Any) -> None:
    REQUEST_LOGGER.info(
        json.dumps(request_log_event(**values), sort_keys=True, separators=(",", ":"))
    )
