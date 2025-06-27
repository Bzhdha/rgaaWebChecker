# RGAA Web Checker

## Présentation
RGAA Web Checker est un outil d'analyse d'accessibilité web qui permet de vérifier la conformité des sites web selon les critères RGAA (Référentiel Général d'Amélioration de l'Accessibilité).

## Installation et Configuration

### Prérequis
- Python 3.7 ou supérieur
- PowerShell (pour Windows)
- Chrome ou Chromium installé

### Installation avec PowerShell (Windows)

#### 1. Configuration de la politique d'exécution PowerShell
Avant d'utiliser les scripts PowerShell, vous devez autoriser l'exécution de scripts locaux. Ouvrez PowerShell en tant qu'administrateur et exécutez :

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Cette commande permet l'exécution de scripts locaux tout en maintenant la sécurité pour les scripts téléchargés.

#### 2. Activation de l'environnement virtuel
Le projet inclut des scripts PowerShell pour gérer automatiquement l'environnement virtuel :

```powershell
# Activer l'environnement virtuel (création automatique si nécessaire)
.\activate_venv.ps1
```

Ce script :
- Crée automatiquement l'environnement virtuel s'il n'existe pas
- Active l'environnement virtuel
- Installe automatiquement les dépendances depuis `requirements.txt`

#### 3. Désactivation de l'environnement virtuel
```powershell
# Désactiver l'environnement virtuel
.\deactivate_venv.ps1
```

### Installation sur Ubuntu/Linux

#### 1. Installation automatique (recommandé)
```bash
# Rendre le script exécutable
chmod +x install_ubuntu.sh

# Exécuter le script d'installation
./install_ubuntu.sh
```

Ce script :
- Installe tous les prérequis système (python3-venv, dépendances de compilation)
- Crée l'environnement virtuel
- Installe toutes les dépendances Python

#### 2. Installation de Chrome (requis pour Selenium)
```bash
# Rendre le script exécutable
chmod +x install_chrome.sh

# Exécuter le script d'installation de Chrome
./install_chrome.sh
```

Ce script :
- Installe Google Chrome depuis le dépôt officiel
- Configure les dépendances nécessaires
- Configure automatiquement le mode headless pour WSL
- Crée des logs détaillés dans `chrome_install.log`

#### 3. Installation de Chromium (alternative à Chrome)
```bash
# Rendre le script exécutable
chmod +x install_chromium.sh

# Exécuter le script d'installation de Chromium
./install_chromium.sh
```

Ce script :
- Installe Chromium depuis les dépôts Ubuntu
- Configure les dépendances X11 pour WSL
- Crée un alias `chromium` pour faciliter l'utilisation
- Crée des logs détaillés dans `chromium_install.log`

**Note :** Chrome et Chromium sont compatibles avec le même ChromeDriver, vous pouvez utiliser l'un ou l'autre.

#### 4. Activation manuelle
```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances (si pas déjà fait)
pip install -r requirements.txt
```

#### 4. Désactivation
```bash
# Désactiver l'environnement virtuel
deactivate
```

### Installation manuelle (Alternative)
Si vous préférez une installation manuelle :

```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel (Windows)
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
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
# Utiliser Chromium à la place
chmod +x install_chromium.sh
./install_chromium.sh

# Ou utiliser Firefox
sudo apt install firefox
```

#### Solution 4 : Installation manuelle des prérequis
```bash
# Mettre à jour les paquets
sudo apt update

# Installer les prérequis Python
sudo apt install -y python3 python3-pip python3-venv python3-full

# Installer les dépendances de compilation
sudo apt install -y python3-dev build-essential libxml2-dev libxslt1-dev
sudo apt install -y libjpeg-dev libpng-dev libfreetype6-dev liblcms2-dev
```

#### Solution 5 : Erreur DevToolsActivePort (WSL + Chromium)
Si vous obtenez l'erreur "DevToolsActivePort file doesn't exist" sur WSL avec Chromium :

```bash
# Nettoyer le cache webdriver-manager
chmod +x clean_webdriver_cache.sh
./clean_webdriver_cache.sh
```

Ce script :
- Nettoie le cache webdriver-manager corrompu
- Vérifie les permissions du ChromeDriver
- Teste la configuration Chromium
- Crée des logs détaillés

#### Solution 6 : Erreur "Exec format error" ChromeDriver
Si vous obtenez l'erreur "Exec format error" avec le ChromeDriver :

```bash
# Correction spécifique du ChromeDriver
chmod +x fix_chromedriver.sh
./fix_chromedriver.sh
```

Ce script :
- Nettoie complètement le cache webdriver-manager
- Réinstalle webdriver-manager
- Corrige les permissions du ChromeDriver
- Teste le fonctionnement complet
- Identifie et corrige les fichiers corrompus

#### Solution 7 : Erreur de version ChromeDriver/Chromium
Si vous obtenez l'erreur "This version of ChromeDriver only supports Chrome version X" :

```bash
# Correction des problèmes de version
chmod +x fix_chromium_version.sh
./fix_chromium_version.sh
```

Ce script :
- Détecte automatiquement la version de Chromium
- Télécharge le ChromeDriver compatible
- Nettoie le cache webdriver-manager
- Teste la compatibilité
- Résout les incompatibilités de version

#### Solution 8 : Test de diagnostic Chromium sur WSL
```bash
# Test complet de la configuration Chromium
python test_chromium_wsl.py
```

Ce script de diagnostic :
- Vérifie la détection WSL
- Teste le binaire Chromium
- Vérifie le ChromeDriver
- Teste Selenium avec Chromium
- Identifie les problèmes spécifiques à WSL

#### Solution 9 : Utilisation de Firefox (alternative)
Si Chrome/Chromium pose des problèmes persistants :
```bash
# Installer Firefox
sudo apt install firefox

# Utiliser Firefox avec geckodriver
pip install webdriver-manager
```

Puis modifier le script pour utiliser Firefox au lieu de Chrome/Chromium.

### Fichiers de logs

Les scripts créent automatiquement des fichiers de logs pour faciliter le dépannage :

- **`install.log`** : Logs du script d'activation (`activate_venv.sh`)
- **`install_ubuntu.log`** : Logs du script d'installation Ubuntu (`install_ubuntu.sh`)
- **`fix_ubuntu.log`** : Logs du script de dépannage Ubuntu (`fix_ubuntu.sh`)
- **`clean_install.log`** : Logs du script de nettoyage (`clean_and_install.sh`)
- **`chrome_install.log`** : Logs du script d'installation Chrome (`install_chrome.sh`)
- **`chromium_install.log`** : Logs du script d'installation Chromium (`install_chromium.sh`)

Ces fichiers contiennent :
- Horodatage de chaque action
- Sortie détaillée des commandes
- Messages d'erreur complets
- Statut de chaque étape d'installation

En cas de problème, consultez ces fichiers pour identifier la cause exacte de l'erreur.

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

### Démarrage rapide (Windows avec PowerShell)

1. **Configuration initiale** (une seule fois) :
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Activation de l'environnement** :
   ```powershell
   .\activate_venv.ps1
   ```

3. **Exécution de l'analyse** :
   ```powershell
   python main.py <url> [options]
   ```

4. **Désactivation de l'environnement** (optionnel) :
   ```powershell
   .\deactivate_venv.ps1
   ```

### Démarrage rapide (Ubuntu/Linux)

1. **Installation complète** :
   ```bash
   chmod +x install_ubuntu.sh && ./install_ubuntu.sh
   chmod +x install_chrome.sh && ./install_chrome.sh
   # OU pour Chromium (plus léger)
   chmod +x install_chromium.sh && ./install_chromium.sh
   ```

2. **Activation de l'environnement** :
   ```bash
   source venv/bin/activate
   ```

3. **Exécution de l'analyse** :
   ```bash
   python main.py <url> [options]
   ```

### Exécution
```bash
python main.py <url> [options]

Options:
  --debug              Afficher les logs détaillés
  --encoding ENCODING  Encodage du rapport (utf-8 ou cp1252)
  --cookie-banner TEXT Texte du bouton de la bannière de cookies
  --modules            Liste des modules à activer (contrast, dom, daltonism, tab, screen, image)
  --output-dir         Répertoire de sortie pour les images (défaut: site_images)
  --browser            Navigateur à utiliser (chrome, chromium, ou auto pour détection automatique)
```

### Exemples d'utilisation

```bash
# Analyse simple d'une page
python main.py https://example.com

# Analyse avec gestion de bannière de cookies
python main.py https://example.com --cookie-banner "Accepter tout"

# Analyse en mode debug avec modules spécifiques
python main.py https://example.com --debug --modules contrast dom image

# Analyse avec encodage spécifique
python main.py https://example.com --encoding cp1252

# Analyse avec Chromium explicitement
python main.py https://example.com --browser chromium

# Analyse avec Chrome explicitement
python main.py https://example.com --browser chrome
```

## Architecture

### Dépannage Ubuntu/Linux

Si vous rencontrez des erreurs sur Ubuntu/Linux, voici les solutions :

#### Solution 1 : Script de dépannage automatique
```bash
# Après avoir activé l'environnement virtuel
chmod +x fix_ubuntu.sh
./fix_ubuntu.sh
```

#### Solution 2 : Nettoyage et réinstallation complète (recommandé pour les problèmes persistants)
```bash
# Script de nettoyage et réinstallation complète
chmod +x clean_and_install.sh
./clean_and_install.sh
```

Ce script :
- Supprime complètement l'environnement virtuel existant
- Installe automatiquement tous les prérequis système
- Crée un nouvel environnement virtuel propre
- Installe toutes les dépendances
- Crée des logs détaillés dans `clean_install.log`

#### Solution 3 : Installation de Chrome (si erreur "Chrome not found")
```bash
# Installation automatique de Chrome
chmod +x install_chrome.sh
./install_chrome.sh
```

Alternatives si Chrome ne peut pas être installé :
```bash
# Utiliser Chromium à la place
chmod +x install_chromium.sh
./install_chromium.sh

# Ou utiliser Firefox
sudo apt install firefox
```

#### Solution 4 : Installation manuelle des prérequis
```bash
# Mettre à jour les paquets
sudo apt update

# Installer les prérequis Python
sudo apt install -y python3 python3-pip python3-venv python3-full

# Installer les dépendances de compilation
sudo apt install -y python3-dev build-essential libxml2-dev libxslt1-dev
sudo apt install -y libjpeg-dev libpng-dev libfreetype6-dev liblcms2-dev
```