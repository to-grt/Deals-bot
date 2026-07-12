from pc_deals_bot.config import Watch
from pc_deals_bot.filters import find_matching_watch, match_watch
from pc_deals_bot.models import Deal
from pc_deals_bot.scrapers.dealabs import _parse_price


def make_deal(title: str, price: float | None = None) -> Deal:
    return Deal(id="test:1", source="test", title=title, url="http://x", price=price)


def test_match_keyword_and_price():
    watch = Watch(name="GPU", keywords=["rtx 4070"], max_price=600)
    assert match_watch(make_deal("MSI RTX 4070 Super", 549.0), watch)
    assert not match_watch(make_deal("MSI RTX 4070 Super", 699.0), watch)
    assert not match_watch(make_deal("MSI RTX 4060", 300.0), watch)


def test_exclude_keyword():
    watch = Watch(name="PC", keywords=["pc gamer"], exclude=["portable"])
    assert match_watch(make_deal("PC Gamer fixe Ryzen 7", 900.0), watch)
    assert not match_watch(make_deal("PC Gamer portable RTX", 900.0), watch)


def test_unknown_price_still_matches():
    watch = Watch(name="GPU", keywords=["rtx 4070"], max_price=600)
    assert match_watch(make_deal("RTX 4070 en promo", None), watch)


def test_find_matching_watch_returns_first():
    watches = [
        Watch(name="GPU", keywords=["rtx"]),
        Watch(name="PC", keywords=["pc gamer"]),
    ]
    deal = make_deal("PC Gamer avec RTX 4070", 999.0)
    assert find_matching_watch(deal, watches).name == "GPU"
    assert find_matching_watch(make_deal("Clavier mécanique"), watches) is None


def test_parse_price_formats():
    assert _parse_price("Super PC à 699€") == 699.0
    assert _parse_price("GPU 549.99 €") == 549.99
    assert _parse_price("Config 1 299,99€") == 1299.99
    assert _parse_price("Pas de prix ici") is None
