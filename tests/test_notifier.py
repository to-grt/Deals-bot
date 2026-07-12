from pc_deals_bot.models import Deal
from pc_deals_bot.notifier import (
    ConsoleNotifier,
    DiscordNotifier,
    TelegramNotifier,
    _format_message,
    build_notifiers,
)


def make_deal(title: str, price: float | None = None) -> Deal:
    return Deal(id="test:1", source="test", title=title, url="http://x", price=price)


def test_format_message_contains_essentials():
    msg = _format_message(make_deal("RTX 4070 Super", 549.0), "Carte graphique")
    assert "Carte graphique" in msg
    assert "RTX 4070 Super" in msg
    assert "549.00" in msg
    assert "http://x" in msg


def test_build_notifiers_default_console_only():
    notifiers = build_notifiers({})
    assert len(notifiers) == 1
    assert isinstance(notifiers[0], ConsoleNotifier)


def test_build_notifiers_all_enabled():
    notifiers = build_notifiers(
        {
            "console": {"enabled": True},
            "discord": {"enabled": True, "webhook_url": "https://discord.test/hook"},
            "telegram": {"enabled": True, "bot_token": "123:abc", "chat_id": "42"},
        }
    )
    assert {type(n) for n in notifiers} == {
        ConsoleNotifier,
        DiscordNotifier,
        TelegramNotifier,
    }


def test_build_notifiers_skips_unresolved_env_placeholder():
    # ${VAR} non résolue -> le notifier est ignoré au lieu de planter
    notifiers = build_notifiers(
        {
            "console": {"enabled": False},
            "discord": {"enabled": True, "webhook_url": "${DISCORD_WEBHOOK_URL}"},
        }
    )
    assert notifiers == []
