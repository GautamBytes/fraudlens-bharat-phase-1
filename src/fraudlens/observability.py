"""Minimal privacy-safe request observability for the HTTP boundary."""

import json
import logging
from typing import Any, Mapping


REQUEST_LOGGER = logging.getLogger("fraudlens.request")


def configure_request_logging() -> None:
    """Route safe request events through Uvicorn's configured error sink."""

    REQUEST_LOGGER.setLevel(logging.INFO)
    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_logger = logging.getLogger("uvicorn")
    configured_handlers = uvicorn_error_logger.handlers or uvicorn_logger.handlers
    if not REQUEST_LOGGER.handlers and configured_handlers:
        REQUEST_LOGGER.handlers = list(configured_handlers)
        REQUEST_LOGGER.propagate = False


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
