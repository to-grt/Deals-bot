from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Watch:
    """Une recherche : mots-clés à inclure/exclure, fourchette de prix, sources."""

    name: str
    keywords: list[str]
    exclude: list[str] = field(default_factory=list)
    min_price: float | None = None
    max_price: float | None = None
    # Labels de sources auxquels la recherche se limite (vide = toutes).
    # Un label correspond au champ "label" d'un flux dans la config scrapers.
    sources: list[str] = field(default_factory=list)


@dataclass
class Config:
    database: Path
    scrapers: dict
    notifiers: dict
    watches: list[Watch]


def _expand_env(value):
    """Remplace récursivement les ${VAR} par les variables d'environnement.

    Permet de garder les secrets (webhook Discord, token Telegram) hors du
    fichier de config versionné.
    """
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


def load_config(path: str | Path = "config.yaml") -> Config:
    path = Path(path)
    raw = _expand_env(yaml.safe_load(path.read_text(encoding="utf-8")))

    watches = [
        Watch(
            name=w["name"],
            keywords=[k.lower() for k in w.get("keywords", [])],
            exclude=[k.lower() for k in w.get("exclude", [])],
            min_price=w.get("min_price"),
            max_price=w.get("max_price"),
            sources=list(w.get("sources", [])),
        )
        for w in raw.get("watches", [])
    ]

    # Le chemin de la base est relatif au fichier de config
    database = path.parent / raw.get("database", "data/deals.db")

    return Config(
        database=database,
        scrapers=raw.get("scrapers", {}),
        notifiers=raw.get("notifiers", {}),
        watches=watches,
    )
