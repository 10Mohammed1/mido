"""Async HTTP helpers with a small ``requests``-like surface.

Why
---
The original plugins called ``requests.get/post`` directly inside coroutines.
Every such call blocks the *whole* event loop (no other command, no update,
no heartbeat can run while a slow endpoint answers), which is what made the
bot feel laggy and occasionally "freeze".

How
---
``aget`` / ``apost`` / ``arequest`` are drop-in async equivalents built on
``aiohttp``.  They return a tiny ``Response`` object exposing the attributes
the plugins actually used: ``.json()``, ``.text``, ``.content``,
``.status_code``, ``.ok``, ``.headers``, ``.url`` and ``.raise_for_status()``.
"""

from __future__ import annotations

import json as _json
import re
from typing import Any, Optional

import aiohttp

__all__ = ["HTTPStatusError", "Response", "arequest", "aget", "apost", "ahead"]


class HTTPStatusError(aiohttp.ClientError):
    """Raised by :meth:`Response.raise_for_status` for 4xx/5xx answers."""

    def __init__(self, status: int, url: str = "", message: str = "") -> None:
        super().__init__(message or f"HTTP {status} for {url}")
        self.status = status
        self.status_code = status
        self.url = url

_CHARSET_RE = re.compile(r"charset=([\w\-]+)", re.I)
_DEFAULT_TIMEOUT = 40.0


class Response:
    """Minimal stand-in for ``requests.Response``."""

    __slots__ = ("status_code", "headers", "url", "_body", "history", "encoding")

    def __init__(
        self,
        status_code: int,
        headers: Any,
        body: bytes,
        url: str = "",
        encoding: Optional[str] = None,
    ) -> None:
        self.status_code = status_code
        self.headers = headers
        self.url = url
        self._body = body
        self.history: list = []
        self.encoding = encoding or self._guess_encoding()

    # -- body -----------------------------------------------------------------
    def _guess_encoding(self) -> str:
        ctype = ""
        try:
            ctype = self.headers.get("Content-Type", "") or ""
        except Exception:
            pass
        match = _CHARSET_RE.search(ctype)
        return match.group(1) if match else "utf-8"

    @property
    def content(self) -> bytes:
        return self._body

    @property
    def text(self) -> str:
        return self._body.decode(self.encoding, "replace")

    def json(self, **kwargs: Any) -> Any:
        text = self.text.strip() or "null"
        try:
            return _json.loads(text, **kwargs)
        except ValueError:
            # some endpoints return a JSON body prefixed by a callback/extra text
            start = min(
                (i for i in (text.find("{"), text.find("[")) if i != -1),
                default=-1,
            )
            if start > 0:
                return _json.loads(text[start:], **kwargs)
            raise

    # -- status ---------------------------------------------------------------
    @property
    def ok(self) -> bool:
        return self.status_code < 400

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise HTTPStatusError(self.status_code, self.url)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Response [{self.status_code}] {self.url}>"


def _build_form(files: dict, data: Any) -> aiohttp.FormData:
    """Translate a ``requests`` ``files=`` mapping to ``aiohttp.FormData``."""
    form = aiohttp.FormData()
    if isinstance(data, dict):
        for key, value in data.items():
            form.add_field(key, str(value))
    elif isinstance(data, str):
        pass  # multipart only, keep it simple
    for field, value in files.items():
        if isinstance(value, (tuple, list)):
            filename = value[0]
            payload = value[1]
            ctype = value[2] if len(value) > 2 else "application/octet-stream"
            form.add_field(
                field,
                payload,
                filename=filename,
                content_type=ctype,
            )
        else:
            form.add_field(field, value)
    return form


async def arequest(
    method: str,
    url: Optional[str] = None,
    *,
    params: Any = None,
    data: Any = None,
    json: Any = None,
    headers: Any = None,
    cookies: Any = None,
    files: Any = None,
    auth: Any = None,
    timeout: Any = None,
    allow_redirects: bool = True,
    verify: bool = True,
    stream: Any = None,  # accepted for compatibility; body is always read
    **_ignored: Any,
) -> Response:
    """Perform an HTTP request without blocking the event loop."""
    if url is None:
        raise ValueError("arequest() requires a url")

    if files is not None:
        data = _build_form(files, data)
        headers = headers or {}

    if timeout is None:
        client_timeout = aiohttp.ClientTimeout(total=_DEFAULT_TIMEOUT)
    elif isinstance(timeout, (int, float)):
        client_timeout = aiohttp.ClientTimeout(total=float(timeout))
    else:
        client_timeout = timeout

    connector = None
    if verify is False:
        connector = aiohttp.TCPConnector(ssl=False)

    kwargs: dict = {
        "params": params,
        "headers": headers,
        "cookies": cookies,
        "allow_redirects": allow_redirects,
        "timeout": client_timeout,
    }
    if data is not None:
        kwargs["data"] = data
    if json is not None:
        kwargs["json"] = json
    if auth is not None:
        kwargs["auth"] = aiohttp.BasicAuth(*auth) if isinstance(auth, (tuple, list)) else auth

    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.request(method.upper(), url, **kwargs) as resp:
            body = await resp.read()
            return Response(
                status_code=resp.status,
                headers=resp.headers,
                body=body,
                url=str(resp.url),
            )


async def aget(url: Optional[str] = None, **kwargs: Any) -> Response:
    """Async equivalent of ``requests.get``."""
    return await arequest("GET", url, **kwargs)


async def apost(url: Optional[str] = None, **kwargs: Any) -> Response:
    """Async equivalent of ``requests.post``."""
    return await arequest("POST", url, **kwargs)


async def ahead(url: Optional[str] = None, **kwargs: Any) -> Response:
    """Async equivalent of ``requests.head``."""
    return await arequest("HEAD", url, **kwargs)
