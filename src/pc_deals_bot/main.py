from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

from .config import load_config
from .filters import find_matching_watch
from .notifier import build_notifiers
from .scrapers import build_scrapers
from .storage import DealStore

log = logging.getLogger("pc_deals_bot")


def run_once(config_path: Path) -> int:
    """Un passage complet : scrape, filtre, notifie. Renvoie le nb de nouveaux deals."""
    config = load_config(config_path)
    store = DealStore(config.database)
    notifiers = build_notifiers(config.notifiers)
    new_matches = 0

    try:
        for scraper in build_scrapers(config.scrapers):
            try:
                deals = scraper.fetch_deals()
            except Exception:
                log.exception(
                    "Échec du scraper %s", getattr(scraper, "label", scraper.name)
                )
                continue

            log.info(
                "%s : %d deals récupérés",
                getattr(scraper, "label", scraper.name),
                len(deals),
            )

            for deal in deals:
                if store.is_seen(deal.id):
                    continue

                watch = find_matching_watch(deal, config.watches)
                store.save(deal, matched_watch=watch.name if watch else None)

                if watch:
                    new_matches += 1
                    for notifier in notifiers:
                        try:
                            notifier.notify(deal, watch.name)
                        except Exception:
                            log.exception(
                                "Échec de la notification %s", notifier.name
                            )
    finally:
        store.close()

    if new_matches == 0:
        log.info("Aucun nouveau deal correspondant aux critères.")
    return new_matches


# Le mode --loop ne tourne que sur une plage horaire : inutile de solliciter
# Dealabs (et le Pi) la nuit, un deal tombé à 3h du matin sera vu à 9h.
DEFAULT_INTERVAL_MINUTES = 60
DEFAULT_START_HOUR = 9
DEFAULT_END_HOUR = 20

# Un sommeil de plusieurs heures survit mal à une remise à l'heure ou au
# changement d'heure : on dort par tranches et on recalcule à chaque réveil.
SLEEP_CHUNK_SECONDS = 900


def next_run_at(
    now: datetime, interval_minutes: int, start_hour: int, end_hour: int
) -> datetime:
    """Prochain passage, sur une grille alignée sur l'heure pile.

    Les créneaux partent de start_hour:00 et s'espacent de interval_minutes ;
    le dernier créneau de la journée est celui de end_hour:00. Une fois celui-ci
    passé, on repart à start_hour:00 le lendemain.
    """
    step = timedelta(minutes=interval_minutes)
    slot = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    last = now.replace(hour=end_hour, minute=0, second=0, microsecond=0)

    while slot <= now:
        slot += step

    if slot > last:
        slot = (now + timedelta(days=1)).replace(
            hour=start_hour, minute=0, second=0, microsecond=0
        )
    return slot


def in_window(now: datetime, start_hour: int, end_hour: int) -> bool:
    """Vrai si l'on est dans la plage horaire de veille."""
    return start_hour <= now.hour <= end_hour


def sleep_until(target: datetime) -> None:
    """Attend jusqu'à target, en recalculant le reste à chaque tranche."""
    while True:
        remaining = (target - datetime.now()).total_seconds()
        if remaining <= 0:
            return
        time.sleep(min(remaining, SLEEP_CHUNK_SECONDS))


def _safe_run(config_path: Path) -> None:
    try:
        run_once(config_path)
    except Exception:
        log.exception(
            "Erreur pendant le passage, nouvelle tentative au prochain cycle"
        )


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
        default=DEFAULT_INTERVAL_MINUTES,
        help=(
            "Minutes entre deux passages en mode --loop "
            f"(défaut : {DEFAULT_INTERVAL_MINUTES})"
        ),
    )
    parser.add_argument(
        "--start-hour",
        type=int,
        default=DEFAULT_START_HOUR,
        help=(
            "Heure du premier passage de la journée "
            f"(défaut : {DEFAULT_START_HOUR})"
        ),
    )
    parser.add_argument(
        "--end-hour",
        type=int,
        default=DEFAULT_END_HOUR,
        help=(
            "Heure du dernier passage de la journée "
            f"(défaut : {DEFAULT_END_HOUR})"
        ),
    )
    args = parser.parse_args()

    if not 0 <= args.start_hour <= args.end_hour <= 23:
        parser.error(
            "--start-hour doit être inférieure ou égale à --end-hour, "
            "les deux entre 0 et 23"
        )
    if args.interval < 1:
        parser.error("--interval doit valoir au moins 1 minute")

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    if not args.loop:
        run_once(args.config)
        return

    log.info(
        "Mode boucle : un passage toutes les %d minutes, de %dh à %dh "
        "(Ctrl+C pour arrêter)",
        args.interval,
        args.start_hour,
        args.end_hour,
    )

    # Au démarrage, si l'on est déjà dans la plage, on ne fait pas attendre le
    # créneau suivant : un redémarrage du service donne un passage immédiat.
    if in_window(datetime.now(), args.start_hour, args.end_hour):
        _safe_run(args.config)

    while True:
        target = next_run_at(
            datetime.now(), args.interval, args.start_hour, args.end_hour
        )
        log.info("Prochain passage le %s", target.strftime("%d/%m à %H:%M"))
        sleep_until(target)
        _safe_run(args.config)


if __name__ == "__main__":
    main()
