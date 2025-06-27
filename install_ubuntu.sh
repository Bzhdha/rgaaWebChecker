#!/bin/bash

# Configuration du logging
LOG_FILE="install_ubuntu.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Fonction de logging
log_message() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

# Fonction pour gérer les erreurs
handle_error() {
    log_message "ERREUR: $1"
    log_message "Le script d'installation s'est arrêté à cause d'une erreur."
    log_message "Consultez le fichier $LOG_FILE pour plus de détails."
    echo ""
    echo "Appuyez sur une touche pour fermer cette fenêtre..."
    read -n 1 -s
    exit 1
}

# Rediriger les erreurs vers le log
exec 2>> "$LOG_FILE"

# Démarrer le logging
log_message "=== Début de l'installation RGAA Web Checker pour Ubuntu/Debian ==="

# Vérifier si on est sur Ubuntu/Debian
if ! command -v apt &> /dev/null; then
    handle_error "Ce script est destiné aux systèmes Ubuntu/Debian"
fi

# Mettre à jour les paquets
log_message "Mise à jour des paquets système..."
if ! sudo apt update 2>&1 | tee -a "$LOG_FILE"; then
    handle_error "Échec de la mise à jour des paquets système"
fi

# Installer les prérequis Python
log_message "Installation des prérequis Python..."
if ! sudo apt install -y python3 python3-pip python3-venv python3-full 2>&1 | tee -a "$LOG_FILE"; then
    handle_error "Échec de l'installation des prérequis Python"
fi

# Installer les dépendances système pour les packages Python
log_message "Installation des dépendances système..."
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

# Vérifier si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    log_message "Création de l'environnement virtuel..."
    if ! python3 -m venv venv 2>&1 | tee -a "$LOG_FILE"; then
        handle_error "Échec de la création de l'environnement virtuel"
    fi
    log_message "Environnement virtuel créé avec succès"
else
    log_message "Environnement virtuel existant détecté"
fi

# Activer l'environnement virtuel
log_message "Activation de l'environnement virtuel..."
if ! source venv/bin/activate 2>&1 | tee -a "$LOG_FILE"; then
    handle_error "Échec de l'activation de l'environnement virtuel"
fi

# Mettre à jour pip dans l'environnement virtuel
log_message "Mise à jour de pip..."
if ! pip install --upgrade pip 2>&1 | tee -a "$LOG_FILE"; then
    log_message "ATTENTION: Échec de la mise à jour de pip, continuation..."
fi

# Installer les dépendances Python
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
        handle_error "Certaines dépendances n'ont pas pu être installées. Consultez $LOG_FILE pour plus de détails."
    fi
fi

# Créer le fichier de marquage
touch venv/.dependencies_installed

log_message "=== Installation terminée avec succès ==="
echo ""
echo "✅ Installation terminée avec succès !"
echo "📋 Logs disponibles dans : $LOG_FILE"
echo "🔧 Pour activer l'environnement virtuel : source venv/bin/activate"
echo "🚪 Pour le désactiver : deactivate"
echo ""
echo "Appuyez sur une touche pour continuer..."
read -n 1 -s 