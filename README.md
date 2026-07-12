# PC Deals Bot

Bot de scraping qui surveille régulièrement les sites de bons plans (Dealabs, etc.)
pour détecter les bonnes affaires sur les PC fixes et composants performants
(GPU, CPU, RAM, SSD, config complète) à prix raisonnable.

## Fonctionnement

1. Les **scrapers** récupèrent les derniers deals (flux RSS Dealabs par défaut).
2. Les **filtres** gardent uniquement les deals qui matchent tes critères
   (mots-clés, prix max) définis dans `config.yaml`.
3. Le **stockage** SQLite mémorise les deals déjà vus pour ne jamais notifier deux fois.
4. Le **notifier** affiche les nouveaux deals (console par défaut, extensible
   vers Discord/Telegram/e-mail).

## Installation

```bash
cd pc-deals-bot
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e .
```

## Utilisation

```bash
# Un seul passage (idéal pour un lancement via le Planificateur de tâches Windows / cron)
python -m pc_deals_bot

# Boucle continue : re-scanne toutes les 30 minutes
python -m pc_deals_bot --loop --interval 30
```

## Configuration

Édite `config.yaml` pour ajuster les recherches : mots-clés à inclure/exclure
et prix maximum par catégorie (GPU, config complète, etc.).

## Ajouter un nouveau site

Crée une classe dans `src/pc_deals_bot/scrapers/` qui hérite de `BaseScraper`
et implémente `fetch_deals()`, puis référence-la dans `scrapers/__init__.py`.

## Bonnes pratiques de scraping

- Privilégier les flux RSS / API officielles quand ils existent.
- Respecter les `robots.txt` et espacer les requêtes (l'intervalle par défaut est de 30 min).
- User-Agent identifiable, pas de parallélisation agressive.
