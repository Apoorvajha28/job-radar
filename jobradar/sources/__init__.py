"""Source registry. Each module exposes fetch(cfg) -> list[Job]."""
from __future__ import annotations

import logging

from ..models import Job
from . import arbeitsagentur, ats, bigtech, boards, workday

log = logging.getLogger("jobradar.sources")

# order is cosmetic; all run every pass
_MODULES = [ats, bigtech, boards, workday, arbeitsagentur]


def collect_all(cfg: dict) -> list[Job]:
    jobs: list[Job] = []
    for mod in _MODULES:
        try:
            jobs.extend(mod.fetch(cfg))
        except Exception as exc:  # noqa: BLE001 - one source must not sink the run
            log.error("source module %s crashed: %s", mod.__name__, exc)
    return jobs
