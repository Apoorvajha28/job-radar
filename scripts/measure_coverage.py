"""Measure source-coverage overlap: what would a CLOUD run (no JobSpy) miss?

Runs the real pipeline for each profile from THIS machine (residential IP, so
the scraped boards work), then compares the full matched set against the
API-only backbone that also works from the cloud (ATS, Arbeitsagentur, Adzuna,
Workday, Amazon). Touches no state, sends nothing.

Usage:
    ./.venv/bin/python scripts/measure_coverage.py                     # both profiles
    ./.venv/bin/python scripts/measure_coverage.py profiles/ml.yaml    # one profile
"""
from __future__ import annotations

import collections
import os
import sys

# Make the repo importable no matter the cwd this is launched from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobradar.config import load_config          # noqa: E402
from jobradar.filters import Matcher             # noqa: E402
from jobradar.sources import collect_all         # noqa: E402


def dedupe(jobs):
    seen_uid, seen_key, out = set(), set(), []
    for j in jobs:
        if j.uid in seen_uid or j.dupe_key in seen_key:
            continue
        seen_uid.add(j.uid)
        seen_key.add(j.dupe_key)
        out.append(j)
    return out


def analyze(path):
    print(f"\n{'='*70}\nPROFILE: {path}\n{'='*70}", flush=True)
    cfg = load_config(path)
    raw = collect_all(cfg)
    matched = Matcher(cfg).filter(raw)

    def grp(src):
        return "jobspy" if src.startswith("jobspy") else src.split(":")[0]

    raw_by = collections.Counter(grp(j.source) for j in raw)
    matched_by = collections.Counter(grp(j.source) for j in matched)

    api = [j for j in matched if not j.source.startswith("jobspy")]
    js = [j for j in matched if j.source.startswith("jobspy")]
    api_keys = {j.dupe_key for j in api}
    api_uids = {j.uid for j in api}

    full = dedupe(matched)
    api_only = dedupe(api)
    js_lost = dedupe([j for j in js
                      if j.dupe_key not in api_keys and j.uid not in api_uids])

    print(f"\nRAW {len(raw)} -> MATCHED {len(matched)} -> deduped FULL {len(full)}")
    print("  raw by source-group:    ", dict(raw_by))
    print("  matched by source-group:", dict(matched_by))
    print(f"\n  FULL (home run):            {len(full)}")
    print(f"  BACKBONE (cloud/API-only):  {len(api_only)}")
    pct = (100 * len(js_lost) / len(full)) if full else 0
    print(f"  >>> LOST on a cloud run:    {len(js_lost)}  ({pct:.0f}% of home)")
    if js_lost:
        print("\n  Sample a cloud run would MISS (up to 15):")
        for j in js_lost[:15]:
            print(f"    - [{j.source}] {j.title} | {j.company} | {j.location}")


if __name__ == "__main__":
    for p in sys.argv[1:] or ["profiles/payments.yaml", "profiles/ml.yaml"]:
        try:
            analyze(p)
        except Exception as exc:  # noqa: BLE001
            print(f"!! {p} failed: {exc}", flush=True)
    print("\nDONE", flush=True)
