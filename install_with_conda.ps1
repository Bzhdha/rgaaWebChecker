# Script d'installation alternative utilisant conda (si disponible)

Write-Host "=== Installation alternative avec conda ===" -ForegroundColor Cyan

# Vérifier si conda est disponible
$condaPath = $null
if (Get-Command conda -ErrorAction SilentlyContinue) {
    $condaPath = "conda"
} elseif (Test-Path "$env:USERPROFILE\anaconda3\Scripts\conda.exe") {
    $condaPath = "$env:USERPROFILE\anaconda3\Scripts\conda.exe"
} elseif (Test-Path "$env:USERPROFILE\miniconda3\Scripts\conda.exe") {
    $condaPath = "$env:USERPROFILE\miniconda3\Scripts\conda.exe"
} else {
    Write-Host "Conda n'est pas installé ou n'est pas dans le PATH." -ForegroundColor Red
    Write-Host "Veuillez installer Anaconda ou Miniconda depuis :" -ForegroundColor Yellow
    Write-Host "https://docs.conda.io/en/latest/miniconda.html" -ForegroundColor Cyan
    exit 1
}

Write-Host "Conda trouvé : $condaPath" -ForegroundColor Green

# Vérifier si l'environnement virtuel est activé
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Erreur : L'environnement virtuel n'est pas activé." -ForegroundColor Red
    Write-Host "Veuillez d'abord exécuter : .\activate_venv.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "Environnement virtuel détecté : $env:VIRTUAL_ENV" -ForegroundColor Green

# Installation des packages problématiques avec conda
Write-Host "`nInstallation des packages avec conda..." -ForegroundColor Yellow

# Pillow
Write-Host "Installation de Pillow..." -ForegroundColor Yellow
& $condaPath install -c conda-forge pillow=9.5.0 -y

# lxml
Write-Host "Installation de lxml..." -ForegroundColor Yellow
& $condaPath install -c conda-forge lxml=4.9.3 -y

# Installation des autres packages avec pip
Write-Host "`nInstallation des autres packages avec pip..." -ForegroundColor Yellow
pip install selenium==4.18.1
pip install webdriver-manager==4.0.1
pip install markdown==3.5.2
pip install beautifulsoup4==4.12.3
pip install requests==2.31.0
pip install pdfkit==1.0.0
pip install tksheet==7.5.12

# Vérification finale
Write-Host "`nVérification de l'installation..." -ForegroundColor Yellow
$packages = @("selenium", "webdriver-manager", "Pillow", "markdown", "beautifulsoup4", "requests", "lxml", "pdfkit", "tksheet")

$allInstalled = $true
foreach ($package in $packages) {
    try {
        $version = pip show $package | Select-String "Version"
        if ($version) {
            Write-Host "✓ $package installé" -ForegroundColor Green
        } else {
            Write-Host "✗ $package non installé" -ForegroundColor Red
            $allInstalled = $false
        }
    } catch {
        Write-Host "✗ $package non installé" -ForegroundColor Red
        $allInstalled = $false
    }
}

if ($allInstalled) {
    Write-Host "`n✅ Toutes les dépendances sont installées avec succès !" -ForegroundColor Green
    New-Item -Path "venv\.dependencies_installed" -ItemType File -Force | Out-Null
} else {
    Write-Host "`n❌ Certaines dépendances n'ont pas pu être installées." -ForegroundColor Red
} 