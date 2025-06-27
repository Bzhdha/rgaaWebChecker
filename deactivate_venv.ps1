# Script PowerShell pour désactiver l'environnement virtuel

# Vérifier si l'environnement virtuel est activé
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Aucun environnement virtuel n'est actuellement activé." -ForegroundColor Yellow
    exit 1
}

# Désactiver l'environnement virtuel
deactivate

Write-Host "Environnement virtuel désactivé !" -ForegroundColor Green 