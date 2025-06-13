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
├── utils/
│   └── log_utils.py   # Utilitaires de logging
└── main.py           # Point d'entrée de l'application
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

#### 3. Utilitaires (`utils/log_utils.py`)
- Gestion des logs
- Formatage des messages
- Configuration des niveaux de log

#### 4. Point d'Entrée (`main.py`)
- Gestion des arguments en ligne de commande
- Configuration du navigateur Chrome
- Gestion des bannières de cookies
- Orchestration de l'analyse

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
   - Format détaillé
   - Résultats par critère
   - Recommandations d'amélioration

4. **Options de Configuration**
   - Mode debug
   - Choix de l'encodage
   - Personnalisation de l'analyse

## Utilisation

### Installation
```bash
# Installation des dépendances
pip install -r requirements.txt
```

### Exécution
```bash
python main.py <url> [options]

Options:
  --debug              Afficher les logs détaillés
  --encoding ENCODING  Encodage du rapport (utf-8 ou cp1252)
  --cookie-banner TEXT Texte du bouton de la bannière de cookies
```

## Dépendances Principales
- Selenium WebDriver
- ChromeDriver
- webdriver_manager

## Contribution
Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request 