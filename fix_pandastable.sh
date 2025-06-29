#!/bin/bash

# Script pour corriger le problème pandastable atdivider
# Compatible Ubuntu/Linux (priorité) et Windows/WSL

echo "🔧 Correction du problème pandastable atdivider..."

# Vérifier si l'environnement virtuel est activé
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Environnement virtuel non activé"
    echo "Veuillez activer l'environnement virtuel :"
    echo "source venv/bin/activate"
    exit 1
fi

echo "✅ Environnement virtuel activé: $VIRTUAL_ENV"

# Désinstaller la version actuelle
echo "🗑️  Désinstallation de pandastable actuel..."
pip uninstall -y pandastable

# Installer une version plus récente
echo "📦 Installation de pandastable>=0.12.3..."
pip install "pandastable>=0.12.3"

# Vérifier l'installation
echo "🔍 Vérification de l'installation..."
pip show pandastable

echo "✅ Mise à jour terminée !"
echo ""
echo "📝 Notes :"
echo "- Le problème 'atdivider' devrait être résolu"
echo "- Si le problème persiste, le code a été modifié pour le contourner"
echo "- Redémarrez l'application pour appliquer les changements" 