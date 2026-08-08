import asyncio

from fraudlens.request_limits import RequestBodyLimitMiddleware


def test_body_limit_copies_only_limit_plus_one_from_a_single_large_chunk():
    requested_slices = []
    sent = []

    class _TrackingChunk(bytes):
        def __getitem__(self, key):
            if isinstance(key, slice):
                requested_slices.append(key)
            return super().__getitem__(key)

    async def forbidden_app(scope, receive, send):
        raise AssertionError("oversized body reached the application")

    async def receive():
        return {
            "type": "http.request",
            "body": _TrackingChunk(b"x" * 1_000),
            "more_body": False,
        }

    async def send(message):
        sent.append(message)

    middleware = RequestBodyLimitMiddleware(forbidden_app, path_limits={"/analyze": 4})
    asyncio.run(
        middleware(
            {
                "type": "http",
                "method": "POST",
                "path": "/analyze",
                "headers": [],
                "query_string": b"",
                "http_version": "1.1",
                "scheme": "http",
                "server": ("test", 80),
                "client": ("test", 1),
                "root_path": "",
            },
            receive,
            send,
        )
    )

    assert requested_slices == [slice(None, 5, None)]
    assert sent[0]["status"] == 413


def test_body_limit_handles_an_extremely_large_declared_length_without_integer_parsing():
    sent = []

    async def forbidden_app(scope, receive, send):
        raise AssertionError("oversized declared body reached the application")

    async def forbidden_receive():
        raise AssertionError("oversized declared body was read")

    async def send(message):
        sent.append(message)

    middleware = RequestBodyLimitMiddleware(forbidden_app, path_limits={"/analyze": 4})
    asyncio.run(
        middleware(
            {
                "type": "http",
                "method": "POST",
                "path": "/analyze",
                "headers": [(b"content-length", b"9" * 10_000)],
                "query_string": b"",
                "http_version": "1.1",
                "scheme": "http",
                "server": ("test", 80),
                "client": ("test", 1),
                "root_path": "",
            },
            forbidden_receive,
            send,
        )
    )

    assert sent[0]["status"] == 413
