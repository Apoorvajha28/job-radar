"""Big Tech career-site adapters.

Reality check (probed Sep 2026): of the FAANG-ish set, only Amazon exposes a
clean, unauthenticated public JSON search API. Apple returns 401, Google's
public careers API 404s, and Microsoft's gated its endpoint. Fighting those
per-company private APIs is the fragile treadmill we want to avoid.

So: Amazon is a native adapter here. Apple / Microsoft / Google / Meta are
covered instead by the Google-Jobs aggregator sweep in boards.py (see the
`bigtech_companies` list in config.yaml), which indexes their career sites and
links straight back to them. Add a native adapter here only if/when one of
those exposes a stable public endpoint again.
"""
from __future__ import annotations

import logging

from ..models import Job
from .base import http_json

log = logging.getLogger("jobradar.sources.bigtech")

AMAZON_BASE = "https://www.amazon.jobs"


def _amazon(query: str, limit: int = 50, sort: str = "recent") -> list[Job]:
    url = (
        f"{AMAZON_BASE}/en/search.json?base_query="
        f"{query.replace(' ', '+')}&result_limit={limit}&sort={sort}"
    )
    data = http_json(url)
    jobs = []
    for j in data.get("jobs", []):
        jobs.append(
            Job(
                source="amazon",
                external_id=str(j.get("id_icims") or j.get("id", "")),
                title=j.get("title", ""),
                company="Amazon",
                url=AMAZON_BASE + j.get("job_path", ""),
                location=j.get("normalized_location")
                or j.get("location", ""),
                posted_at=j.get("posted_date", ""),
                description=j.get("description_short", "")[:500],
                raw=j,
            )
        )
    return jobs


def fetch(cfg: dict) -> list[Job]:
    bt = (cfg.get("sources", {}) or {}).get("bigtech", {}) or {}
    out: list[Job] = []

    amz = bt.get("amazon", {}) or {}
    if amz.get("enabled"):
        for q in amz.get("queries", []):
            try:
                found = _amazon(q, limit=amz.get("limit", 50))
                log.info("amazon '%s' -> %d postings", q, len(found))
                out.extend(found)
            except Exception as exc:  # noqa: BLE001
                log.warning("amazon '%s' failed: %s", q, exc)
    return out
