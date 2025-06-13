#!/bin/bash

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installation des dépendances système...${NC}"
sudo apt-get update
sudo apt-get install -y \
    wkhtmltopdf \
    python3-venv \
    python3-pip \
    chromium-browser \
    chromium-chromedriver

echo -e "${GREEN}Création de l'environnement virtuel...${NC}"
python3 -m venv venv

echo -e "${GREEN}Activation de l'environnement virtuel...${NC}"
source venv/bin/activate

echo -e "${GREEN}Installation des dépendances Python...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}Installation terminée !${NC}"
echo -e "Pour activer l'environnement virtuel, utilisez : ${GREEN}source venv/bin/activate${NC}" 