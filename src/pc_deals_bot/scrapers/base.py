from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Deal

USER_AGENT = "pc-deals-bot/0.1 (veille personnelle de bons plans)"


class BaseScraper(ABC):
    """Interface commune à tous les scrapers de sites de bons plans."""

    name: str

    @abstractmethod
    def fetch_deals(self) -> list[Deal]:
        """Récupère les derniers deals publiés sur le site."""
        ...
