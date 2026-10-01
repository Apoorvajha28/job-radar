"""Shared HTTP helpers and the source contract."""
from __future__ import annotations

import json
import logging
import time
import urllib.request
from typing import Any

log = logging.getLogger("jobradar.sources")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) job-radar/0.1"
TIMEOUT = 40          # some feeds (e.g. Stripe's) are large and slow
RETRIES = 2           # extra attempts after the first, with backoff


def http_json(
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    """GET/POST a URL and parse JSON. Retries on transient network errors."""
    body = json.dumps(payload).encode() if payload is not None else None
    hdrs = {"User-Agent": UA, "Accept": "application/json"}
    if payload is not None:
        hdrs["Content-Type"] = "application/json"
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)

    last_exc: Exception | None = None
    for attempt in range(RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8", errors="replace"))
        except Exception as exc:  # noqa: BLE001 - retry any transient failure
            last_exc = exc
            if attempt < RETRIES:
                time.sleep(1.5 * (attempt + 1))  # 1.5s, then 3s
    raise last_exc  # type: ignore[misc]
