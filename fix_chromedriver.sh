#!/bin/bash

# Script de correction des problèmes ChromeDriver
# Résout les problèmes de permissions et de fichiers corrompus

set -e

echo "=================================================="
echo "Correction des problèmes ChromeDriver"
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

if [ -d "$HOME/.wdm" ]; then
    log_info "Suppression du répertoire ~/.wdm..."
    rm -rf "$HOME/.wdm"
    log_success "Cache webdriver-manager supprimé"
else
    log_info "Aucun cache webdriver-manager trouvé"
fi

# Réinstaller webdriver-manager
log_info "Réinstallation de webdriver-manager..."
pip uninstall -y webdriver-manager 2>/dev/null || true
pip install webdriver-manager
log_success "webdriver-manager réinstallé"

# Test de téléchargement et correction des permissions
log_info "Test de téléchargement du ChromeDriver..."
python3 -c "
import os
import glob
from webdriver_manager.chrome import ChromeDriverManager

try:
    # Télécharger le ChromeDriver
    driver_dir = os.path.dirname(ChromeDriverManager().install())
    print(f'Répertoire ChromeDriver: {driver_dir}')
    
    # Chercher le vrai binaire
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
    
    # Vérifier que c'est bien un binaire
    import subprocess
    result = subprocess.run(['file', chromedriver_path], capture_output=True, text=True)
    print(f'Type de fichier: {result.stdout.strip()}')
    
    print('ChromeDriver prêt à utiliser')
    
except Exception as e:
    print(f'Erreur: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    log_success "ChromeDriver corrigé avec succès"
else
    log_error "Échec de la correction du ChromeDriver"
    exit 1
fi

# Test de fonctionnement
log_info "Test de fonctionnement..."
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
    
    # Configuration
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    
    # Test de lancement
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Test de navigation
    driver.get('https://www.google.com')
    title = driver.title
    print(f'Test réussi: {title}')
    
    driver.quit()
    print('ChromeDriver fonctionne correctement')
    
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
log_success "Correction terminée avec succès !"
echo ""
log_info "Vous pouvez maintenant relancer votre script :"
echo "python main.py https://www.niji.fr --browser chromium"
echo "" 