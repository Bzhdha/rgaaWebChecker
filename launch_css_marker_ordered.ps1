# Script PowerShell de lancement pour le CSSMarker avec main_ordered.py

Write-Host "🎨 CSSMarker - Intégration avec main_ordered.py" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier que Python est installé
try {
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Python non trouvé"
    }
    Write-Host "✅ Python trouvé : $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python n'est pas installé ou n'est pas dans le PATH" -ForegroundColor Red
    exit 1
}

# Activer l'environnement virtuel si disponible
if (Test-Path "venv") {
    Write-Host "🔧 Activation de l'environnement virtuel..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
}

Write-Host "📋 Votre ligne de commande habituelle :" -ForegroundColor White
Write-Host "python main_ordered.py https://www.ouest-france.fr --modules screen --cookies `"OptanonAlertBoxClosed=2025-10-23T07:06:37.754Z`" --max-screenshots 200 --export-csv" -ForegroundColor Gray
Write-Host ""

Write-Host "🎯 Avec le CSSMarker activé :" -ForegroundColor White
Write-Host "python main_ordered.py https://www.ouest-france.fr --modules screen --cookies `"OptanonAlertBoxClosed=2025-10-23T07:06:37.754Z`" --max-screenshots 200 --export-csv --css-marker --css-marker-delay 10" -ForegroundColor Gray
Write-Host ""

Write-Host "✨ Nouvelles options disponibles :" -ForegroundColor Cyan
Write-Host "   --css-marker              : Active le marquage CSS des éléments analysés" -ForegroundColor White
Write-Host "   --css-marker-delay N      : Délai en secondes pour observer les marquages (défaut: 5)" -ForegroundColor White
Write-Host ""

# Menu de choix
Write-Host "Choisissez une option :" -ForegroundColor Yellow
Write-Host "1) Lancer votre commande habituelle avec CSSMarker" -ForegroundColor White
Write-Host "2) Démonstration interactive" -ForegroundColor White
Write-Host "3) Afficher l'aide" -ForegroundColor White
Write-Host "4) Quitter" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Votre choix (1-4)"

switch ($choice) {
    "1" {
        Write-Host "🚀 Lancement avec CSSMarker..." -ForegroundColor Green
        Write-Host "⏳ Cela peut prendre quelques minutes..." -ForegroundColor Yellow
        Write-Host ""
        
        python main_ordered.py https://www.ouest-france.fr `
            --modules screen `
            --cookies "OptanonAlertBoxClosed=2025-10-23T07:06:37.754Z" `
            --max-screenshots 200 `
            --export-csv `
            --css-marker `
            --css-marker-delay 10
    }
    "2" {
        Write-Host "🎯 Lancement de la démonstration interactive..." -ForegroundColor Green
        python demo_css_marker_ordered.py
    }
    "3" {
        Write-Host "📖 Affichage de l'aide..." -ForegroundColor Green
        python demo_css_marker_ordered.py --help
    }
    "4" {
        Write-Host "👋 Au revoir !" -ForegroundColor Green
        exit 0
    }
    default {
        Write-Host "❌ Choix invalide" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "✅ Opération terminée !" -ForegroundColor Green
Write-Host ""
Write-Host "🎨 Pendant l'analyse, vous avez pu observer :" -ForegroundColor Cyan
Write-Host "   • Les éléments analysés marqués visuellement" -ForegroundColor White
Write-Host "   • Les éléments conformes avec bordure verte et badge ✅" -ForegroundColor White
Write-Host "   • Les éléments non conformes avec bordure rouge et badge ⚠️" -ForegroundColor White
Write-Host "   • Les tooltips informatifs au survol des éléments" -ForegroundColor White
Write-Host "   • Les styles spécifiques par type d'élément" -ForegroundColor White
Write-Host ""
Write-Host "📚 Pour plus d'informations :" -ForegroundColor Cyan
Write-Host "   • Guide d'utilisation : docs/CSS_MARKER_GUIDE.md" -ForegroundColor White
Write-Host "   • README dédié : README_CSS_MARKER.md" -ForegroundColor White
Write-Host "   • Tests : test_css_marker.py" -ForegroundColor White
Write-Host "   • Démonstration : demo_css_marker.py" -ForegroundColor White
