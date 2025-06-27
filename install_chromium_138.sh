#!/bin/bash

echo "🔄 Installation de Chromium version 138"
echo "========================================"

# Vérifier si on est sur WSL
if [[ -f /proc/version && $(cat /proc/version) == *"microsoft"* ]]; then
    echo "✅ WSL détecté"
else
    echo "⚠️  Ce script est optimisé pour WSL"
fi

# Désinstaller la version snap actuelle
echo "🗑️  Désinstallation de la version snap actuelle..."
if command -v snap &> /dev/null; then
    sudo snap remove chromium
    echo "✅ Version snap supprimée"
else
    echo "ℹ️  Snap non installé, passage à l'installation directe"
fi

# Ajouter le dépôt Google Chrome (qui contient Chromium)
echo "📦 Ajout du dépôt Google Chrome..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

# Mettre à jour les paquets
echo "🔄 Mise à jour des paquets..."
sudo apt update

# Installer Chromium version 138
echo "📥 Installation de Chromium version 138..."
sudo apt install -y chromium-browser=138.0.7151.119-1

# Vérifier l'installation
echo "🔍 Vérification de l'installation..."
if command -v chromium-browser &> /dev/null; then
    VERSION=$(chromium-browser --version)
    echo "✅ Chromium installé: $VERSION"
else
    echo "❌ Échec de l'installation"
    exit 1
fi

# Créer un lien symbolique si nécessaire
if [ ! -f /usr/bin/chromium ]; then
    echo "🔗 Création du lien symbolique..."
    sudo ln -sf /usr/bin/chromium-browser /usr/bin/chromium
fi

echo "✅ Installation terminée !"
echo "🚀 Vous pouvez maintenant utiliser: chromium-browser --version" 