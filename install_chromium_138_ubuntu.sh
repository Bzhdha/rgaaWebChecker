#!/bin/bash

echo "🔄 Installation de Chromium version 138 (Ubuntu)"
echo "================================================"

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

# Ajouter le dépôt Ubuntu backports pour les versions plus récentes
echo "📦 Ajout du dépôt backports..."
echo "deb http://archive.ubuntu.com/ubuntu $(lsb_release -cs)-backports main restricted universe multiverse" | sudo tee /etc/apt/sources.list.d/backports.list

# Mettre à jour les paquets
echo "🔄 Mise à jour des paquets..."
sudo apt update

# Installer Chromium depuis les backports
echo "📥 Installation de Chromium depuis les backports..."
sudo apt install -y chromium-browser/$(lsb_release -cs)-backports

# Alternative: installer depuis le dépôt principal
if ! command -v chromium-browser &> /dev/null; then
    echo "📥 Installation depuis le dépôt principal..."
    sudo apt install -y chromium-browser
fi

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