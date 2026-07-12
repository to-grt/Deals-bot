from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

from .config import load_config
from .filters import find_matching_watch
from .notifier import ConsoleNotifier
from .scrapers import build_scrapers
from .storage import DealStore

log = logging.getLogger("pc_deals_bot")


def run_once(config_path: Path) -> int:
    """Un passage complet : scrape, filtre, notifie. Renvoie le nb de nouveaux deals."""
    config = load_config(config_path)
    store = DealStore(config.database)
    notifier = ConsoleNotifier()
    new_matches = 0

    try:
        for scraper in build_scrapers(config.scrapers):
            try:
                deals = scraper.fetch_deals()
            except Exception:
                log.exception("Échec du scraper %s", scraper.name)
                continue

            log.info("%s : %d deals récupérés", scraper.name, len(deals))

            for deal in deals:
                if store.is_seen(deal.id):
                    continue

                watch = find_matching_watch(deal, config.watches)
                store.save(deal, matched_watch=watch.name if watch else None)

                if watch:
                    notifier.notify(deal, watch.name)
                    new_matches += 1
    finally:
        store.close()

    if new_matches == 0:
        log.info("Aucun nouveau deal correspondant aux critères.")
    return new_matches


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bot de veille des bons plans PC fixe / composants"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "config.yaml",
        help="Chemin du fichier de configuration",
    )
    parser.add_argument(
        "--loop", action="store_true", help="Tourner en continu au lieu d'un seul passage"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Minutes entre deux passages en mode --loop (défaut : 30)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    if not args.loop:
        run_once(args.config)
        return

    log.info("Mode boucle : un passage toutes les %d minutes (Ctrl+C pour arrêter)", args.interval)
    while True:
        try:
            run_once(args.config)
        except Exception:
            log.exception("Erreur pendant le passage, nouvelle tentative au prochain cycle")
        time.sleep(args.interval * 60)


if __name__ == "__main__":
    main()
