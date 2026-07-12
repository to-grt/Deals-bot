from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Watch:
    """Une recherche : mots-clés à inclure/exclure et prix plafond."""

    name: str
    keywords: list[str]
    exclude: list[str] = field(default_factory=list)
    max_price: float | None = None


@dataclass
class Config:
    database: Path
    scrapers: dict
    watches: list[Watch]


def load_config(path: str | Path = "config.yaml") -> Config:
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    watches = [
        Watch(
            name=w["name"],
            keywords=[k.lower() for k in w.get("keywords", [])],
            exclude=[k.lower() for k in w.get("exclude", [])],
            max_price=w.get("max_price"),
        )
        for w in raw.get("watches", [])
    ]

    # Le chemin de la base est relatif au fichier de config
    database = path.parent / raw.get("database", "data/deals.db")

    return Config(
        database=database,
        scrapers=raw.get("scrapers", {}),
        watches=watches,
    )
