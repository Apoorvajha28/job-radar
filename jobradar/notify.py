"""Notification sinks. Telegram now; WhatsApp can slot in later."""
from __future__ import annotations

import html
import logging
import urllib.parse
import urllib.request
from typing import Any

from .models import Job

log = logging.getLogger("jobradar.notify")

TG_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_LEN = 3800  # Telegram hard limit is 4096; leave headroom


def _format(job: Job) -> str:
    title = html.escape(job.title)
    company = html.escape(job.company or "—")
    loc = html.escape(job.location or "—")
    src = html.escape(job.source)
    return (
        f"<b>{title}</b>\n"
        f"{company} · {loc}\n"
        f"<a href=\"{html.escape(job.url)}\">Apply / view</a>  <i>({src})</i>"
    )


def _chunks(jobs: list[Job]) -> list[str]:
    """Pack job cards into messages under the Telegram size limit."""
    messages: list[str] = []
    buf: list[str] = []
    length = 0
    for job in jobs:
        card = _format(job)
        if length + len(card) + 2 > MAX_LEN and buf:
            messages.append("\n\n".join(buf))
            buf, length = [], 0
        buf.append(card)
        length += len(card) + 2
    if buf:
        messages.append("\n\n".join(buf))
    return messages


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id

    @property
    def configured(self) -> bool:
        return bool(self.token and self.chat_id)

    def send(self, jobs: list[Job]) -> None:
        if not jobs:
            return
        header = f"🛰️ <b>{len(jobs)} new job match(es)</b>"
        for i, body in enumerate(_chunks(jobs)):
            text = f"{header}\n\n{body}" if i == 0 else body
            self._post(text)

    def send_text(self, text: str) -> None:
        """Send one plain status message (HTML allowed), e.g. a baseline note."""
        self._post(text)

    def _post(self, text: str) -> None:
        data = urllib.parse.urlencode(
            {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": "true",
            }
        ).encode()
        req = urllib.request.Request(TG_API.format(token=self.token), data=data)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                resp.read()
        except Exception as exc:  # noqa: BLE001 - don't let alerts crash the run
            log.error("Telegram send failed: %s", exc)


class ConsoleNotifier:
    """Dry-run sink: prints matches instead of messaging."""

    configured = True

    def send(self, jobs: list[Job]) -> None:
        if not jobs:
            print("(no new matches)")
            return
        print(f"\n=== {len(jobs)} NEW MATCH(ES) ===")
        for j in jobs:
            print(f"- {j.title} | {j.company} | {j.location}\n  {j.url}  [{j.source}]")

    def send_text(self, text: str) -> None:
        print(text)


def build_notifier(cfg: dict[str, Any], dry_run: bool):
    if dry_run:
        return ConsoleNotifier()
    tg = cfg.get("telegram", {})
    notifier = TelegramNotifier(tg.get("bot_token", ""), tg.get("chat_id", ""))
    if not notifier.configured:
        log.warning("Telegram not configured; falling back to console output.")
        return ConsoleNotifier()
    return notifier
