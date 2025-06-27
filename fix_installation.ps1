# Script de dépannage pour l'installation des dépendances

Write-Host "=== Script de dépannage pour l'installation des dépendances ===" -ForegroundColor Cyan

# Vérifier si l'environnement virtuel est activé
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Erreur : L'environnement virtuel n'est pas activé." -ForegroundColor Red
    Write-Host "Veuillez d'abord exécuter : .\activate_venv.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "Environnement virtuel détecté : $env:VIRTUAL_ENV" -ForegroundColor Green

# Étape 1 : Mettre à jour pip
Write-Host "`nÉtape 1 : Mise à jour de pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Étape 2 : Installer les outils de build si nécessaire
Write-Host "`nÉtape 2 : Installation des outils de build..." -ForegroundColor Yellow
pip install wheel setuptools --upgrade

# Étape 3 : Tentative d'installation avec des versions précompilées
Write-Host "`nÉtape 3 : Installation avec des versions précompilées..." -ForegroundColor Yellow
pip install --only-binary=all selenium==4.18.1 webdriver-manager==4.0.1 markdown==3.5.2 beautifulsoup4==4.12.3 requests==2.31.0

# Étape 4 : Installation de Pillow avec une version très stable
Write-Host "`nÉtape 4 : Installation de Pillow..." -ForegroundColor Yellow
$pillowVersions = @("9.5.0", "9.4.0", "9.3.0", "9.2.0")
$pillowInstalled = $false

foreach ($version in $pillowVersions) {
    Write-Host "Tentative avec Pillow $version..." -ForegroundColor Yellow
    $result = pip install --only-binary=all "Pillow==$version" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Pillow $version installé avec succès !" -ForegroundColor Green
        $pillowInstalled = $true
        break
    } else {
        Write-Host "Échec avec Pillow $version, tentative suivante..." -ForegroundColor Red
    }
}

if (-not $pillowInstalled) {
    Write-Host "Tentative d'installation de Pillow sans --only-binary=all..." -ForegroundColor Yellow
    pip install Pillow==9.5.0
    if ($LASTEXITCODE -eq 0) {
        $pillowInstalled = $true
        Write-Host "Pillow installé avec succès !" -ForegroundColor Green
    }
}

# Étape 5 : Installation de lxml avec une version stable
Write-Host "`nÉtape 5 : Installation de lxml..." -ForegroundColor Yellow
$lxmlVersions = @("4.9.3", "4.9.2", "4.9.1", "4.9.0")
$lxmlInstalled = $false

foreach ($version in $lxmlVersions) {
    Write-Host "Tentative avec lxml $version..." -ForegroundColor Yellow
    $result = pip install --only-binary=all "lxml==$version" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "lxml $version installé avec succès !" -ForegroundColor Green
        $lxmlInstalled = $true
        break
    } else {
        Write-Host "Échec avec lxml $version, tentative suivante..." -ForegroundColor Red
    }
}

if (-not $lxmlInstalled) {
    Write-Host "Tentative d'installation de lxml sans --only-binary=all..." -ForegroundColor Yellow
    pip install lxml==4.9.3
    if ($LASTEXITCODE -eq 0) {
        $lxmlInstalled = $true
        Write-Host "lxml installé avec succès !" -ForegroundColor Green
    }
}

# Étape 6 : Tentative d'installation de pdfkit
Write-Host "`nÉtape 6 : Installation de pdfkit..." -ForegroundColor Yellow
pip install pdfkit==1.0.0

# Vérification finale
Write-Host "`nVérification de l'installation..." -ForegroundColor Yellow
$packages = @("selenium", "webdriver-manager", "Pillow", "markdown", "beautifulsoup4", "requests", "lxml", "pdfkit")

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
    Write-Host "Solutions alternatives :" -ForegroundColor Yellow
    Write-Host "1. Installez Visual C++ Build Tools : https://visualstudio.microsoft.com/visual-cpp-build-tools/" -ForegroundColor Cyan
    Write-Host "2. Utilisez Anaconda/Miniconda pour une meilleure gestion des packages" -ForegroundColor Cyan
    Write-Host "3. Installez les packages un par un avec des versions spécifiques" -ForegroundColor Cyan
    Write-Host "4. Utilisez conda pour installer Pillow et lxml : conda install pillow lxml" -ForegroundColor Cyan
} 