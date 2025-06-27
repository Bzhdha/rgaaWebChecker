#!/bin/bash

echo "🔄 Installation directe de Chromium version 138"
echo "==============================================="

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
fi

# Créer le répertoire d'installation
INSTALL_DIR="/opt/chromium-138"
echo "📁 Création du répertoire d'installation: $INSTALL_DIR"
sudo mkdir -p $INSTALL_DIR

# Méthode 1: Tenter de télécharger depuis les snapshots Chromium
echo "📥 Tentative de téléchargement depuis les snapshots Chromium..."
cd /tmp

# URL alternative pour Chromium 138
CHROMIUM_URLS=(
    "https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/1387204/chrome-linux.zip"
    "https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/1387151/chrome-linux.zip"
    "https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/1380000/chrome-linux.zip"
)

DOWNLOAD_SUCCESS=false

for url in "${CHROMIUM_URLS[@]}"; do
    echo "🔄 Tentative avec: $url"
    if wget -q --show-progress "$url" -O chromium-138.zip; then
        echo "✅ Téléchargement réussi"
        DOWNLOAD_SUCCESS=true
        break
    else
        echo "❌ Échec avec cette URL"
        rm -f chromium-138.zip
    fi
done

# Si le téléchargement direct échoue, utiliser apt avec un dépôt spécifique
if [ "$DOWNLOAD_SUCCESS" = false ]; then
    echo "📥 Utilisation de la méthode apt avec dépôt spécifique..."
    
    # Ajouter le dépôt Google Chrome
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
    
    # Mettre à jour et installer
    sudo apt update
    sudo apt install -y google-chrome-stable
    
    # Créer des liens symboliques pour Chromium
    if [ -f "/usr/bin/google-chrome-stable" ]; then
        sudo ln -sf /usr/bin/google-chrome-stable /usr/bin/chromium-browser
        sudo ln -sf /usr/bin/google-chrome-stable /usr/bin/chromium
        echo "✅ Google Chrome installé et configuré comme Chromium"
        DOWNLOAD_SUCCESS=true
    fi
fi

# Si toujours pas de succès, essayer avec les backports Ubuntu
if [ "$DOWNLOAD_SUCCESS" = false ]; then
    echo "📥 Utilisation des backports Ubuntu..."
    
    # Ajouter les backports
    echo "deb http://archive.ubuntu.com/ubuntu $(lsb_release -cs)-backports main restricted universe multiverse" | sudo tee /etc/apt/sources.list.d/backports.list
    sudo apt update
    
    # Installer la version la plus récente disponible
    sudo apt install -y chromium-browser/$(lsb_release -cs)-backports
    
    if command -v chromium-browser &> /dev/null; then
        echo "✅ Chromium installé depuis les backports"
        DOWNLOAD_SUCCESS=true
    fi
fi

# Si le téléchargement direct a réussi, extraire l'archive
if [ "$DOWNLOAD_SUCCESS" = true ] && [ -f "chromium-138.zip" ]; then
    echo "📦 Extraction de l'archive..."
    sudo unzip -q chromium-138.zip -d $INSTALL_DIR
    sudo mv $INSTALL_DIR/chrome-linux/* $INSTALL_DIR/
    sudo rmdir $INSTALL_DIR/chrome-linux
    
    # Nettoyer
    rm -f chromium-138.zip
    
    # Créer les liens symboliques
    echo "🔗 Création des liens symboliques..."
    sudo ln -sf $INSTALL_DIR/chrome /usr/bin/chromium-browser
    sudo ln -sf $INSTALL_DIR/chrome /usr/bin/chromium
fi

# Vérifier l'installation
echo "🔍 Vérification de l'installation..."
if command -v chromium-browser &> /dev/null; then
    VERSION=$(chromium-browser --version)
    echo "✅ Chromium installé: $VERSION"
else
    echo "❌ Échec de l'installation"
    echo "💡 Solutions alternatives:"
    echo "1. Installer manuellement: sudo apt install chromium-browser"
    echo "2. Utiliser Chrome: sudo apt install google-chrome-stable"
    echo "3. Télécharger depuis: https://www.chromium.org/getting-involved/download-chromium"
    exit 1
fi

echo "✅ Installation terminée !"
echo "🚀 Vous pouvez maintenant utiliser: chromium-browser --version"
if [ -d "$INSTALL_DIR" ]; then
    echo "📍 Installation dans: $INSTALL_DIR"
fi 