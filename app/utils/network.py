from fastapi import Request


def get_server_url(request: Request) -> str:
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.url.netloc)
    if not host:
        raise RuntimeError("Cannot determine public host")
    return f"{proto}://{host}"
