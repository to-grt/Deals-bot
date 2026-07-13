from __future__ import annotations

from .base import BaseScraper
from .dealabs import DealabsScraper


def build_scrapers(scrapers_config: dict) -> list[BaseScraper]:
    """Instancie les scrapers activés dans la config."""
    scrapers: list[BaseScraper] = []

    dealabs_cfg = scrapers_config.get("dealabs", {})
    if dealabs_cfg.get("enabled"):
        # feed_urls (liste) ou feed_url (simple) : un scraper par flux,
        # le dédoublonnage par id gère les deals présents dans plusieurs flux.
        # Chaque entrée est soit une URL, soit {url: ..., label: ...} pour
        # donner au flux un label de source ciblable par les watches.
        feeds = dealabs_cfg.get("feed_urls") or [dealabs_cfg["feed_url"]]
        for feed in feeds:
            if isinstance(feed, dict):
                scrapers.append(
                    DealabsScraper(feed_url=feed["url"], label=feed.get("label"))
                )
            else:
                scrapers.append(DealabsScraper(feed_url=feed))

    return scrapers
