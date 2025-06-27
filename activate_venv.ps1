# Script PowerShell pour activer l'environnement virtuel

# Vérifier si l'environnement virtuel existe
if (-not (Test-Path "venv")) {
    Write-Host "L'environnement virtuel n'existe pas. Création en cours..." -ForegroundColor Yellow
    python -m venv venv
}

# Activer l'environnement virtuel
& "venv\Scripts\Activate.ps1"

# Vérifier si les dépendances sont installées
if (-not (Test-Path "venv\.dependencies_installed")) {
    Write-Host "Installation des dépendances..." -ForegroundColor Yellow
    
    # Mettre à jour pip et les outils de build
    Write-Host "Mise à jour de pip et des outils de build..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    pip install wheel setuptools --upgrade
    
    # Première tentative d'installation avec des versions précompilées
    Write-Host "Installation avec des versions précompilées..." -ForegroundColor Yellow
    $installResult = pip install --only-binary=all -r requirements.txt 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Erreur lors de l'installation des dépendances." -ForegroundColor Red
        Write-Host "Tentative d'installation package par package..." -ForegroundColor Yellow
        
        # Installation package par package avec des versions stables
        $packages = @(
            "selenium==4.18.1",
            "webdriver-manager==4.0.1", 
            "Pillow==9.5.0",
            "markdown==3.5.2",
            "beautifulsoup4==4.12.3",
            "requests==2.31.0",
            "lxml==4.9.3",
            "pdfkit==1.0.0"
        )
        
        $success = $true
        foreach ($package in $packages) {
            Write-Host "Installation de $package..." -ForegroundColor Yellow
            $result = pip install --only-binary=all $package 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Échec de l'installation de $package" -ForegroundColor Red
                Write-Host "Tentative sans --only-binary=all..." -ForegroundColor Yellow
                $result = pip install $package 2>&1
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "Échec définitif de $package" -ForegroundColor Red
                    $success = $false
                }
            }
        }
        
        if ($success) {
            Write-Host "Installation réussie avec les versions alternatives !" -ForegroundColor Green
            New-Item -Path "venv\.dependencies_installed" -ItemType File -Force | Out-Null
        } else {
            Write-Host "Échec de l'installation. Voici quelques solutions :" -ForegroundColor Red
            Write-Host "1. Exécutez le script de dépannage : .\fix_installation.ps1" -ForegroundColor Cyan
            Write-Host "2. Installez Visual C++ Build Tools pour Windows" -ForegroundColor Cyan
            Write-Host "3. Utilisez Anaconda/Miniconda pour une meilleure gestion des packages" -ForegroundColor Cyan
            Write-Host "4. Installez les packages manuellement un par un" -ForegroundColor Cyan
            exit 1
        }
    } else {
        New-Item -Path "venv\.dependencies_installed" -ItemType File -Force | Out-Null
    }
}

Write-Host "Environnement virtuel activé !" -ForegroundColor Green
Write-Host "Pour le désactiver, utilisez : .\deactivate_venv.ps1" -ForegroundColor Cyan 