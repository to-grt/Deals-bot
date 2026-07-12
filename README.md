# PC Deals Bot

> 🤖 Projet *vibe codé* avec [Claude Code](https://claude.com/claude-code).

Bot de veille qui surveille régulièrement les sites de bons plans (Dealabs pour
commencer) afin de dénicher les bonnes affaires sur les **PC fixes et composants
performants** — GPU, CPU, RAM, SSD, configs complètes — à prix raisonnable.
Quand un deal correspond à tes critères, tu es notifié en console, sur Discord
ou sur Telegram.

## Fonctionnement

À chaque passage, le bot enchaîne quatre étapes :

1. **Scraping** — chaque scraper activé récupère les derniers deals publiés.
   Le scraper Dealabs passe par le **flux RSS** du groupe informatique : une
   seule requête par passage, pas de parsing HTML fragile, et plus respectueux
   du site qu'un scraping de pages. Le prix et la "température" (score
   communautaire) sont extraits du titre et du résumé.
2. **Dédoublonnage** — chaque deal vu est enregistré dans une base **SQLite**
   (`data/deals.db`). Un deal déjà rencontré n'est jamais notifié deux fois,
   même si le bot redémarre.
3. **Filtrage** — les deals nouveaux sont comparés aux recherches ("watches")
   de `config.yaml` : le titre doit contenir au moins un mot-clé, aucun mot
   exclu, et le prix détecté ne doit pas dépasser le plafond. Un deal sans prix
   détectable passe le filtre (mieux vaut une fausse alerte qu'un deal raté).
4. **Notification** — chaque deal retenu est envoyé sur tous les canaux
   activés : console, webhook Discord et/ou bot Telegram. L'échec d'un canal
   n'empêche pas les autres de fonctionner.

```
scrapers (RSS) ──> SQLite (déjà vu ?) ──> filtres (mots-clés + prix) ──> notifiers
```

## Mise en marche

### 1. Installation

Prérequis : Python ≥ 3.10.

```bash
git clone https://github.com/<toi>/pc-deals-bot.git
cd pc-deals-bot
python -m venv .venv
.venv\Scripts\activate        # Windows  (Linux/macOS : source .venv/bin/activate)
pip install -e .
```

### 2. Configurer tes recherches

Édite la section `watches` de `config.yaml`. Exemple :

```yaml
watches:
  - name: "Carte graphique"
    keywords: ["rtx 4070", "rx 7800"]   # au moins un doit apparaître dans le titre
    exclude: ["portable", "laptop"]     # aucun ne doit apparaître
    max_price: 600                      # euros ; null = pas de limite
```

### 3. Lancer le bot

```bash
# Un seul passage
python -m pc_deals_bot

# En continu : un scan toutes les 30 minutes
python -m pc_deals_bot --loop --interval 30
```

Pour une exécution automatique sans fenêtre ouverte, planifie `python -m
pc_deals_bot` (un passage) toutes les 30 min via le **Planificateur de tâches
Windows** ou un **cron** Linux.

### 4. Activer les notifications (optionnel)

Par défaut, seule la console est active. Les secrets ne sont pas écrits dans
`config.yaml` (qui est versionné) : le fichier référence des **variables
d'environnement** via la syntaxe `${VAR}`.

**Discord** — crée un webhook (paramètres du salon → Intégrations → Webhooks),
puis :

```yaml
notifiers:
  discord:
    enabled: true
    webhook_url: "${DISCORD_WEBHOOK_URL}"
```

```powershell
$env:DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/…"
python -m pc_deals_bot --loop
```

**Telegram** — crée un bot auprès de [@BotFather](https://t.me/BotFather) (il
donne le token), envoie un message à ton bot, puis récupère ton `chat_id` sur
`https://api.telegram.org/bot<TOKEN>/getUpdates` :

```yaml
notifiers:
  telegram:
    enabled: true
    bot_token: "${TELEGRAM_BOT_TOKEN}"
    chat_id: "${TELEGRAM_CHAT_ID}"
```

```powershell
$env:TELEGRAM_BOT_TOKEN = "123456:ABC-…"
$env:TELEGRAM_CHAT_ID = "123456789"
python -m pc_deals_bot --loop
```

## Structure du projet

```
pc-deals-bot/
├── config.yaml                  # Recherches, scrapers et notifiers
├── data/deals.db                # Base SQLite des deals déjà vus (créée au 1er run)
├── src/pc_deals_bot/
│   ├── main.py                  # Point d'entrée CLI (--loop, --interval, --config)
│   ├── config.py                # Chargement YAML + résolution des ${VAR}
│   ├── models.py                # Dataclass Deal
│   ├── filters.py               # Matching mots-clés / prix
│   ├── storage.py               # Dédoublonnage SQLite
│   ├── notifier.py              # Console, Discord (webhook), Telegram (bot)
│   └── scrapers/
│       ├── base.py              # Interface BaseScraper
│       └── dealabs.py           # Flux RSS Dealabs + extraction prix/température
└── tests/                       # pytest
```

## Ajouter un site de bons plans

1. Crée `src/pc_deals_bot/scrapers/monsite.py` avec une classe qui hérite de
   `BaseScraper` et implémente `fetch_deals() -> list[Deal]`.
2. Référence-la dans `build_scrapers()` (`scrapers/__init__.py`).
3. Ajoute sa config dans la section `scrapers` de `config.yaml`.

## Tests

```bash
pip install -e .[dev]
pytest
```

## Bonnes pratiques de scraping

- Privilégier les flux RSS / API officielles quand ils existent.
- Respecter les `robots.txt` et espacer les requêtes (30 min par défaut).
- User-Agent identifiable, pas de parallélisation agressive.
