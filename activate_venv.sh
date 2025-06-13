#!/bin/bash

# Vérifier si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo "L'environnement virtuel n'existe pas. Création en cours..."
    python3 -m venv venv
fi

# Activer l'environnement virtuel
source venv/bin/activate

# Vérifier si les dépendances sont installées
if [ ! -f "venv/.dependencies_installed" ]; then
    echo "Installation des dépendances..."
    pip install -r requirements.txt
    touch venv/.dependencies_installed
fi

echo "Environnement virtuel activé !"
echo "Pour le désactiver, utilisez : ./deactivate_venv.sh" 