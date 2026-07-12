from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Deal:
    """Un bon plan repéré sur un site source."""

    id: str  # identifiant unique (source + id du deal)
    source: str  # ex: "dealabs"
    title: str
    url: str
    price: float | None = None  # en euros, None si non détecté
    temperature: float | None = None  # score communautaire (Dealabs)
    published_at: datetime | None = None
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __str__(self) -> str:
        price = f"{self.price:.2f} €" if self.price is not None else "prix ?"
        temp = f" [{self.temperature:.0f}°]" if self.temperature is not None else ""
        return f"[{self.source}]{temp} {self.title} — {price}\n    {self.url}"
