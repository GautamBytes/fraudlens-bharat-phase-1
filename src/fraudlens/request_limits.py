"""Small ASGI request-body limits for bounded JSON ingestion."""

from typing import Awaitable, Callable, Mapping, MutableMapping

from starlette.responses import JSONResponse


ANALYZE_BODY_MAX_BYTES = 64 * 1024


class RequestBodyLimitMiddleware:
    """Reject oversized bodies before FastAPI buffers and parses their JSON."""

    def __init__(self, app, path_limits: Mapping[str, int]) -> None:
        self.app = app
        self.path_limits = dict(path_limits)

    async def __call__(
        self,
        scope: MutableMapping[str, object],
        receive: Callable[[], Awaitable[MutableMapping[str, object]]],
        send: Callable[[MutableMapping[str, object]], Awaitable[None]],
    ) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        max_bytes = self.path_limits.get(str(scope.get("path", "")))
        if max_bytes is None:
            await self.app(scope, receive, send)
            return

        for name, value in scope.get("headers", []):
            if name == b"content-length" and value.isdigit() and int(value) > max_bytes:
                await self._reject(scope, receive, send)
                return

        body = bytearray()
        while True:
            message = await receive()
            if message.get("type") == "http.request":
                chunk = message.get("body", b"")
                remaining = max_bytes + 1 - len(body)
                if remaining > 0:
                    body.extend(chunk[:remaining])
                if len(body) > max_bytes or len(chunk) > remaining:
                    await self._reject(scope, receive, send)
                    return
                if not message.get("more_body", False):
                    break
            else:
                await self.app(scope, _single_message_receiver(message), send)
                return

        replayed = False

        async def replay_receive():
            nonlocal replayed
            if replayed:
                return {"type": "http.disconnect"}
            replayed = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, replay_receive, send)

    @staticmethod
    async def _reject(scope, receive, send) -> None:
        response = JSONResponse(
            status_code=413,
            content={"detail": "Request body is too large"},
            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
        )
        await response(scope, receive, send)


def _single_message_receiver(message):
    async def receive_once():
        return message

    return receive_once
