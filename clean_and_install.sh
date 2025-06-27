#!/bin/bash

# Script de nettoyage et réinstallation complète

# Configuration du logging
LOG_FILE="clean_install.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Fonction de logging
log_message() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

# Fonction pour gérer les erreurs
handle_error() {
    log_message "ERREUR: $1"
    log_message "Le script s'est arrêté à cause d'une erreur."
    log_message "Consultez le fichier $LOG_FILE pour plus de détails."
    echo ""
    echo "Appuyez sur une touche pour fermer cette fenêtre..."
    read -n 1 -s
    exit 1
}

# Rediriger les erreurs vers le log
exec 2>> "$LOG_FILE"

# Démarrer le logging
log_message "=== Début du nettoyage et réinstallation ==="

echo "🧹 Nettoyage et réinstallation complète de l'environnement virtuel"
echo ""

# Étape 1 : Nettoyage
log_message "Étape 1 : Nettoyage de l'environnement existant..."
echo "Suppression de l'environnement virtuel existant..."

if [ -d "venv" ]; then
    if rm -rf venv 2>&1 | tee -a "$LOG_FILE"; then
        log_message "Environnement virtuel supprimé avec succès"
    else
        log_message "ATTENTION: Impossible de supprimer complètement l'environnement virtuel"
    fi
else
    log_message "Aucun environnement virtuel existant à supprimer"
fi

# Supprimer les fichiers de marquage
if [ -f "venv/.dependencies_installed" ]; then
    rm -f venv/.dependencies_installed
    log_message "Fichier de marquage supprimé"
fi

# Étape 2 : Installation des prérequis système
log_message "Étape 2 : Installation des prérequis système..."
echo "Installation des prérequis système..."

if command -v apt &> /dev/null; then
    # Mettre à jour les paquets
    log_message "Mise à jour des paquets système..."
    if ! sudo apt update 2>&1 | tee -a "$LOG_FILE"; then
        handle_error "Échec de la mise à jour des paquets"
    fi
    
    # Installer les prérequis Python
    log_message "Installation des prérequis Python..."
    if ! sudo apt install -y python3 python3-pip python3-full 2>&1 | tee -a "$LOG_FILE"; then
        handle_error "Échec de l'installation des prérequis Python"
    fi
    
    # Détecter la version de Python et installer le bon package venv
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    log_message "Version Python détectée: $PYTHON_VERSION"
    
    # Essayer d'abord la version spécifique, puis la version générique
    log_message "Installation de python3-venv..."
    if ! sudo apt install -y "python3-${PYTHON_VERSION}-venv" 2>&1 | tee -a "$LOG_FILE"; then
        log_message "Échec avec la version spécifique, tentative avec python3-venv..."
        if ! sudo apt install -y python3-venv 2>&1 | tee -a "$LOG_FILE"; then
            handle_error "Impossible d'installer python3-venv"
        fi
    fi
    
    # Installer les dépendances de compilation
    log_message "Installation des dépendances de compilation..."
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
        handle_error "Échec de l'installation des dépendances de compilation"
    fi
else
    handle_error "apt n'est pas disponible. Ce script est destiné aux systèmes Ubuntu/Debian"
fi

# Étape 3 : Création de l'environnement virtuel
log_message "Étape 3 : Création de l'environnement virtuel..."
echo "Création de l'environnement virtuel..."

# Vérifier que python3-venv est disponible
if ! python3 -c "import venv" 2>/dev/null; then
    handle_error "python3-venv n'est toujours pas disponible après installation"
fi

# Créer l'environnement virtuel
CREATE_OUTPUT=$(python3 -m venv venv 2>&1)
CREATE_EXIT_CODE=$?

log_message "Sortie de la création: $CREATE_OUTPUT"

if [ $CREATE_EXIT_CODE -ne 0 ]; then
    handle_error "La création de l'environnement virtuel a échoué. Sortie: $CREATE_OUTPUT"
fi

# Vérifier que l'environnement a été créé correctement
if [ ! -d "venv/bin" ] || [ ! -f "venv/bin/activate" ]; then
    handle_error "L'environnement virtuel n'a pas été créé correctement"
fi

log_message "Environnement virtuel créé avec succès"

# Étape 4 : Activation et installation des dépendances
log_message "Étape 4 : Activation et installation des dépendances..."
echo "Activation de l'environnement virtuel et installation des dépendances..."

# Activer l'environnement virtuel
source venv/bin/activate
if [ -z "$VIRTUAL_ENV" ]; then
    handle_error "L'activation de l'environnement virtuel a échoué"
fi

log_message "Environnement virtuel activé: $VIRTUAL_ENV"

# Mettre à jour pip
log_message "Mise à jour de pip..."
if ! pip install --upgrade pip 2>&1 | tee -a "$LOG_FILE"; then
    log_message "ATTENTION: Échec de la mise à jour de pip, continuation..."
fi

# Installer les outils de build
log_message "Installation des outils de build..."
if ! pip install wheel setuptools --upgrade 2>&1 | tee -a "$LOG_FILE"; then
    log_message "ATTENTION: Échec de l'installation des outils de build, continuation..."
fi

# Installer les dépendances
log_message "Installation des dépendances Python..."
if pip install -r requirements.txt 2>&1 | tee -a "$LOG_FILE"; then
    log_message "Dépendances installées avec succès"
else
    log_message "Échec de l'installation en lot, tentative package par package..."
    
    # Installation package par package
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
    
    if [ "$success" = false ]; then
        handle_error "Certaines dépendances n'ont pas pu être installées"
    fi
fi

# Créer le fichier de marquage
touch venv/.dependencies_installed

# Vérification finale
log_message "Vérification finale de l'installation..."
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
    log_message "=== Installation terminée avec succès ==="
    echo ""
    echo "✅ Installation terminée avec succès !"
    echo "📋 Logs disponibles dans : $LOG_FILE"
    echo "🔧 Environnement virtuel activé et prêt à l'emploi"
    echo "🚪 Pour le désactiver : deactivate"
    echo ""
    echo "Appuyez sur une touche pour continuer..."
    read -n 1 -s
else
    handle_error "Certaines dépendances n'ont pas pu être installées. Consultez $LOG_FILE pour plus de détails."
fi 