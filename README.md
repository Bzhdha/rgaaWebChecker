# RGAA Web Checker

## Présentation
RGAA Web Checker est un outil d'analyse d'accessibilité web qui permet de vérifier la conformité des sites web selon les critères RGAA (Référentiel Général d'Amélioration de l'Accessibilité).

## Interface Graphique

### 🖥️ Lancement de l'Interface Graphique

RGAA Web Checker dispose d'une interface graphique moderne et intuitive pour faciliter l'analyse d'accessibilité.

#### Windows (PowerShell)
```powershell
# Lancement automatique avec environnement virtuel
.\launch_gui.ps1

# Lancement sans environnement virtuel
.\launch_gui.ps1 -NoVenv

# Afficher l'aide
.\launch_gui.ps1 -Help
```

#### Ubuntu/Linux
```bash
# Rendre le script exécutable (une seule fois)
chmod +x launch_gui.sh

# Lancement automatique avec environnement virtuel
./launch_gui.sh

# Lancement sans environnement virtuel
./launch_gui.sh --no-venv

# Afficher l'aide
./launch_gui.sh --help
```

#### Lancement direct (Python)
```bash
# Après activation de l'environnement virtuel
python launch_gui.py
```

### 🎯 Fonctionnalités de l'Interface Graphique

#### 1. **Configuration de l'Analyse**
- **Saisie d'URL** : Champ de saisie pour l'URL du site à analyser
- **Sélection des modules** : Cases à cocher pour activer/désactiver les modules :
  - ✅ Analyse des contrastes
  - ✅ Analyse DOM
  - ✅ Simulation daltonisme
  - ✅ Navigation tabulation
  - ✅ Lecteur d'écran
  - ✅ Analyse d'images

#### 2. **Options Avancées**
- **Navigateur** : Choix entre Chrome, Chromium ou détection automatique
- **Encodage** : UTF-8 ou CP1252
- **Bannière cookies** : Texte du bouton à cliquer
- **Répertoire de sortie** : Dossier pour sauvegarder les résultats
- **Mode debug** : Affichage des logs détaillés
- **Charger derniers résultats** : Bypass l'analyse et charge les fichiers existants

#### 3. **Boutons d'Action**
- **Démarrer l'analyse** : Lance l'analyse complète
- **Arrêter** : Interrompt l'analyse en cours
- **Charger derniers résultats** : Charge les résultats sans refaire l'analyse
- **Info fichiers** : Affiche les informations sur les fichiers disponibles
- **Ouvrir dossier résultats** : Ouvre le dossier des résultats

#### 4. **Onglet Résultats**
- **Statistiques** : Vue d'ensemble des problèmes détectés
- **Tableau détaillé** : Liste complète des résultats avec :
  - Module source
  - Type de problème
  - Message descriptif
  - Niveau de sévérité
- **Export** : Sauvegarde en CSV ou JSON

#### 5. **Onglet Analyse DOM (Nouveau avec TKSheet)**
- **Tableau interactif** : Affichage avancé avec TKSheet
- **Tri par colonne** : Clic sur les en-têtes pour trier
- **Filtrage avancé** : Recherche textuelle et filtres par type
- **Édition en ligne** : Possibilité de modifier les données
- **Copie XPath** : Double-clic sur la colonne XPath pour copier
- **Export** : Sauvegarde en CSV ou JSON
- **Navigation fluide** : Ascenseurs horizontaux et verticaux

#### 6. **Onglet Images Capturées**
- **Navigation** : Boutons précédent/suivant
- **Affichage** : Visualisation des captures d'écran
- **Zoom** : Défilement pour voir les détails
- **Informations** : Nom et numéro de l'image

#### 7. **Onglet Logs**
- **Logs en temps réel** : Affichage des messages d'analyse
- **Sauvegarde** : Export des logs en fichier texte
- **Nettoyage** : Effacement des logs

### 🚀 Utilisation de l'Interface

#### Étape 1 : Configuration
1. Saisissez l'URL du site à analyser
2. Sélectionnez les modules d'analyse souhaités
3. Configurez les options avancées si nécessaire

#### Étape 2 : Lancement de l'Analyse
1. Cliquez sur "Démarrer l'analyse"
2. Suivez la progression dans l'onglet Logs
3. L'analyse s'exécute en arrière-plan

#### Étape 3 : Consultation des Résultats
1. **Onglet Résultats** : Consultez les statistiques et la liste détaillée
2. **Onglet Images** : Visualisez les captures d'écran
3. **Export** : Sauvegardez les résultats en CSV ou JSON

### 🔧 Fonctionnalités Avancées

#### Gestion des Erreurs
- **Vérification automatique** des dépendances au lancement
- **Messages d'erreur** explicites en cas de problème
- **Suggestions de résolution** automatiques

#### Performance
- **Analyse asynchrone** : L'interface reste responsive pendant l'analyse
- **Threading** : L'analyse s'exécute en arrière-plan
- **Arrêt sécurisé** : Possibilité d'arrêter l'analyse en cours

#### Personnalisation
- **Taille de fenêtre** : Redimensionnable (minimum 1000x600)
- **Thème moderne** : Interface claire et professionnelle
- **Barre de statut** : Informations sur l'état de l'application

### 📋 Prérequis pour l'Interface Graphique

#### Dépendances Python
```bash
# Installation automatique
pip install -r requirements.txt

# Ou installation manuelle
pip install tkinter pillow selenium webdriver-manager tksheet

# Installation spécifique de TKSheet
pip install tksheet==6.1.12
```

#### Installation de TKSheet (Nouveau)
TKSheet est une bibliothèque avancée pour les tableaux dans Tkinter. Elle offre :
- **Tri interactif** par colonne
- **Édition en ligne** des cellules
- **Filtrage avancé** des données
- **Navigation fluide** avec ascenseurs
- **Performance optimisée** pour de grandes quantités de données

**Installation automatique (Ubuntu/Linux - PRIORITÉ) :**
```bash
# Rendre le script exécutable
chmod +x install_tksheet.sh

# Installation avec vérification complète
./install_tksheet.sh
```

**Installation manuelle (Ubuntu/Linux) :**
```bash
# Après activation de l'environnement virtuel
source venv/bin/activate
pip install tksheet==7.5.12
```

**Installation Windows (SECONDAIRE) :**
```powershell
# Script PowerShell
.\install_tksheet.ps1

# Ou installation manuelle
pip install tksheet==7.5.12
```

**Test de l'installation :**
```bash
# Ubuntu/Linux (PRIORITÉ)
python3 test_tksheet.py
# ou
python3 test_tksheet_simple.py

# Windows (SECONDAIRE)
python test_tksheet.py
```

#### Dépendances Système
- **Windows** : Python avec tkinter (inclus par défaut)
- **Ubuntu/Linux** : `sudo apt install python3-tk`
- **macOS** : Python avec tkinter (inclus par défaut)

### 🛠️ Dépannage de l'Interface Graphique

#### Erreur "tkinter not found"
```bash
# Ubuntu/Linux
sudo apt install python3-tk

# Windows
# Réinstaller Python en cochant "tcl/tk and IDLE"
```

#### Erreur "PIL not found"
```bash
pip install Pillow
```

#### Erreur "selenium not found"
```bash
pip install selenium webdriver-manager
```

#### Interface qui ne se lance pas
1. Vérifiez que vous êtes dans le répertoire racine de l'application
2. Activez l'environnement virtuel : `source venv/bin/activate` ou `.\venv\Scripts\activate`
3. Lancez avec le script : `./launch_gui.sh` ou `.\launch_gui.ps1`

### 💡 Conseils d'Utilisation

1. **Première utilisation** : Lancez tous les modules pour une analyse complète
2. **Analyse ciblée** : Désactivez les modules non nécessaires pour plus de rapidité
3. **Mode debug** : Activez pour voir les détails de l'analyse
4. **Export régulier** : Sauvegardez vos résultats pour comparaison
5. **Images** : Consultez les captures pour comprendre les problèmes visuels

### 🎯 Démonstration de l'Interface

Pour tester l'interface graphique sans effectuer de vraie analyse, utilisez la démonstration :

#### Windows (PowerShell)
```powershell
# Lancement de la démonstration
.\demo_gui.ps1
```

#### Ubuntu/Linux
```bash
# Rendre le script exécutable (une seule fois)
chmod +x demo_gui.sh

# Lancement de la démonstration
./demo_gui.sh
```

#### Lancement direct (Python)
```bash
# Après activation de l'environnement virtuel
python demo_gui.py
```

#### Fonctionnalités de la Démonstration
- **Interface complète** : Toutes les fonctionnalités de l'interface
- **Données fictives** : Résultats d'exemple pour tester l'affichage
- **Export test** : Test des fonctions d'export CSV/JSON
- **Navigation images** : Test de la visualisation d'images
- **Gestion logs** : Test de l'affichage et sauvegarde des logs

**Note** : La démonstration utilise des données fictives. Pour une vraie analyse, utilisez `launch_gui.ps1` ou `launch_gui.sh`.

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