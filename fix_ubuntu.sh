#!/bin/bash

# Configuration du logging
LOG_FILE="fix_ubuntu.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Fonction de logging
log_message() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

# Fonction pour gérer les erreurs
handle_error() {
    log_message "ERREUR: $1"
    log_message "Le script de dépannage s'est arrêté à cause d'une erreur."
    log_message "Consultez le fichier $LOG_FILE pour plus de détails."
    echo ""
    echo "Appuyez sur une touche pour fermer cette fenêtre..."
    read -n 1 -s
    exit 1
}

# Rediriger les erreurs vers le log
exec 2>> "$LOG_FILE"

# Démarrer le logging
log_message "=== Script de dépannage Ubuntu/Debian ==="

# Vérifier si on est sur Ubuntu/Debian
if ! command -v apt &> /dev/null; then
    handle_error "Ce script est destiné aux systèmes Ubuntu/Debian"
fi

# Vérifier si l'environnement virtuel est activé
if [ -z "$VIRTUAL_ENV" ]; then
    handle_error "L'environnement virtuel n'est pas activé. Veuillez d'abord exécuter : source venv/bin/activate"
fi

log_message "Environnement virtuel détecté : $VIRTUAL_ENV"

# Étape 1 : Vérifier et installer les prérequis système
log_message "Étape 1 : Vérification des prérequis système..."
if ! python3 -c "import venv" 2>/dev/null; then
    log_message "Installation de python3-venv..."
    if ! sudo apt update 2>&1 | tee -a "$LOG_FILE"; then
        handle_error "Échec de la mise à jour des paquets"
    fi
    if ! sudo apt install -y python3-venv python3-full 2>&1 | tee -a "$LOG_FILE"; then
        handle_error "Échec de l'installation de python3-venv"
    fi
fi

# Étape 2 : Installer les dépendances système pour Pillow et lxml
log_message "Étape 2 : Installation des dépendances système..."
if ! sudo apt install -y \
    python3-dev \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libtiff5-dev \
    libopenjp2-7-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev 2>&1 | tee -a "$LOG_FILE"; then
    handle_error "Échec de l'installation des dépendances système"
fi

# Étape 3 : Mettre à jour pip
log_message "Étape 3 : Mise à jour de pip..."
if ! pip install --upgrade pip 2>&1 | tee -a "$LOG_FILE"; then
    log_message "ATTENTION: Échec de la mise à jour de pip, continuation..."
fi

# Étape 4 : Installer les outils de build
log_message "Étape 4 : Installation des outils de build..."
if ! pip install wheel setuptools --upgrade 2>&1 | tee -a "$LOG_FILE"; then
    log_message "ATTENTION: Échec de l'installation des outils de build, continuation..."
fi

# Étape 5 : Installation des packages un par un
log_message "Étape 5 : Installation des packages..."

packages=(
    "selenium==4.18.1"
    "webdriver-manager==4.0.1"
    "Pillow==9.5.0"
    "markdown==3.5.2"
    "beautifulsoup4==4.12.3"
    "requests==2.31.0"
    "lxml==4.9.3"
    "pdfkit==1.0.0"
)

success=true
for package in "${packages[@]}"; do
    log_message "Installation de $package..."
    if pip install "$package" 2>&1 | tee -a "$LOG_FILE"; then
        log_message "✓ $package installé avec succès"
    else
        log_message "✗ Échec de l'installation de $package"
        success=false
    fi
done

# Vérification finale
log_message "Vérification de l'installation..."
packages_check=("selenium" "webdriver-manager" "Pillow" "markdown" "beautifulsoup4" "requests" "lxml" "pdfkit")

all_installed=true
for package in "${packages_check[@]}"; do
    if pip show "$package" >/dev/null 2>&1; then
        log_message "✓ $package installé"
    else
        log_message "✗ $package non installé"
        all_installed=false
    fi
done

if [ "$all_installed" = true ]; then
    log_message "=== Toutes les dépendances sont installées avec succès ! ==="
    touch venv/.dependencies_installed
    echo ""
    echo "✅ Toutes les dépendances sont installées avec succès !"
    echo "📋 Logs disponibles dans : $LOG_FILE"
    echo ""
    echo "Appuyez sur une touche pour continuer..."
    read -n 1 -s
else
    log_message "=== Certaines dépendances n'ont pas pu être installées ==="
    echo ""
    echo "❌ Certaines dépendances n'ont pas pu être installées."
    echo "📋 Logs disponibles dans : $LOG_FILE"
    echo ""
    echo "Solutions alternatives :"
    echo "1. Réinstallez les dépendances système : sudo apt install python3-dev build-essential"
    echo "2. Utilisez des versions plus anciennes des packages"
    echo "3. Installez les packages via apt : sudo apt install python3-pillow python3-lxml"
    echo ""
    echo "Appuyez sur une touche pour continuer..."
    read -n 1 -s
fi 