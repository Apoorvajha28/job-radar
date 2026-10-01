"""SQLite-backed 'already seen' state so we only alert on NEW postings."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Iterable

from .models import Job

SCHEMA = """
CREATE TABLE IF NOT EXISTS seen_jobs (
    uid         TEXT PRIMARY KEY,
    source      TEXT,
    title       TEXT,
    company     TEXT,
    location    TEXT,
    url         TEXT,
    posted_at   TEXT,
    first_seen  REAL,
    dupe_key    TEXT
);
CREATE INDEX IF NOT EXISTS idx_seen_first ON seen_jobs(first_seen);
"""


class Store:
    def __init__(self, db_path: str | Path):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.executescript(SCHEMA)
        # migrate older dbs that predate the dupe_key column (must happen
        # before we index that column)
        cols = {r[1] for r in self.conn.execute("PRAGMA table_info(seen_jobs)")}
        if "dupe_key" not in cols:
            self.conn.execute("ALTER TABLE seen_jobs ADD COLUMN dupe_key TEXT")
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_seen_dupe ON seen_jobs(dupe_key)"
        )
        self.conn.commit()

    def new_jobs(self, jobs: Iterable[Job], cross_source: bool = True) -> list[Job]:
        """Return jobs we've never recorded before.

        Dedupes by stable per-posting id always, and additionally by
        normalized title+company (cross-source) when cross_source is True.
        """
        cur = self.conn.cursor()
        fresh: list[Job] = []
        seen_uids: set[str] = set()
        seen_keys: set[str] = set()
        for job in jobs:
            if job.uid in seen_uids or (cross_source and job.dupe_key in seen_keys):
                continue
            seen_uids.add(job.uid)
            seen_keys.add(job.dupe_key)
            if cross_source:
                row = cur.execute(
                    "SELECT 1 FROM seen_jobs WHERE uid = ? OR dupe_key = ? LIMIT 1",
                    (job.uid, job.dupe_key),
                ).fetchone()
            else:
                row = cur.execute(
                    "SELECT 1 FROM seen_jobs WHERE uid = ?", (job.uid,)
                ).fetchone()
            if row is None:
                fresh.append(job)
        return fresh

    def mark_seen(self, jobs: Iterable[Job]) -> None:
        now = time.time()
        self.conn.executemany(
            "INSERT OR IGNORE INTO seen_jobs "
            "(uid, source, title, company, location, url, posted_at, first_seen, dupe_key) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            [
                (j.uid, j.source, j.title, j.company, j.location, j.url,
                 j.posted_at, now, j.dupe_key)
                for j in jobs
            ],
        )
        self.conn.commit()

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM seen_jobs").fetchone()[0]

    def close(self) -> None:
        self.conn.close()
