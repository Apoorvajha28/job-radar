"""Adzuna — a legitimate job-aggregator REST API (free tier).

Why this exists: Indeed/Google Jobs/LinkedIn are reached only by SCRAPING
(JobSpy), which gets blocked from datacenter IPs (GitHub Actions, any cloud
host). Adzuna aggregates much of that same breadth but through an official API
with an app key, so it works reliably from the cloud too — the piece that makes
a hosted/public deployment viable without proxies.

Free keys: register an app at https://developer.adzuna.com/ (free tier ~250
calls/day). Put them in .env as ADZUNA_APP_ID / ADZUNA_APP_KEY; config.py injects
them so they never live in committed YAML.

This is a keyword+radius SEARCH source (like Arbeitsagentur), so results are
marked prefiltered: they may include nearby towns by design and skip our own
location filter (keyword include/exclude still applies).

Docs: https://developer.adzuna.com/docs/search
"""
from __future__ import annotations

import logging
import urllib.parse

from ..models import Job
from .base import http_json

log = logging.getLogger("jobradar.sources.adzuna")

# Adzuna has one host per supported country; {country} is a 2-letter code.
ENDPOINT = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
# Countries Adzuna serves that are relevant here (Luxembourg is NOT supported —
# Arbeitsagentur covers DE; Adzuna adds DE + AT breadth).
_SUPPORTED = {
    "at", "au", "be", "br", "ca", "ch", "de", "es", "fr", "gb",
    "in", "it", "mx", "nl", "nz", "pl", "sg", "us", "za",
}


def _search(country: str, what: str, where: str, distance: int,
            per_page: int, max_days_old: int, app_id: str, app_key: str) -> list[Job]:
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": per_page,
        "what": what,
        "content-type": "application/json",
    }
    if where:
        params["where"] = where
        params["distance"] = distance      # km
    if max_days_old:
        params["max_days_old"] = max_days_old
    url = ENDPOINT.format(country=country, page=1) + "?" + urllib.parse.urlencode(params)
    data = http_json(url)
    jobs: list[Job] = []
    for r in data.get("results", []):
        jobs.append(
            Job(
                source=f"adzuna:{country}",
                external_id=str(r.get("id") or ""),
                title=r.get("title", ""),
                company=(r.get("company") or {}).get("display_name", ""),
                url=r.get("redirect_url", ""),
                location=(r.get("location") or {}).get("display_name", ""),
                posted_at=r.get("created", ""),
                description=r.get("description", ""),
                prefiltered=True,
                raw={},
            )
        )
    return jobs


def fetch(cfg: dict) -> list[Job]:
    az = (cfg.get("sources", {}) or {}).get("adzuna", {}) or {}
    if not az.get("enabled"):
        return []
    app_id = az.get("app_id", "")
    app_key = az.get("app_key", "")
    if not (app_id and app_key):
        log.info("adzuna enabled but ADZUNA_APP_ID/ADZUNA_APP_KEY not set; skipping")
        return []

    countries = [c.lower() for c in (az.get("countries") or ["de"])]
    where = az.get("location", "")
    distance = int(az.get("distance_km", 30))
    per_page = min(int(az.get("results_per_page", 50)), 50)   # API max is 50
    max_days_old = int(az.get("max_days_old", 7))
    searches = az.get("searches", [])

    out: list[Job] = []
    for country in countries:
        if country not in _SUPPORTED:
            log.warning("adzuna: country '%s' not supported; skipping", country)
            continue
        for what in searches:
            try:
                found = _search(country, what, where, distance, per_page,
                                max_days_old, app_id, app_key)
                log.info("adzuna[%s] '%s' -> %d postings", country, what, len(found))
                out.extend(found)
            except Exception as exc:  # noqa: BLE001 - one search must not sink the run
                log.warning("adzuna[%s] '%s' failed: %s", country, what, exc)
    return out
