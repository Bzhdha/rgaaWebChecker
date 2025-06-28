# Script PowerShell pour lancer la démonstration de l'interface graphique
# Usage: .\demo_gui.ps1

Write-Host "🎯 RGAA Web Checker - Démonstration Interface Graphique" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Cette démonstration lance l'interface graphique avec des données fictives" -ForegroundColor Yellow
Write-Host "pour tester toutes les fonctionnalités sans effectuer de vraie analyse." -ForegroundColor Yellow
Write-Host ""

# Vérifier si Python est installé
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python détecté: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python n'est pas installé ou n'est pas dans le PATH" -ForegroundColor Red
    Write-Host "Veuillez installer Python depuis https://python.org" -ForegroundColor Yellow
    exit 1
}

# Vérifier si tkinter est disponible
try {
    python -c "import tkinter; print('tkinter disponible')" 2>$null
    Write-Host "✅ Tkinter disponible" -ForegroundColor Green
} catch {
    Write-Host "❌ Tkinter n'est pas disponible" -ForegroundColor Red
    Write-Host "Tkinter est généralement inclus avec Python. Vérifiez votre installation." -ForegroundColor Yellow
    exit 1
}

# Vérifier si PIL est disponible
try {
    python -c "import PIL; print('Pillow disponible')" 2>$null
    Write-Host "✅ Pillow (PIL) disponible" -ForegroundColor Green
} catch {
    Write-Host "❌ Pillow (PIL) manquant" -ForegroundColor Red
    Write-Host "Installer: pip install Pillow" -ForegroundColor Yellow
    exit 1
}

# Vérifier que le script de démonstration existe
if (-not (Test-Path "demo_gui.py")) {
    Write-Host "❌ demo_gui.py non trouvé" -ForegroundColor Red
    Write-Host "Assurez-vous d'être dans le répertoire racine de l'application" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "✅ Toutes les vérifications sont passées" -ForegroundColor Green
Write-Host "🚀 Lancement de la démonstration..." -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 Fonctionnalités de la démonstration :" -ForegroundColor Yellow
Write-Host "  • Interface de configuration" -ForegroundColor White
Write-Host "  • Résultats fictifs avec statistiques" -ForegroundColor White
Write-Host "  • Export CSV/JSON" -ForegroundColor White
Write-Host "  • Visualisation d'images" -ForegroundColor White
Write-Host "  • Gestion des logs" -ForegroundColor White
Write-Host ""

# Lancer la démonstration
try {
    python demo_gui.py
    $exitCode = $LASTEXITCODE
} catch {
    Write-Host "❌ Erreur lors du lancement: $($_.Exception.Message)" -ForegroundColor Red
    $exitCode = 1
}

Write-Host ""
Write-Host "🎯 Démonstration terminée" -ForegroundColor Green
Write-Host "Pour une vraie analyse, utilisez : .\launch_gui.ps1" -ForegroundColor Cyan

exit $exitCode 