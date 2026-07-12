from __future__ import annotations

from .config import Watch
from .models import Deal


def match_watch(deal: Deal, watch: Watch) -> bool:
    """Vrai si le deal correspond aux critères d'une recherche."""
    title = deal.title.lower()

    if not any(kw in title for kw in watch.keywords):
        return False

    if any(kw in title for kw in watch.exclude):
        return False

    if (
        watch.max_price is not None
        and deal.price is not None
        and deal.price > watch.max_price
    ):
        return False

    return True


def find_matching_watch(deal: Deal, watches: list[Watch]) -> Watch | None:
    """Renvoie la première recherche qui matche le deal, sinon None."""
    for watch in watches:
        if match_watch(deal, watch):
            return watch
    return None
