# RGAA Web Checker

Outil d’analyse d’accessibilité web orienté critères **RGAA** : contrastes, navigation clavier, lecteur d’écran, images, DOM, etc. Les rapports sont générés en Markdown (et PDF selon la configuration du générateur).

## Prérequis

- **Python 3** (voir `requirements.txt`)
- **Chrome** : nécessaire pour le mode **Selenium** ; le mode **Playwright** gère Chromium via ses propres binaires

## Installation rapide

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
```

Scripts utiles (Windows) en cas de souci avec Pillow / lxml : `fix_installation.ps1`, `install_with_conda.ps1`.

## Lancer une analyse

```bash
python main.py https://example.com
```

Sans `--modules`, tous les modules sont activés. Liste **complète** des arguments :

```bash
python main.py -h
```

Variante avec plan d’exécution explicite : `main_ordered.py` (voir `python main_ordered.py -h`).

### Exemples

```bash
python main.py https://example.com --modules contrast dom image
python main.py https://example.com --cookie-banner "Accepter tout"
python main.py https://example.com --cookies "consent=accepted" "analytics=true"
python main.py https://example.com --debug --export-csv
```

### Options utiles

| Option | Description |
|--------|-------------|
| `--engine playwright` | **Défaut.** Chromium intégré ; pour l’instant, seul le module `titles` est pris en charge. |
| `--engine selenium` | Analyse complète avec **Chrome** et **OrderedAccessibilityCrawler**. |
| `--modules` | Sous-ensemble : `contrast`, `dom`, `daltonism`, `tab`, `screen`, `image`, `navigation`, `titles` |
| `--output-dir` | Dossier des images analysées (défaut : `site_images`) |
| `--max-screenshots` | Limite de captures pour la navigation au clavier — **Selenium** (défaut : 50) |
| `--focus-second-screenshot` | **Selenium** : 2e capture par étape de focus (désactivé par défaut = plus rapide) |
| `--focus-second-delay` | **Selenium** : délai avant cette 2e capture en secondes (défaut : 0,5 ; sans effet sans `--focus-second-screenshot`) |
| `--use-hierarchy` | **Selenium** : lecteur d’écran hiérarchique (expérimental) |

Le détail du module **DOM** (batch vs analyse legacy) est décrit dans **`ALIGNEMENT_DOM.md`**.

## Structure du dépôt (aperçu)

```
core/          # Config, crawlers (ordonné, Playwright, etc.)
modules/       # Contrastes, tabulation, lecteur d’écran, images, DOM, titres…
utils/         # Logs, rapports, couleurs, images
main.py        # Point d’entrée principal
report_generator.py
```

## Tests

```bash
python test_crawler.py
```

## Dépendances

Voir **`requirements.txt`** (Selenium, Playwright, Pillow, BeautifulSoup, etc.).

## Contribution

Fork, branche dédiée, pull request — les retours et correctifs sont les bienvenus.
