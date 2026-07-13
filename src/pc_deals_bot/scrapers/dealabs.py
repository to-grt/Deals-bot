from __future__ import annotations

import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import requests

from ..models import Deal
from .base import BaseScraper, USER_AGENT

# Prix dans le titre ou la description : "699€", "699.99 €", "1 299,99€"…
_PRICE_RE = re.compile(r"(\d[\d\s.,]*?)\s*€")
_TEMP_RE = re.compile(r"(-?\d+)\s*°")


def _parse_price(text: str) -> float | None:
    m = _PRICE_RE.search(text)
    if not m:
        return None
    raw = m.group(1).replace(" ", "").replace(" ", "")
    # "1.299,99" ou "1299,99" -> notation française ; "699.99" -> notation anglaise
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


class DealabsScraper(BaseScraper):
    """Récupère les deals via le flux RSS de Dealabs.

    Le RSS est la méthode la plus légère et la plus stable : pas de parsing
    HTML fragile, et une seule requête par passage.
    """

    name = "dealabs"

    def __init__(self, feed_url: str, label: str | None = None):
        self.feed_url = feed_url
        # Label de source : permet aux watches de cibler un flux précis
        # (ex. "dealabs-audio"). L'id du deal garde le préfixe "dealabs"
        # pour que le dédoublonnage reste global entre les flux.
        self.label = label or self.name

    def fetch_deals(self) -> list[Deal]:
        resp = requests.get(
            self.feed_url, headers={"User-Agent": USER_AGENT}, timeout=30
        )
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)

        deals = []
        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "")
            if not title or not link:
                continue

            searchable = f"{title} {entry.get('summary', '')}"
            published_at = None
            if entry.get("published"):
                try:
                    published_at = parsedate_to_datetime(entry["published"])
                except (TypeError, ValueError):
                    pass

            temp_match = _TEMP_RE.search(entry.get("summary", ""))

            deals.append(
                Deal(
                    id=f"{self.name}:{entry.get('id', link)}",
                    source=self.label,
                    title=title,
                    url=link,
                    price=_parse_price(searchable),
                    temperature=float(temp_match.group(1)) if temp_match else None,
                    published_at=published_at,
                    fetched_at=datetime.now(timezone.utc),
                )
            )
        return deals
