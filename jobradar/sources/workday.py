"""Workday career sites (public cxs JSON endpoint).

Many big corporations run on Workday (Mastercard, PayPal, ...). Each company
has its own endpoint; find it once from the careers site's network calls:
    https://<tenant>.wdN.myworkdayjobs.com/wday/cxs/<tenant>/<site>/jobs

Workday's own search is broad, so results are NOT marked prefiltered — our
keyword + location filters trim them to relevant roles. `searches` narrows the
fetch server-side first (each string is a separate searchText query).
"""
from __future__ import annotations

import logging

from ..models import Job
from .base import http_json

log = logging.getLogger("jobradar.sources.workday")


def _public_base(endpoint: str) -> str:
    """Turn a cxs endpoint into the human career-site base URL.

    .../wday/cxs/<tenant>/<site>/jobs  ->  https://<host>/<site>
    """
    base, _, rest = endpoint.partition("/wday/cxs/")
    parts = rest.split("/")  # [tenant, site, "jobs"]
    site = parts[1] if len(parts) > 1 else ""
    return f"{base}/{site}"


def _fetch_company(name: str, endpoint: str, searches: list[str],
                   limit: int) -> list[Job]:
    public_base = _public_base(endpoint)
    jobs: list[Job] = []
    for term in (searches or [""]):
        payload = {"appliedFacets": {}, "limit": limit, "offset": 0,
                   "searchText": term}
        data = http_json(endpoint, method="POST", payload=payload)
        for j in data.get("jobPostings", []):
            ext = j.get("externalPath", "")
            req_id = (j.get("bulletFields") or [""])[0]
            jobs.append(
                Job(
                    source=f"workday:{name}",
                    external_id=req_id or ext,
                    title=j.get("title", ""),
                    company=name.title(),
                    url=public_base + ext if ext else public_base,
                    location=j.get("locationsText", ""),
                    posted_at=j.get("postedOn", ""),
                    raw={},
                )
            )
    return jobs


def fetch(cfg: dict) -> list[Job]:
    wd = (cfg.get("sources", {}) or {}).get("workday", {}) or {}
    limit = int(wd.get("limit", 20))
    out: list[Job] = []
    for name, conf in wd.items():
        if name == "limit" or not isinstance(conf, dict):
            continue
        endpoint = conf.get("endpoint")
        if not endpoint:
            continue
        try:
            found = _fetch_company(name, endpoint, conf.get("searches", []), limit)
            log.info("workday %s -> %d postings", name, len(found))
            out.extend(found)
        except Exception as exc:  # noqa: BLE001 - isolate per-company failures
            log.warning("workday %s failed: %s", name, exc)
    return out
