#!/bin/bash

# Script de nettoyage du cache webdriver-manager
# Résout les problèmes de ChromeDriver corrompus ou non exécutables

set -e

echo "=================================================="
echo "Nettoyage du cache webdriver-manager"
echo "=================================================="

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier si on est dans un environnement virtuel
if [[ "$VIRTUAL_ENV" != "" ]]; then
    log_info "Environnement virtuel détecté: $VIRTUAL_ENV"
else
    log_warning "Aucun environnement virtuel détecté"
    log_info "Activation de l'environnement virtuel..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        log_success "Environnement virtuel activé"
    else
        log_error "Fichier d'activation de l'environnement virtuel non trouvé"
        exit 1
    fi
fi

# Nettoyer le cache webdriver-manager
log_info "Nettoyage du cache webdriver-manager..."

# Vérifier si le répertoire existe
if [ -d "$HOME/.wdm" ]; then
    log_info "Suppression du répertoire ~/.wdm..."
    rm -rf "$HOME/.wdm"
    log_success "Cache webdriver-manager supprimé"
else
    log_info "Aucun cache webdriver-manager trouvé"
fi

# Nettoyer aussi le cache pip si nécessaire
log_info "Nettoyage du cache pip..."
pip cache purge 2>/dev/null || log_warning "Cache pip non disponible ou déjà vide"

# Réinstaller webdriver-manager si nécessaire
log_info "Vérification de webdriver-manager..."
if ! pip show webdriver-manager >/dev/null 2>&1; then
    log_info "Installation de webdriver-manager..."
    pip install webdriver-manager
    log_success "webdriver-manager installé"
else
    log_info "webdriver-manager déjà installé"
fi

# Vérifier les navigateurs disponibles
log_info "Vérification des navigateurs disponibles..."

# Vérifier Chrome
if command -v google-chrome >/dev/null 2>&1; then
    CHROME_VERSION=$(google-chrome --version)
    log_success "Chrome trouvé: $CHROME_VERSION"
else
    log_warning "Chrome non trouvé"
fi

# Vérifier Chromium
if command -v chromium-browser >/dev/null 2>&1; then
    CHROMIUM_VERSION=$(chromium-browser --version)
    log_success "Chromium trouvé: $CHROMIUM_VERSION"
else
    log_warning "Chromium non trouvé"
fi

# Test de téléchargement du ChromeDriver
log_info "Test de téléchargement du ChromeDriver..."
python3 -c "
import sys
from webdriver_manager.chrome import ChromeDriverManager
try:
    driver_path = ChromeDriverManager().install()
    print(f'ChromeDriver téléchargé avec succès: {driver_path}')
    import os
    if os.access(driver_path, os.X_OK):
        print('ChromeDriver est exécutable')
    else:
        print('ChromeDriver n\'est pas exécutable, correction des permissions...')
        os.chmod(driver_path, 0o755)
        print('Permissions corrigées')
except Exception as e:
    print(f'Erreur lors du téléchargement: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    log_success "Test de ChromeDriver réussi"
else
    log_error "Test de ChromeDriver échoué"
    exit 1
fi

echo ""
log_success "Nettoyage terminé avec succès !"
echo ""
log_info "Vous pouvez maintenant relancer votre script :"
echo "python main.py https://www.niji.fr --browser chromium"
echo "" 