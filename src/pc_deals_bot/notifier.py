from __future__ import annotations

import sys

from .models import Deal


class ConsoleNotifier:
    """Affiche les nouveaux deals dans la console.

    Pour aller plus loin : créer une classe avec la même interface `notify()`
    qui envoie vers Discord (webhook), Telegram (bot API) ou e-mail.
    """

    def notify(self, deal: Deal, watch_name: str) -> None:
        # errors="replace" : la console Windows en cp1252 ne connaît pas
        # certains caractères pouvant apparaître dans les titres de deals
        text = f"\n>>> Nouveau deal ({watch_name})\n    {deal}"
        print(text.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(
            sys.stdout.encoding or "utf-8"
        ))
