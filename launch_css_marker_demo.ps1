# Script PowerShell de lancement pour la démonstration du système de marquage CSS

Write-Host "🎨 Lancement de la démonstration CSS Marker" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

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

# Vérifier que les dépendances sont installées
Write-Host "🔍 Vérification des dépendances..." -ForegroundColor Yellow

try {
    python -c "import selenium" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Selenium non installé"
    }
    Write-Host "✅ Selenium est installé" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Selenium n'est pas installé. Installation..." -ForegroundColor Yellow
    pip install selenium
}

# Activer l'environnement virtuel si disponible
if (Test-Path "venv") {
    Write-Host "🔧 Activation de l'environnement virtuel..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
}

# Lancer la démonstration
Write-Host "🚀 Lancement de la démonstration..." -ForegroundColor Green
Write-Host ""

# Choisir le type de démonstration
Write-Host "Choisissez le type de démonstration :" -ForegroundColor White
Write-Host "1) Démonstration simple (recommandé)" -ForegroundColor White
Write-Host "2) Tests complets" -ForegroundColor White
Write-Host "3) Démonstration avec DOMAnalyzer" -ForegroundColor White
Write-Host ""
$choice = Read-Host "Votre choix (1-3)"

switch ($choice) {
    "1" {
        Write-Host "🎯 Lancement de la démonstration simple..." -ForegroundColor Green
        python demo_css_marker.py
    }
    "2" {
        Write-Host "🧪 Lancement des tests complets..." -ForegroundColor Green
        python test_css_marker.py
    }
    "3" {
        Write-Host "🔍 Lancement de la démonstration avec DOMAnalyzer..." -ForegroundColor Green
        Write-Host "Note: Cette option nécessite une page web réelle" -ForegroundColor Yellow
        Write-Host "Modifiez le script pour pointer vers une URL spécifique" -ForegroundColor Yellow
    }
    default {
        Write-Host "❌ Choix invalide" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "✅ Démonstration terminée !" -ForegroundColor Green
Write-Host ""
Write-Host "📚 Pour plus d'informations :" -ForegroundColor Cyan
Write-Host "   • Guide d'utilisation : docs/CSS_MARKER_GUIDE.md" -ForegroundColor White
Write-Host "   • Tests unitaires : test_css_marker.py" -ForegroundColor White
Write-Host "   • Démonstration : demo_css_marker.py" -ForegroundColor White
Write-Host ""
Write-Host "🎯 Fonctionnalités principales :" -ForegroundColor Cyan
Write-Host "   • Marquage visuel des éléments analysés" -ForegroundColor White
Write-Host "   • Indication de la conformité (vert/rouge)" -ForegroundColor White
Write-Host "   • Tooltips informatifs au survol" -ForegroundColor White
Write-Host "   • Mode production pour masquer les marquages" -ForegroundColor White
Write-Host "   • Intégration avec tous les modules d'analyse" -ForegroundColor White
