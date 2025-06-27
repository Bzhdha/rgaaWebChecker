#!/bin/bash

# Configuration du logging
LOG_FILE="install.log"
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
log_message "=== Début de l'activation de l'environnement virtuel ==="

# Vérifier si python3-venv est installé
log_message "Vérification de python3-venv..."
if ! python3 -c "import venv" 2>/dev/null; then
    log_message "ERREUR: Le package python3-venv n'est pas installé."
    log_message "Installation automatique des prérequis..."
    
    # Détecter la version de Python
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    log_message "Version Python détectée: $PYTHON_VERSION"
    
    # Installer le bon package selon la version
    if command -v apt &> /dev/null; then
        log_message "Installation de python3-venv via apt..."
        if ! sudo apt update 2>&1 | tee -a "$LOG_FILE"; then
            handle_error "Échec de la mise à jour des paquets"
        fi
        
        # Essayer d'abord la version spécifique, puis la version générique
        if ! sudo apt install -y "python3-${PYTHON_VERSION}-venv" 2>&1 | tee -a "$LOG_FILE"; then
            log_message "Échec avec la version spécifique, tentative avec python3-venv..."
            if ! sudo apt install -y python3-venv 2>&1 | tee -a "$LOG_FILE"; then
                handle_error "Impossible d'installer python3-venv. Veuillez exécuter manuellement : sudo apt install python3-venv"
            fi
        fi
    else
        handle_error "Le package python3-venv n'est pas installé et apt n'est pas disponible. Veuillez l'installer manuellement."
    fi
fi

# Vérifier si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    log_message "L'environnement virtuel n'existe pas. Création en cours..."
    
    # Créer l'environnement virtuel et capturer la sortie
    CREATE_OUTPUT=$(python3 -m venv venv 2>&1)
    CREATE_EXIT_CODE=$?
    
    # Log de la sortie
    log_message "Sortie de la création: $CREATE_OUTPUT"
    
    if [ $CREATE_EXIT_CODE -ne 0 ]; then
        handle_error "La création de l'environnement virtuel a échoué. Sortie: $CREATE_OUTPUT"
    fi
    
    # Vérifier si la création a vraiment réussi
    if [ ! -d "venv/bin" ] || [ ! -f "venv/bin/activate" ]; then
        handle_error "La création de l'environnement virtuel semble avoir échoué. Le dossier venv/bin n'existe pas."
    fi
    log_message "Environnement virtuel créé avec succès"
else
    log_message "Environnement virtuel existant détecté"
fi

# Activer l'environnement virtuel
log_message "Activation de l'environnement virtuel..."
if [ ! -f "venv/bin/activate" ]; then
    handle_error "Le fichier d'activation venv/bin/activate n'existe pas. L'environnement virtuel n'a pas été créé correctement."
fi

# Activer l'environnement virtuel
source venv/bin/activate
if [ -z "$VIRTUAL_ENV" ]; then
    handle_error "L'activation de l'environnement virtuel a échoué. VIRTUAL_ENV n'est pas défini."
fi
log_message "Environnement virtuel activé avec succès: $VIRTUAL_ENV"

# Vérifier si les dépendances sont installées
if [ ! -f "venv/.dependencies_installed" ]; then
    log_message "Installation des dépendances..."
    
    # Mettre à jour pip
    log_message "Mise à jour de pip..."
    if ! pip install --upgrade pip 2>&1 | tee -a "$LOG_FILE"; then
        log_message "ATTENTION: Échec de la mise à jour de pip, continuation..."
    fi
    
    # Installer les dépendances
    log_message "Installation des dépendances depuis requirements.txt..."
    if pip install -r requirements.txt 2>&1 | tee -a "$LOG_FILE"; then
        touch venv/.dependencies_installed
        log_message "Dépendances installées avec succès !"
    else
        log_message "ERREUR: Échec de l'installation des dépendances"
        log_message "Tentative d'installation package par package..."
        
        # Installation package par package
        packages=(
            "selenium==4.18.1"
            "webdriver-manager==4.0.1"
            "Pillow==9.5.0"
            "markdown==3.5.2"
            "beautifulsoup4==4.12.3"
            "requests==2.31.0"
            "lxml==4.9.3"
            "pdfkit==1.0.0"
        )
        
        success=true
        for package in "${packages[@]}"; do
            log_message "Installation de $package..."
            if pip install "$package" 2>&1 | tee -a "$LOG_FILE"; then
                log_message "✓ $package installé avec succès"
            else
                log_message "✗ Échec de l'installation de $package"
                success=false
            fi
        done
        
        if [ "$success" = true ]; then
            touch venv/.dependencies_installed
            log_message "Toutes les dépendances installées avec succès !"
        else
            handle_error "Certaines dépendances n'ont pas pu être installées. Consultez $LOG_FILE pour plus de détails. Veuillez exécuter le script d'installation Ubuntu : chmod +x install_ubuntu.sh && ./install_ubuntu.sh"
        fi
    fi
else
    log_message "Dépendances déjà installées"
fi

log_message "=== Activation terminée avec succès ==="
echo ""
echo "✅ Environnement virtuel activé !"
echo "📋 Logs disponibles dans : $LOG_FILE"
echo "🚪 Pour le désactiver, utilisez : ./deactivate_venv.sh"
echo ""
echo "Appuyez sur une touche pour continuer..."
read -n 1 -s 