#!/bin/bash
# Script bash pour lancer l'interface graphique RGAA Web Checker
# Usage: ./launch_gui.sh

set -e  # Arrêter en cas d'erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Fonction d'aide
show_help() {
    echo -e "${CYAN}RGAA Web Checker - Interface Graphique${NC}"
    echo -e "${CYAN}=====================================${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo "  ./launch_gui.sh              # Lance avec environnement virtuel automatique"
    echo "  ./launch_gui.sh --no-venv    # Lance sans environnement virtuel"
    echo "  ./launch_gui.sh --help       # Affiche cette aide"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "  --no-venv    Désactive l'activation automatique de l'environnement virtuel"
    echo "  --help       Affiche cette aide"
    echo ""
}

# Vérifier les arguments
if [[ "$1" == "--help" ]]; then
    show_help
    exit 0
fi

NO_VENV=false
if [[ "$1" == "--no-venv" ]]; then
    NO_VENV=true
fi

echo -e "${GREEN}RGAA Web Checker - Interface Graphique${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""

# Vérifier si Python est installé
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo -e "${GREEN}✅ Python détecté: $PYTHON_VERSION${NC}"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1)
    echo -e "${GREEN}✅ Python détecté: $PYTHON_VERSION${NC}"
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Python n'est pas installé ou n'est pas dans le PATH${NC}"
    echo -e "${YELLOW}Veuillez installer Python: sudo apt install python3${NC}"
    exit 1
fi

# Vérifier si tkinter est disponible
if $PYTHON_CMD -c "import tkinter; print('tkinter disponible')" 2>/dev/null; then
    echo -e "${GREEN}✅ Tkinter disponible${NC}"
else
    echo -e "${RED}❌ Tkinter n'est pas disponible${NC}"
    echo -e "${YELLOW}Installer tkinter: sudo apt install python3-tk${NC}"
    exit 1
fi

# Gestion de l'environnement virtuel
if [[ "$NO_VENV" == false ]]; then
    echo -e "${YELLOW}🔍 Vérification de l'environnement virtuel...${NC}"
    
    if [[ -f "venv/bin/activate" ]]; then
        echo -e "${GREEN}✅ Environnement virtuel trouvé${NC}"
        echo -e "${YELLOW}🔄 Activation de l'environnement virtuel...${NC}"
        
        if source venv/bin/activate; then
            echo -e "${GREEN}✅ Environnement virtuel activé${NC}"
        else
            echo -e "${YELLOW}⚠️  Erreur lors de l'activation de l'environnement virtuel${NC}"
            echo -e "${YELLOW}Tentative de lancement sans environnement virtuel...${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Aucun environnement virtuel trouvé${NC}"
        echo -e "${YELLOW}Tentative de lancement sans environnement virtuel...${NC}"
    fi
fi

# Vérifier les dépendances
echo -e "${YELLOW}🔍 Vérification des dépendances...${NC}"

MISSING_DEPS=()

if $PYTHON_CMD -c "import PIL" 2>/dev/null; then
    echo -e "${GREEN}✅ Pillow (PIL) disponible${NC}"
else
    MISSING_DEPS+=("Pillow (PIL)")
    echo -e "${RED}❌ Pillow (PIL) manquant${NC}"
fi

if $PYTHON_CMD -c "import selenium" 2>/dev/null; then
    echo -e "${GREEN}✅ Selenium disponible${NC}"
else
    MISSING_DEPS+=("selenium")
    echo -e "${RED}❌ Selenium manquant${NC}"
fi

if $PYTHON_CMD -c "import webdriver_manager" 2>/dev/null; then
    echo -e "${GREEN}✅ webdriver-manager disponible${NC}"
else
    MISSING_DEPS+=("webdriver-manager")
    echo -e "${RED}❌ webdriver-manager manquant${NC}"
fi

if [[ ${#MISSING_DEPS[@]} -gt 0 ]]; then
    echo ""
    echo -e "${RED}❌ Dépendances manquantes:${NC}"
    for dep in "${MISSING_DEPS[@]}"; do
        echo -e "   - ${RED}$dep${NC}"
    done
    echo ""
    echo -e "${YELLOW}Pour installer les dépendances manquantes:${NC}"
    echo -e "${CYAN}pip install -r requirements.txt${NC}"
    echo ""
    echo -e "${YELLOW}Ou utilisez le script d'installation automatique:${NC}"
    echo -e "${CYAN}./install_ubuntu.sh${NC}"
    exit 1
fi

# Vérifier que les modules de l'application existent
echo -e "${YELLOW}🔍 Vérification des modules de l'application...${NC}"

REQUIRED_MODULES=(
    "core.config"
    "core.crawler"
    "utils.log_utils"
    "modules.contrast_checker"
    "modules.dom_analyzer"
    "modules.color_simulator"
    "modules.tab_navigator"
    "modules.screen_reader"
    "modules.image_analyzer"
)

MISSING_MODULES=()
for module in "${REQUIRED_MODULES[@]}"; do
    if $PYTHON_CMD -c "import $module" 2>/dev/null; then
        echo -e "${GREEN}✅ $module disponible${NC}"
    else
        MISSING_MODULES+=("$module")
        echo -e "${RED}❌ $module manquant${NC}"
    fi
done

if [[ ${#MISSING_MODULES[@]} -gt 0 ]]; then
    echo ""
    echo -e "${RED}❌ Modules de l'application manquants:${NC}"
    for module in "${MISSING_MODULES[@]}"; do
        echo -e "   - ${RED}$module${NC}"
    done
    echo ""
    echo -e "${YELLOW}Assurez-vous d'être dans le répertoire racine de l'application.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Toutes les vérifications sont passées${NC}"
echo -e "${CYAN}🚀 Lancement de l'interface graphique...${NC}"
echo ""

# Lancer l'interface graphique
if $PYTHON_CMD launch_gui.py; then
    EXIT_CODE=0
else
    echo -e "${RED}❌ Erreur lors du lancement${NC}"
    EXIT_CODE=1
fi

# Désactiver l'environnement virtuel si nécessaire
if [[ "$NO_VENV" == false && -f "venv/bin/activate" ]]; then
    echo ""
    echo -e "${YELLOW}🔄 Désactivation de l'environnement virtuel...${NC}"
    deactivate 2>/dev/null || true
fi

exit $EXIT_CODE 