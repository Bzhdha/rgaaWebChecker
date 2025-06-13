#!/bin/bash

# Vérifier si l'environnement virtuel est activé
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Aucun environnement virtuel n'est actuellement activé."
    exit 1
fi

# Désactiver l'environnement virtuel
deactivate

echo "Environnement virtuel désactivé !" 
