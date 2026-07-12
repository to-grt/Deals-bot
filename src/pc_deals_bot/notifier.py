from __future__ import annotations

import logging
import sys
from abc import ABC, abstractmethod

import requests

from .models import Deal

log = logging.getLogger("pc_deals_bot")


def _format_message(deal: Deal, watch_name: str) -> str:
    price = f"{deal.price:.2f} €" if deal.price is not None else "prix non détecté"
    temp = f" ({deal.temperature:.0f}°)" if deal.temperature is not None else ""
    return (
        f"🔥 Nouveau deal — {watch_name}\n"
        f"{deal.title}{temp}\n"
        f"💶 {price}\n"
        f"{deal.url}"
    )


class BaseNotifier(ABC):
    """Interface commune : chaque canal de notification implémente notify()."""

    name: str

    @abstractmethod
    def notify(self, deal: Deal, watch_name: str) -> None: ...


class ConsoleNotifier(BaseNotifier):
    """Affiche les nouveaux deals dans la console."""

    name = "console"

    def notify(self, deal: Deal, watch_name: str) -> None:
        # errors="replace" : la console Windows en cp1252 ne connaît pas
        # certains caractères pouvant apparaître dans les titres de deals
        encoding = sys.stdout.encoding or "utf-8"
        text = "\n" + _format_message(deal, watch_name)
        print(text.encode(encoding, errors="replace").decode(encoding))


class DiscordNotifier(BaseNotifier):
    """Envoie les deals sur un salon Discord via un webhook.

    Créer le webhook : paramètres du salon > Intégrations > Webhooks.
    """

    name = "discord"

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def notify(self, deal: Deal, watch_name: str) -> None:
        resp = requests.post(
            self.webhook_url,
            json={"content": _format_message(deal, watch_name)},
            timeout=15,
        )
        resp.raise_for_status()


class TelegramNotifier(BaseNotifier):
    """Envoie les deals sur Telegram via un bot.

    Créer le bot avec @BotFather (qui donne le token), puis récupérer son
    chat_id en écrivant au bot et en consultant
    https://api.telegram.org/bot<TOKEN>/getUpdates
    """

    name = "telegram"

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = str(chat_id)

    def notify(self, deal: Deal, watch_name: str) -> None:
        resp = requests.post(
            f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
            json={
                "chat_id": self.chat_id,
                "text": _format_message(deal, watch_name),
                "disable_web_page_preview": False,
            },
            timeout=15,
        )
        resp.raise_for_status()


def build_notifiers(notifiers_config: dict) -> list[BaseNotifier]:
    """Instancie les notifiers activés dans la config.

    Un notifier activé mais mal configuré (URL/token manquant, valeur
    ${ENV_VAR} non résolue) est ignoré avec un avertissement plutôt que de
    faire planter le bot.
    """
    notifiers: list[BaseNotifier] = []

    def _valid(value: str | None) -> bool:
        return bool(value) and not str(value).startswith("$")

    console_cfg = notifiers_config.get("console", {"enabled": True})
    if console_cfg.get("enabled", True):
        notifiers.append(ConsoleNotifier())

    discord_cfg = notifiers_config.get("discord", {})
    if discord_cfg.get("enabled"):
        url = discord_cfg.get("webhook_url")
        if _valid(url):
            notifiers.append(DiscordNotifier(webhook_url=url))
        else:
            log.warning("Notifier Discord activé mais webhook_url manquant — ignoré")

    telegram_cfg = notifiers_config.get("telegram", {})
    if telegram_cfg.get("enabled"):
        token = telegram_cfg.get("bot_token")
        chat_id = telegram_cfg.get("chat_id")
        if _valid(token) and _valid(chat_id):
            notifiers.append(TelegramNotifier(bot_token=token, chat_id=chat_id))
        else:
            log.warning(
                "Notifier Telegram activé mais bot_token/chat_id manquant — ignoré"
            )

    return notifiers
