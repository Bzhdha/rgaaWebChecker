# Script PowerShell pour lancer l'interface graphique RGAA Web Checker
# Usage: .\launch_gui.ps1

param(
    [switch]$NoVenv,
    [switch]$Help
)

function Show-Help {
    Write-Host "RGAA Web Checker - Interface Graphique" -ForegroundColor Cyan
    Write-Host "=====================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\launch_gui.ps1              # Lance avec environnement virtuel automatique"
    Write-Host "  .\launch_gui.ps1 -NoVenv      # Lance sans environnement virtuel"
    Write-Host "  .\launch_gui.ps1 -Help        # Affiche cette aide"
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -NoVenv    Désactive l'activation automatique de l'environnement virtuel"
    Write-Host "  -Help      Affiche cette aide"
    Write-Host ""
}

if ($Help) {
    Show-Help
    exit 0
}

Write-Host "RGAA Web Checker - Interface Graphique" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
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

# Gestion de l'environnement virtuel
if (-not $NoVenv) {
    Write-Host "🔍 Vérification de l'environnement virtuel..." -ForegroundColor Yellow
    
    if (Test-Path "venv\Scripts\Activate.ps1") {
        Write-Host "✅ Environnement virtuel trouvé" -ForegroundColor Green
        Write-Host "🔄 Activation de l'environnement virtuel..." -ForegroundColor Yellow
        
        try {
            & "venv\Scripts\Activate.ps1"
            Write-Host "✅ Environnement virtuel activé" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  Erreur lors de l'activation de l'environnement virtuel" -ForegroundColor Yellow
            Write-Host "Tentative de lancement sans environnement virtuel..." -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  Aucun environnement virtuel trouvé" -ForegroundColor Yellow
        Write-Host "Tentative de lancement sans environnement virtuel..." -ForegroundColor Yellow
    }
}

# Vérifier les dépendances
Write-Host "🔍 Vérification des dépendances..." -ForegroundColor Yellow

$missingDeps = @()

try {
    python -c "import PIL" 2>$null
    Write-Host "✅ Pillow (PIL) disponible" -ForegroundColor Green
} catch {
    $missingDeps += "Pillow (PIL)"
    Write-Host "❌ Pillow (PIL) manquant" -ForegroundColor Red
}

try {
    python -c "import selenium" 2>$null
    Write-Host "✅ Selenium disponible" -ForegroundColor Green
} catch {
    $missingDeps += "selenium"
    Write-Host "❌ Selenium manquant" -ForegroundColor Red
}

try {
    python -c "import webdriver_manager" 2>$null
    Write-Host "✅ webdriver-manager disponible" -ForegroundColor Green
} catch {
    $missingDeps += "webdriver-manager"
    Write-Host "❌ webdriver-manager manquant" -ForegroundColor Red
}

if ($missingDeps.Count -gt 0) {
    Write-Host ""
    Write-Host "❌ Dépendances manquantes:" -ForegroundColor Red
    foreach ($dep in $missingDeps) {
        Write-Host "   - $dep" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Pour installer les dépendances manquantes:" -ForegroundColor Yellow
    Write-Host "pip install -r requirements.txt" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Ou utilisez le script d'installation automatique:" -ForegroundColor Yellow
    Write-Host ".\activate_venv.ps1" -ForegroundColor Cyan
    exit 1
}

# Vérifier que les modules de l'application existent
Write-Host "🔍 Vérification des modules de l'application..." -ForegroundColor Yellow

$requiredModules = @(
    "core.config",
    "core.crawler",
    "utils.log_utils",
    "modules.contrast_checker",
    "modules.dom_analyzer",
    "modules.color_simulator",
    "modules.tab_navigator",
    "modules.screen_reader",
    "modules.image_analyzer"
)

$missingModules = @()
foreach ($module in $requiredModules) {
    try {
        python -c "import $module" 2>$null
        Write-Host "✅ $module disponible" -ForegroundColor Green
    } catch {
        $missingModules += $module
        Write-Host "❌ $module manquant" -ForegroundColor Red
    }
}

if ($missingModules.Count -gt 0) {
    Write-Host ""
    Write-Host "❌ Modules de l'application manquants:" -ForegroundColor Red
    foreach ($module in $missingModules) {
        Write-Host "   - $module" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Assurez-vous d'être dans le répertoire racine de l'application." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "✅ Toutes les vérifications sont passées" -ForegroundColor Green
Write-Host "🚀 Lancement de l'interface graphique..." -ForegroundColor Cyan
Write-Host ""

# Lancer l'interface graphique
try {
    python launch_gui.py
    $exitCode = $LASTEXITCODE
} catch {
    Write-Host "❌ Erreur lors du lancement: $($_.Exception.Message)" -ForegroundColor Red
    $exitCode = 1
}

# Désactiver l'environnement virtuel si nécessaire
if (-not $NoVenv -and (Test-Path "venv\Scripts\deactivate.bat")) {
    Write-Host ""
    Write-Host "🔄 Désactivation de l'environnement virtuel..." -ForegroundColor Yellow
    & "venv\Scripts\deactivate.bat" 2>$null
}

exit $exitCode 