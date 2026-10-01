"""Keyword / location matching. Config-driven, deliberately simple."""
from __future__ import annotations

from typing import Any

from .models import Job


class Matcher:
    def __init__(self, cfg: dict[str, Any]):
        kw = cfg.get("keywords", {}) or {}
        self.include = [k.lower() for k in kw.get("include", [])]
        self.exclude = [k.lower() for k in kw.get("exclude", [])]
        # exclude_title: negative words checked against the TITLE ONLY. Use this
        # to kill false positives like "Payment Platform Engineer" without also
        # dropping finance roles whose *description* happens to mention engineers
        # (which a plain `exclude` would, since it scans title + snippet).
        self.exclude_title = [k.lower() for k in kw.get("exclude_title", [])]
        # title_only: require include keywords to appear in the TITLE, not just
        # anywhere in the description (cuts a lot of noise).
        self.title_only = bool(kw.get("title_only", True))
        self.locations = [l.lower() for l in cfg.get("locations", [])]
        self.remote_ok = bool(cfg.get("remote_ok", True))

    def matches(self, job: Job) -> bool:
        # Exclude keywords always apply (drop interns/working students etc.).
        if self.exclude and any(k in job.haystack() for k in self.exclude):
            return False

        title = job.title.lower()
        # Title-only excludes: drop off-domain roles that merely share a keyword
        # (e.g. an engineering role with "payment" in its title).
        if self.exclude_title and any(k in title for k in self.exclude_title):
            return False

        hay = title if self.title_only else job.haystack()
        if self.include and not any(k in hay for k in self.include):
            return False

        # Location filter — skipped for prefiltered sources (Arbeitsagentur
        # already did a radius search, so nearby towns are wanted).
        if self.locations and not job.prefiltered:
            loc = job.location.lower()
            is_remote = "remote" in loc or "anywhere" in loc
            if self.remote_ok and is_remote:
                return True
            if not any(l in loc for l in self.locations):
                return False
        return True

    def score(self, job: Job) -> int:
        """Rough relevance score — higher = more relevant. Explainable on purpose.

        - each include keyword found in the TITLE adds points (multi-word
          phrases like "payment operations" count for more than "payment")
        - a preferred city/country in the location adds points
        - Munich gets an extra nudge (home base)
        """
        title = job.title.lower()
        s = 0
        for kw in self.include:
            if kw in title:
                s += 2 + kw.count(" ")  # phrase bonus
        loc = job.location.lower()
        for l in self.locations:
            if l != "europe" and l in loc:  # a specific place, not the whole continent
                s += 3
                break
        if "munich" in loc or "münchen" in loc:
            s += 2
        return s

    def filter(self, jobs: list[Job]) -> list[Job]:
        """Return matching jobs, most relevant first."""
        matched = [j for j in jobs if self.matches(j)]
        matched.sort(key=self.score, reverse=True)
        return matched
