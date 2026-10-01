"""Job-board coverage via JobSpy (Indeed, Google Jobs, LinkedIn).

Indeed + Google Jobs are the reliable free workhorses. LinkedIn works but
rate-limits hard, so it's opt-in. Google Jobs is also how we catch Apple /
Microsoft / Google / Meta career postings without brittle private APIs.

JobSpy is imported lazily so the rest of the app runs even if it's missing.
"""
from __future__ import annotations

import logging
from typing import Any

from ..models import Job

log = logging.getLogger("jobradar.sources.boards")


def _val(v: Any) -> str:
    """Stringify a DataFrame cell, turning NaN/None into ''."""
    if v is None:
        return ""
    s = str(v)
    return "" if s.lower() in ("nan", "nat", "none") else s


def _scrape(scrape_jobs, **kwargs) -> list[Job]:
    df = scrape_jobs(**kwargs)
    if df is None or len(df) == 0:
        return []
    jobs = []
    for rec in df.to_dict("records"):
        url = _val(rec.get("job_url"))
        if not url:
            continue
        jobs.append(
            Job(
                source=f"jobspy:{_val(rec.get('site')) or 'board'}",
                external_id=url,  # boards give no stable id; the url is it
                title=_val(rec.get("title")),
                company=_val(rec.get("company")),
                url=url,
                location=_val(rec.get("location")),
                posted_at=_val(rec.get("date_posted")),
                description=_val(rec.get("description"))[:500],
                raw={},
            )
        )
    return jobs


def fetch(cfg: dict) -> list[Job]:
    js = (cfg.get("sources", {}) or {}).get("jobspy", {}) or {}
    if not js.get("enabled"):
        return []

    try:
        from jobspy import scrape_jobs
    except Exception as exc:  # noqa: BLE001
        log.warning("jobspy not installed (%s); skipping board sources", exc)
        return []

    sites = js.get("sites", ["indeed", "google"])
    location = js.get("location", "")
    results_wanted = int(js.get("results_wanted", 30))
    hours_old = int(js.get("hours_old", 72))
    country_indeed = js.get("country_indeed", "usa")

    out: list[Job] = []

    # 1) plain keyword sweeps
    for term in js.get("search_terms", []):
        google_term = f"{term} jobs near {location}".strip() if location else f"{term} jobs"
        try:
            found = _scrape(
                scrape_jobs,
                site_name=sites,
                search_term=term,
                google_search_term=google_term,
                location=location or None,
                results_wanted=results_wanted,
                hours_old=hours_old,
                country_indeed=country_indeed,
                linkedin_fetch_description=False,
            )
            log.info("jobspy '%s' -> %d postings", term, len(found))
            out.extend(found)
        except Exception as exc:  # noqa: BLE001
            log.warning("jobspy '%s' failed: %s", term, exc)

    # 2) Company sweep, routed through Google Jobs. Use this for companies
    #    that DON'T expose a clean ATS feed (big corps on Workday, custom
    #    career sites, etc.) — Google Jobs indexes them and links back.
    sweep = js.get("company_sweep", {}) or {}
    companies = sweep.get("companies", [])
    roles = sweep.get("roles") or [js.get("search_terms", ["jobs"])[0]]
    for company in companies:
        for role in roles:
            google_term = f"{role} {company} jobs near {location}".strip()
            try:
                found = _scrape(
                    scrape_jobs,
                    site_name=["google"],
                    search_term=f"{role} {company}",
                    google_search_term=google_term,
                    location=location or None,
                    results_wanted=results_wanted,
                    hours_old=hours_old,
                )
                log.info("jobspy sweep '%s / %s' -> %d", company, role, len(found))
                out.extend(found)
            except Exception as exc:  # noqa: BLE001
                log.warning("jobspy sweep '%s / %s' failed: %s", company, role, exc)

    return out
