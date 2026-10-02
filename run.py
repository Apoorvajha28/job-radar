#!/usr/bin/env python3
"""job-radar entry point: one pass = fetch -> filter -> dedupe -> notify.

Usage:
    python run.py                # real run (Telegram if configured)
    python run.py --dry-run      # print matches, touch nothing, notify no one
    python run.py --config x.yaml
"""
from __future__ import annotations

import argparse
import logging
import sys

from jobradar.config import ROOT, load_config
from jobradar.filters import Matcher
from jobradar.notify import build_notifier
from jobradar.sources import collect_all
from jobradar.store import Store


def main() -> int:
    parser = argparse.ArgumentParser(description="Local-first job-posting monitor")
    parser.add_argument("--config", default=None, help="path to config.yaml")
    parser.add_argument("--dry-run", action="store_true",
                        help="print matches; don't notify or persist state")
    parser.add_argument("--seed", action="store_true",
                        help="mark all current matches as seen WITHOUT notifying "
                             "(establish a baseline so you only get new ones)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("jobradar")

    cfg = load_config(args.config)
    matcher = Matcher(cfg)
    db_path = cfg.get("db_path") or str(ROOT / "data" / "seen.db")
    store = Store(db_path)

    # 1) fetch from every source
    raw = collect_all(cfg)
    log.info("fetched %d raw postings", len(raw))

    # 2) filter by keywords/location (returned most-relevant first)
    matched = matcher.filter(raw)
    min_score = int(cfg.get("min_score", 0))
    if min_score:
        matched = [j for j in matched if matcher.score(j) >= min_score]
    log.info("%d match the filters", len(matched))

    # 3) keep only ones we've never seen (optionally across sources too)
    cross = bool(cfg.get("dedupe_cross_source", True))
    fresh = store.new_jobs(matched, cross_source=cross)
    log.info("%d are new", len(fresh))

    # --seed: establish a baseline, send ONE confirmation, then stop. We mark
    # current matches as seen (so we don't flood with everything already open)
    # but ping once so you know the pipe works instead of staring at silence.
    if args.seed:
        store.mark_seen(fresh)
        tracked = store.count()
        store.close()
        notifier = build_notifier(cfg, dry_run=args.dry_run)
        notifier.send_text(
            "✅ <b>job-radar is live.</b>\n"
            f"Baseline set — now tracking {tracked} current postings. "
            "I'll message you here as soon as a new matching job appears."
        )
        print(f"Seeded {len(fresh)} current postings as 'seen'. "
              "Future runs will only alert on new ones.")
        return 0

    # 4) cap how many we send per run so a backlog trickles in instead of
    #    flooding; the rest stay unseen and come through on later runs.
    cap = int(cfg.get("max_per_run", 0))
    to_send = fresh[:cap] if cap else fresh

    # 5) notify + remember (only what we actually sent)
    notifier = build_notifier(cfg, dry_run=args.dry_run)
    notifier.send(to_send)

    if not args.dry_run:
        store.mark_seen(to_send)
        log.info("state now tracks %d postings", store.count())

    store.close()

    if args.dry_run:
        print(
            f"\n[dry-run] fetched={len(raw)} matched={len(matched)} "
            f"new={len(fresh)} would-send={len(to_send)} "
            f"(nothing persisted, nobody notified)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
