#!/bin/bash

# Script de correction des problèmes de version Chromium/ChromeDriver
# Résout les incompatibilités de version

set -e

echo "=================================================="
echo "Correction des problèmes de version Chromium"
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

# Détecter la version de Chromium
log_info "Détection de la version de Chromium..."

CHROMIUM_VERSION=""
if command -v chromium-browser >/dev/null 2>&1; then
    CHROMIUM_VERSION=$(chromium-browser --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    log_success "Version Chromium détectée: $CHROMIUM_VERSION"
else
    log_error "Chromium non trouvé"
    exit 1
fi

if [ -z "$CHROMIUM_VERSION" ]; then
    log_error "Impossible de détecter la version de Chromium"
    exit 1
fi

# Extraire la version majeure
MAJOR_VERSION=$(echo $CHROMIUM_VERSION | cut -d. -f1)
log_info "Version majeure: $MAJOR_VERSION"

# Nettoyer le cache webdriver-manager
log_info "Nettoyage du cache webdriver-manager..."
if [ -d "$HOME/.wdm" ]; then
    rm -rf "$HOME/.wdm"
    log_success "Cache supprimé"
else
    log_info "Aucun cache à supprimer"
fi

# Télécharger la version compatible
log_info "Téléchargement du ChromeDriver compatible..."
python3 -c "
import os
import glob
from webdriver_manager.chrome import ChromeDriverManager

try:
    # Utiliser la version automatique (webdriver-manager gère la compatibilité)
    driver_dir = os.path.dirname(ChromeDriverManager().install())
    print('ChromeDriver téléchargé automatiquement')

# Chercher le binaire
chromedriver_path = None
for f in glob.glob(os.path.join(driver_dir, 'chromedriver*')):
    if not f.endswith('.txt') and not f.endswith('.chromedriver') and 'THIRD_PARTY' not in f:
        chromedriver_path = f
        break

if not chromedriver_path:
    print('Aucun binaire chromedriver trouvé')
    exit(1)

print(f'ChromeDriver trouvé: {chromedriver_path}')

# Corriger les permissions
if not os.access(chromedriver_path, os.X_OK):
    print('Correction des permissions...')
    os.chmod(chromedriver_path, 0o755)
    print('Permissions corrigées')
else:
    print('ChromeDriver déjà exécutable')

print('ChromeDriver prêt')
"

if [ $? -eq 0 ]; then
    log_success "ChromeDriver compatible téléchargé"
else
    log_error "Échec du téléchargement"
    exit 1
fi

# Test de fonctionnement
log_info "Test de fonctionnement avec Chromium..."
python3 -c "
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import glob

try:
    # Trouver le ChromeDriver
    driver_dir = os.path.dirname(ChromeDriverManager().install())
    chromedriver_path = None
    for f in glob.glob(os.path.join(driver_dir, 'chromedriver*')):
        if not f.endswith('.txt') and not f.endswith('.chromedriver') and 'THIRD_PARTY' not in f:
            chromedriver_path = f
            break
    
    if not chromedriver_path:
        raise Exception('ChromeDriver non trouvé')
    
    # Configuration pour Chromium
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.binary_location = '/usr/bin/chromium-browser'
    
    # Test de lancement
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Test de navigation
    driver.get('https://www.google.com')
    title = driver.title
    print(f'Test réussi: {title}')
    
    driver.quit()
    print('Chromium et ChromeDriver fonctionnent correctement ensemble')
    
except Exception as e:
    print(f'Erreur de test: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    log_success "Test de fonctionnement réussi"
else
    log_error "Test de fonctionnement échoué"
    exit 1
fi

echo ""
log_success "Correction des versions terminée avec succès !"
echo ""
log_info "Vous pouvez maintenant relancer votre script :"
echo "python main.py https://www.niji.fr --browser chromium"
echo "" 