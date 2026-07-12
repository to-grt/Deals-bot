from __future__ import annotations

from .base import BaseScraper
from .dealabs import DealabsScraper


def build_scrapers(scrapers_config: dict) -> list[BaseScraper]:
    """Instancie les scrapers activés dans la config."""
    scrapers: list[BaseScraper] = []

    dealabs_cfg = scrapers_config.get("dealabs", {})
    if dealabs_cfg.get("enabled"):
        # feed_urls (liste) ou feed_url (simple) : un scraper par flux,
        # le dédoublonnage par id gère les deals présents dans plusieurs flux
        urls = dealabs_cfg.get("feed_urls") or [dealabs_cfg["feed_url"]]
        scrapers.extend(DealabsScraper(feed_url=url) for url in urls)

    return scrapers
