"""Config loading: YAML for what to search, env for secrets."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent


def _load_env(path: Path) -> None:
    """Minimal .env loader so we don't need python-dotenv as a dependency."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_config(config_path: str | None = None) -> dict[str, Any]:
    _load_env(ROOT / ".env")
    if config_path:
        path = Path(config_path)
    else:
        # Your personal, active search is config.yaml (gitignored — stays local).
        # Fall back to the committed template so a fresh clone runs out of the box.
        path = ROOT / "config.yaml"
        if not path.exists():
            path = ROOT / "config.example.yaml"
    with open(path) as fh:
        cfg = yaml.safe_load(fh) or {}

    # secrets come from env, never from the committed YAML
    cfg.setdefault("telegram", {})
    cfg["telegram"]["bot_token"] = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    cfg["telegram"]["chat_id"] = os.environ.get("TELEGRAM_CHAT_ID", "")
    return cfg
