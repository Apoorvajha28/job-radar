# Contributing to job-radar

Thanks for your interest! job-radar is a small, dependency-light Python project
and contributions are welcome.

## Design principles

- **The code is generic; your search is data.** All personal choices
  (keywords, companies, location, schedule) live in `config.yaml`, which is
  gitignored. Never hard-code a company, keyword, or location in the Python.
- **Config over code.** If a user can express it in YAML, it belongs in
  `config.yaml`, not in a source file.
- **Each source is isolated.** A source adapter that fails must only log a
  warning — never crash the run. See `jobradar/sources/base.py`.
- **No heavy dependencies.** Standard library first (we use stdlib `urllib`,
  not `requests`). Only `PyYAML` and the optional `python-jobspy` are required.

## Adding a new source

1. Create `jobradar/sources/<name>.py` with a `fetch(cfg) -> list[Job]`.
2. Emit normalized `Job` objects (see `jobradar/models.py`). Set
   `prefiltered=True` if the source already does a server-side location search.
3. Register the module in `jobradar/sources/__init__.py`.
4. Add a documented block to `config.example.yaml` and a row to
   `docs/SOURCES.md`.

Good free sources still on the wishlist are listed in
[`docs/SOURCES.md`](docs/SOURCES.md) (SmartRecruiters, Recruitee, Workable,
Teamtailor, RemoteOK, EURES, …).

## Pull requests

- Keep PRs focused and small.
- Run `./.venv/bin/python run.py --dry-run` before submitting.
- Don't commit `config.yaml`, `.env`, or anything under `data/`.
