from __future__ import annotations

from .base import BaseScraper
from .dealabs import DealabsScraper


def build_scrapers(scrapers_config: dict) -> list[BaseScraper]:
    """Instancie les scrapers activés dans la config."""
    scrapers: list[BaseScraper] = []

    dealabs_cfg = scrapers_config.get("dealabs", {})
    if dealabs_cfg.get("enabled"):
        scrapers.append(DealabsScraper(feed_url=dealabs_cfg["feed_url"]))

    return scrapers
