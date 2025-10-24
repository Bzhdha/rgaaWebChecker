# RGAA Web Checker

## Présentation
RGAA Web Checker est un outil d'analyse d'accessibilité web qui permet de vérifier la conformité des sites web selon les critères RGAA (Référentiel Général d'Amélioration de l'Accessibilité).

## Architecture

### Structure du Projet
```
rgaaWebChecker/
├── core/
│   ├── config.py      # Configuration de l'application
│   └── crawler.py     # Moteur d'analyse d'accessibilité
├── modules/
│   ├── contrast_checker.py  # Vérification des contrastes
│   ├── color_simulator.py   # Simulation de daltonisme
│   ├── tab_navigator.py     # Navigation par tabulation
│   ├── screen_reader.py     # Analyse pour lecteurs d'écran
│   ├── dom_analyzer.py      # Analyse du DOM
│   └── image_analyzer.py    # Analyse des images
├── utils/
│   ├── log_utils.py         # Utilitaires de logging
│   ├── report_converter.py  # Conversion des rapports
│   ├── progress_display.py  # Affichage de la progression
│   ├── image_utils.py       # Utilitaires pour les images
│   └── color_utils.py       # Utilitaires pour les couleurs
├── main.py                  # Point d'entrée de l'application
├── report_generator.py      # Génération de rapports (Markdown/PDF)
├── test_crawler.py          # Tests unitaires
├── requirements.txt         # Dépendances du projet
├── install.sh               # Script d'installation
├── activate_venv.sh         # Script d'activation de l'environnement virtuel
└── deactivate_venv.sh       # Script de désactivation de l'environnement virtuel
```

### Composants Principaux

#### 1. Configuration (`core/config.py`)
- Gestion des paramètres de l'application
- Configuration des règles d'accessibilité
- Paramètres de navigation et d'analyse

#### 2. Crawler (`core/crawler.py`)
- Moteur principal d'analyse d'accessibilité
- Navigation sur les pages web
- Analyse des éléments selon les critères RGAA
- Génération des rapports

#### 3. Modules d'Analyse (`modules/`)
- **Contrast Checker** : Vérification des contrastes de couleurs
- **Color Simulator** : Simulation de daltonisme
- **Tab Navigator** : Analyse de la navigation par tabulation
- **Screen Reader** : Analyse pour les lecteurs d'écran
- **DOM Analyzer** : Analyse du DOM pour les problèmes d'accessibilité
- **Image Analyzer** : Analyse des images (alt, contraste, etc.)

#### 4. Utilitaires (`utils/`)
- **Log Utils** : Gestion des logs et formatage des messages
- **Report Converter** : Conversion des rapports en différents formats
- **Progress Display** : Affichage de la progression de l'analyse
- **Image Utils** : Utilitaires pour l'analyse des images
- **Color Utils** : Utilitaires pour l'analyse des couleurs

#### 5. Point d'Entrée (`main.py`)
- Gestion des arguments en ligne de commande
- Configuration du navigateur Chrome
- Gestion des bannières de cookies
- Orchestration de l'analyse

#### 6. Génération de Rapports (`report_generator.py`)
- Génération de rapports en Markdown
- Conversion en PDF
- Statistiques et résultats détaillés

#### 7. Tests (`test_crawler.py`)
- Tests unitaires pour les modules d'analyse
- Utilisation de `unittest`

### Fonctionnalités Principales

1. **Analyse d'Accessibilité**
   - Vérification des critères RGAA
   - Navigation automatique
   - Détection des problèmes d'accessibilité

2. **Gestion des Bannières de Cookies**
   - Détection automatique
   - Interaction avec les bannières
   - Gestion des popups

3. **Génération de Rapports**
   - Format détaillé (Markdown)
   - Conversion en PDF
   - Résultats par critère
   - Recommandations d'amélioration

4. **Options de Configuration**
   - Mode debug
   - Choix de l'encodage
   - Personnalisation de l'analyse
   - Activation/désactivation des modules

## Utilisation

### Installation
```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel (Windows)
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Ou utiliser le script d'installation
./install.sh
```

### Dépannage des problèmes d'installation

Si vous rencontrez des erreurs lors de l'installation des dépendances (notamment avec Pillow ou lxml), voici les solutions dans l'ordre de priorité :

#### Solution 1 : Script de dépannage automatique
```powershell
# Après avoir activé l'environnement virtuel
.\fix_installation.ps1
```

#### Solution 2 : Installation avec conda (recommandé)
Si vous avez Anaconda ou Miniconda installé :
```powershell
# Après avoir activé l'environnement virtuel
.\install_with_conda.ps1
```

#### Solution 3 : Installation de Chrome (si erreur "Chrome not found")
```bash
# Installation automatique de Chrome
chmod +x install_chrome.sh
./install_chrome.sh
```

Alternatives si Chrome ne peut pas être installé :
```bash
python main.py <url> [options]

Options:
  --debug              Afficher les logs détaillés
  --encoding ENCODING  Encodage du rapport (utf-8 ou cp1252)
  --cookie-banner TEXT Texte du bouton de la bannière de cookies
  --cookies COOKIES    Cookies de consentement au format "nom=valeur" (ex: "consent=accepted" "analytics=true")
  --modules MODULES    Liste des modules à activer (contrast, dom, daltonism, tab, screen, image)
  --output-dir DIR     Répertoire de sortie pour les images (défaut: site_images)
```

### Exemples d'utilisation

```bash
# Analyse basique
python main.py https://example.com

# Avec cookies de consentement
python main.py https://example.com --cookies "consent=accepted" "analytics=true" "marketing=false"

# Avec gestion de bannière de cookies
python main.py https://example.com --cookie-banner "Accepter tout"

# Analyse avec modules spécifiques
python main.py https://example.com --modules contrast dom image

# Mode debug avec cookies personnalisés
python main.py https://example.com --debug --cookies "cookie_consent=1" "preferences=all"
```

### Tests
```bash
# Exécuter les tests unitaires
python test_crawler.py
```

## Dépendances Principales
- Selenium WebDriver
- ChromeDriver
- webdriver_manager
- Pillow
- markdown
- pdfkit
- beautifulsoup4
- requests
- lxml

## Contribution
Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request 