#!/bin/bash

# Script d'installation de TKSheet pour Ubuntu/Linux
# Priorité : Ubuntu/Linux (selon les règles de contexte)

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Installation de TKSheet pour Ubuntu/Linux ===${NC}"

# Vérifier si l'environnement virtuel est activé
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${RED}Erreur : L'environnement virtuel n'est pas activé.${NC}"
    echo -e "${YELLOW}Veuillez d'abord exécuter : source venv/bin/activate${NC}"
    exit 1
fi

echo -e "${GREEN}Environnement virtuel détecté : $VIRTUAL_ENV${NC}"

# Vérifier si Python est disponible
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Erreur : Python3 n'est pas installé.${NC}"
    echo -e "${YELLOW}Installez Python3 avec : sudo apt install python3 python3-pip${NC}"
    exit 1
fi

# Installation de TKSheet
echo -e "${BLUE}Installation de TKSheet...${NC}"
pip install tksheet==7.5.12

# Vérification de l'installation
echo -e "${BLUE}Vérification de l'installation...${NC}"
if pip show tksheet &> /dev/null; then
    VERSION=$(pip show tksheet | grep "Version" | cut -d' ' -f2)
    echo -e "${GREEN}✓ TKSheet installé avec succès${NC}"
    echo -e "${GREEN}Version : $VERSION${NC}"
else
    echo -e "${RED}✗ Erreur lors de l'installation de TKSheet${NC}"
    exit 1
fi

# Test de l'installation
echo -e "${BLUE}Test de l'installation...${NC}"
if python3 -c "import tksheet; print('TKSheet importé avec succès')" 2>/dev/null; then
    echo -e "${GREEN}✓ TKSheet fonctionne correctement${NC}"
else
    echo -e "${RED}✗ Erreur lors du test de TKSheet${NC}"
    exit 1
fi

# Test du script de démonstration
echo -e "${BLUE}Test du script de démonstration...${NC}"
if [[ -f "test_tksheet.py" ]]; then
    echo -e "${GREEN}✓ Script de test trouvé${NC}"
    echo -e "${YELLOW}Pour tester TKSheet, exécutez : python3 test_tksheet.py${NC}"
else
    echo -e "${YELLOW}Script de test non trouvé, création d'un test simple...${NC}"
    cat > test_tksheet_simple.py << 'EOF'
#!/usr/bin/env python3
"""
Test simple de TKSheet
"""
import tkinter as tk
from tksheet import Sheet

def test_tksheet():
    root = tk.Tk()
    root.title("Test TKSheet - Ubuntu/Linux")
    root.geometry("600x400")
    
    sheet = Sheet(root, 
                  headers=["Colonne 1", "Colonne 2", "Colonne 3"],
                  theme="light blue")
    
    test_data = [
        ["Test 1", "Donnée 1", "Valeur 1"],
        ["Test 2", "Donnée 2", "Valeur 2"],
    ]
    
    for i, row in enumerate(test_data):
        sheet.insert_row(i + 1, row)
    
    sheet.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    print("✅ TKSheet fonctionne sur Ubuntu/Linux !")
    root.mainloop()

if __name__ == "__main__":
    test_tksheet()
EOF
    echo -e "${GREEN}✓ Script de test créé : test_tksheet_simple.py${NC}"
fi

echo -e "${GREEN}✅ Installation de TKSheet terminée avec succès !${NC}"
echo -e "${BLUE}Vous pouvez maintenant tester avec :${NC}"
echo -e "${YELLOW}  python3 test_tksheet.py${NC}"
echo -e "${YELLOW}  ou${NC}"
echo -e "${YELLOW}  python3 test_tksheet_simple.py${NC}"
echo -e "${BLUE}Et lancer l'interface graphique avec :${NC}"
echo -e "${YELLOW}  python3 gui_app.py${NC}" 