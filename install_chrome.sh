#!/bin/bash

# Script d'installation de Chrome pour Ubuntu

# Configuration du logging
LOG_FILE="chrome_install.log"
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
log_message "=== Installation de Chrome pour Ubuntu ==="

echo "🌐 Installation de Google Chrome pour Ubuntu"
echo ""

# Vérifier si Chrome est déjà installé
if command -v google-chrome &> /dev/null; then
    log_message "Chrome est déjà installé"
    CHROME_VERSION=$(google-chrome --version)
    log_message "Version Chrome: $CHROME_VERSION"
    echo "✅ Chrome est déjà installé: $CHROME_VERSION"
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

# Étape 2 : Installation des dépendances
log_message "Étape 2 : Installation des dépendances..."
echo "Installation des dépendances..."

if ! sudo apt install -y \
    wget \
    gnupg \
    ca-certificates \
    apt-transport-https \
    software-properties-common 2>&1 | tee -a "$LOG_FILE"; then
    handle_error "Échec de l'installation des dépendances"
fi

# Étape 3 : Ajout du dépôt Google Chrome
log_message "Étape 3 : Ajout du dépôt Google Chrome..."
echo "Ajout du dépôt Google Chrome..."

# Télécharger la clé GPG de Google
if ! wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add - 2>&1 | tee -a "$LOG_FILE"; then
    handle_error "Échec du téléchargement de la clé GPG"
fi

# Ajouter le dépôt Chrome
if ! echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list 2>&1 | tee -a "$LOG_FILE"; then
    handle_error "Échec de l'ajout du dépôt Chrome"
fi

# Étape 4 : Mise à jour et installation de Chrome
log_message "Étape 4 : Installation de Google Chrome..."
echo "Installation de Google Chrome..."

# Mettre à jour les paquets pour inclure le nouveau dépôt
if ! sudo apt update 2>&1 | tee -a "$LOG_FILE"; then
    handle_error "Échec de la mise à jour après ajout du dépôt"
fi

# Installer Chrome
if ! sudo apt install -y google-chrome-stable 2>&1 | tee -a "$LOG_FILE"; then
    handle_error "Échec de l'installation de Chrome"
fi

# Étape 5 : Vérification de l'installation
log_message "Étape 5 : Vérification de l'installation..."
echo "Vérification de l'installation..."

if command -v google-chrome &> /dev/null; then
    CHROME_VERSION=$(google-chrome --version)
    log_message "Chrome installé avec succès: $CHROME_VERSION"
    echo "✅ Chrome installé avec succès: $CHROME_VERSION"
else
    handle_error "Chrome n'a pas été installé correctement"
fi

# Étape 6 : Test de Chrome
log_message "Étape 6 : Test de Chrome..."
echo "Test de Chrome..."

# Test simple de Chrome
if google-chrome --version 2>&1 | tee -a "$LOG_FILE"; then
    log_message "Test de Chrome réussi"
    echo "✅ Test de Chrome réussi"
else
    log_message "ATTENTION: Test de Chrome échoué"
    echo "⚠️ Test de Chrome échoué, mais l'installation semble complète"
fi

# Étape 7 : Configuration pour WSL (si applicable)
log_message "Étape 7 : Configuration pour WSL..."
echo "Configuration pour WSL..."

# Vérifier si on est dans WSL
if grep -qi microsoft /proc/version; then
    log_message "WSL détecté, configuration spéciale..."
    echo "WSL détecté, configuration spéciale..."
    
    # Installer les dépendances supplémentaires pour WSL
    if ! sudo apt install -y \
        xvfb \
        x11-utils \
        x11-apps 2>&1 | tee -a "$LOG_FILE"; then
        log_message "ATTENTION: Impossible d'installer les dépendances X11 pour WSL"
        echo "⚠️ Impossible d'installer les dépendances X11 pour WSL"
    fi
    
    echo ""
    echo "📝 Note pour WSL :"
    echo "Pour utiliser Chrome dans WSL, vous devrez peut-être :"
    echo "1. Installer un serveur X11 sur Windows (VcXsrv, Xming, etc.)"
    echo "2. Exporter DISPLAY=:0 avant de lancer le script"
    echo "3. Ou utiliser Chrome en mode headless"
fi

log_message "=== Installation de Chrome terminée avec succès ==="
echo ""
echo "✅ Installation de Chrome terminée avec succès !"
echo "📋 Logs disponibles dans : $LOG_FILE"
echo "🌐 Chrome est maintenant prêt à être utilisé avec Selenium"
echo ""
echo "Appuyez sur une touche pour continuer..."
read -n 1 -s 