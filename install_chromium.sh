#!/bin/bash

# Script d'installation de Chromium pour Ubuntu

# Configuration du logging
LOG_FILE="chromium_install.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Fonction de logging
log_message() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

# Fonction pour gérer les erreurs
handle_error() {
    log_message "ERREUR: $1"
    log_message "Le script s'est arrêté à cause d'une erreur."
    log_message "Consultez le fichier $LOG_FILE pour plus de détails."
    echo ""
    echo "Appuyez sur une touche pour fermer cette fenêtre..."
    read -n 1 -s
    exit 1
}

# Rediriger les erreurs vers le log
exec 2>> "$LOG_FILE"

# Démarrer le logging
log_message "=== Installation de Chromium pour Ubuntu ==="

echo "🌐 Installation de Chromium pour Ubuntu"
echo ""

# Vérifier si Chromium est déjà installé
if command -v chromium-browser &> /dev/null; then
    log_message "Chromium est déjà installé"
    CHROMIUM_VERSION=$(chromium-browser --version)
    log_message "Version Chromium: $CHROMIUM_VERSION"
    echo "✅ Chromium est déjà installé: $CHROMIUM_VERSION"
    echo ""
    echo "Appuyez sur une touche pour continuer..."
    read -n 1 -s
    exit 0
fi

# Étape 1 : Mise à jour des paquets
log_message "Étape 1 : Mise à jour des paquets système..."
echo "Mise à jour des paquets système..."

if ! sudo apt update 2>&1 | tee -a "$LOG_FILE"; then
    handle_error "Échec de la mise à jour des paquets"
fi

# Étape 2 : Installation de Chromium
log_message "Étape 2 : Installation de Chromium..."
echo "Installation de Chromium..."

if ! sudo apt install -y chromium-browser 2>&1 | tee -a "$LOG_FILE"; then
    handle_error "Échec de l'installation de Chromium"
fi

# Étape 3 : Installation des dépendances supplémentaires
log_message "Étape 3 : Installation des dépendances supplémentaires..."
echo "Installation des dépendances supplémentaires..."

# Installer les dépendances pour WSL si nécessaire
if grep -qi microsoft /proc/version; then
    log_message "WSL détecté, installation des dépendances X11..."
    if ! sudo apt install -y \
        xvfb \
        x11-utils \
        x11-apps \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libatspi2.0-0 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        libxss1 \
        libxtst6 \
        xdg-utils 2>&1 | tee -a "$LOG_FILE"; then
        log_message "ATTENTION: Impossible d'installer toutes les dépendances X11 pour WSL"
        echo "⚠️ Impossible d'installer toutes les dépendances X11 pour WSL"
    fi
fi

# Étape 4 : Vérification de l'installation
log_message "Étape 4 : Vérification de l'installation..."
echo "Vérification de l'installation..."

if command -v chromium-browser &> /dev/null; then
    CHROMIUM_VERSION=$(chromium-browser --version)
    log_message "Chromium installé avec succès: $CHROMIUM_VERSION"
    echo "✅ Chromium installé avec succès: $CHROMIUM_VERSION"
else
    handle_error "Chromium n'a pas été installé correctement"
fi

# Étape 5 : Test de Chromium
log_message "Étape 5 : Test de Chromium..."
echo "Test de Chromium..."

# Test simple de Chromium
if chromium-browser --version 2>&1 | tee -a "$LOG_FILE"; then
    log_message "Test de Chromium réussi"
    echo "✅ Test de Chromium réussi"
else
    log_message "ATTENTION: Test de Chromium échoué"
    echo "⚠️ Test de Chromium échoué, mais l'installation semble complète"
fi

# Étape 6 : Configuration pour WSL (si applicable)
log_message "Étape 6 : Configuration pour WSL..."
echo "Configuration pour WSL..."

# Vérifier si on est dans WSL
if grep -qi microsoft /proc/version; then
    log_message "WSL détecté, configuration spéciale..."
    echo "WSL détecté, configuration spéciale..."
    
    echo ""
    echo "📝 Note pour WSL :"
    echo "Pour utiliser Chromium dans WSL, vous devrez peut-être :"
    echo "1. Installer un serveur X11 sur Windows (VcXsrv, Xming, etc.)"
    echo "2. Exporter DISPLAY=:0 avant de lancer le script"
    echo "3. Ou utiliser Chromium en mode headless"
    echo ""
    echo "Configuration recommandée pour WSL :"
    echo "export DISPLAY=:0"
    echo "chromium-browser --headless --no-sandbox --disable-dev-shm-usage"
fi

# Étape 7 : Création d'un alias pour faciliter l'utilisation
log_message "Étape 7 : Création d'alias..."
echo "Création d'alias..."

# Créer un alias pour chromium
if ! grep -q "alias chromium=" ~/.bashrc 2>/dev/null; then
    echo 'alias chromium="chromium-browser"' >> ~/.bashrc
    log_message "Alias 'chromium' créé dans ~/.bashrc"
    echo "✅ Alias 'chromium' créé dans ~/.bashrc"
    echo "   Redémarrez votre terminal ou exécutez : source ~/.bashrc"
else
    log_message "Alias 'chromium' existe déjà"
    echo "ℹ️ Alias 'chromium' existe déjà"
fi

log_message "=== Installation de Chromium terminée avec succès ==="
echo ""
echo "✅ Installation de Chromium terminée avec succès !"
echo "📋 Logs disponibles dans : $LOG_FILE"
echo "🌐 Chromium est maintenant prêt à être utilisé avec Selenium"
echo "🔧 Utilisez 'chromium-browser' ou 'chromium' pour lancer le navigateur"
echo ""
echo "Appuyez sur une touche pour continuer..."
read -n 1 -s 