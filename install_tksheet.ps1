# Script d'installation de TKSheet

Write-Host "=== Installation de TKSheet ===" -ForegroundColor Cyan

# Vérifier si l'environnement virtuel est activé
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Erreur : L'environnement virtuel n'est pas activé." -ForegroundColor Red
    Write-Host "Veuillez d'abord exécuter : .\activate_venv.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "Environnement virtuel détecté : $env:VIRTUAL_ENV" -ForegroundColor Green

# Installation de TKSheet
Write-Host "`nInstallation de TKSheet..." -ForegroundColor Yellow
pip install tksheet==7.5.12

# Vérification de l'installation
Write-Host "`nVérification de l'installation..." -ForegroundColor Yellow
try {
    $version = pip show tksheet | Select-String "Version"
    if ($version) {
        Write-Host "✓ TKSheet installé avec succès" -ForegroundColor Green
        Write-Host "Version : $version" -ForegroundColor Green
    } else {
        Write-Host "✗ TKSheet non installé" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ Erreur lors de l'installation de TKSheet" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ TKSheet installé avec succès !" -ForegroundColor Green
Write-Host "Vous pouvez maintenant tester avec : python test_tksheet.py" -ForegroundColor Cyan 