#!/usr/bin/env python3
"""
Script de test pour Chromium sur WSL
Diagnostique les problèmes de DevToolsActivePort et autres erreurs courantes
"""

import os
import sys
import subprocess
import platform
import glob
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def check_wsl():
    """Vérifie si on est sur WSL"""
    try:
        with open('/proc/version', 'r') as f:
            version_info = f.read().lower()
            return 'microsoft' in version_info
    except:
        return False

def find_chromium_binary():
    """Trouve le binaire Chromium"""
    chromium_paths = [
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/snap/bin/chromium",
        "/usr/bin/google-chrome-stable"
    ]
    
    for path in chromium_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    return None

def test_chromium_basic():
    """Test basique de Chromium"""
    print("=== Test basique de Chromium ===")
    
    chromium_binary = find_chromium_binary()
    if not chromium_binary:
        print("❌ Aucun binaire Chromium trouvé")
        return False
    
    print(f"✅ Binaire Chromium trouvé: {chromium_binary}")
    
    # Test de version
    try:
        result = subprocess.run([chromium_binary, '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Version Chromium: {result.stdout.strip()}")
        else:
            print(f"❌ Erreur version: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erreur lors du test de version: {e}")
        return False
    
    return True

def test_chromedriver():
    """Test du ChromeDriver"""
    print("\n=== Test du ChromeDriver ===")
    
    try:
        driver_dir = os.path.dirname(ChromeDriverManager().install())
        print(f"✅ Répertoire ChromeDriver: {driver_dir}")
        
        # Chercher le vrai binaire chromedriver
        chromedriver_path = None
        for f in glob.glob(os.path.join(driver_dir, "chromedriver*")):
            if not f.endswith('.txt') and not f.endswith('.chromedriver') and not 'THIRD_PARTY' in f:
                chromedriver_path = f
                break
        
        if not chromedriver_path:
            print("❌ Aucun binaire chromedriver trouvé")
            return None
        
        print(f"✅ ChromeDriver trouvé: {chromedriver_path}")
        
        # Vérifier les permissions
        if os.access(chromedriver_path, os.X_OK):
            print("✅ ChromeDriver est exécutable")
        else:
            print("⚠️  ChromeDriver n'est pas exécutable, correction...")
            os.chmod(chromedriver_path, 0o755)
            print("✅ Permissions corrigées")
        
        return chromedriver_path
    except Exception as e:
        print(f"❌ Erreur ChromeDriver: {e}")
        return None

def test_selenium_chromium():
    """Test Selenium avec Chromium"""
    print("\n=== Test Selenium avec Chromium ===")
    
    driver_path = test_chromedriver()
    if not driver_path:
        return False
    
    chromium_binary = find_chromium_binary()
    if not chromium_binary:
        return False
    
    # Configuration des options
    chrome_options = Options()
    
    # Options de base
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    
    # Options spécifiques WSL
    if check_wsl():
        print("🌐 WSL détecté, ajout des options spécifiques...")
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-setuid-sandbox')
        chrome_options.add_argument('--silent')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # Options Chromium
    chrome_options.binary_location = chromium_binary
    chrome_options.add_argument('--disable-background-timer-throttling')
    chrome_options.add_argument('--disable-backgrounding-occluded-windows')
    chrome_options.add_argument('--disable-renderer-backgrounding')
    chrome_options.add_argument('--disable-features=TranslateUI')
    chrome_options.add_argument('--disable-ipc-flooding-protection')
    
    # Test de connexion
    try:
        print("🚀 Lancement du navigateur...")
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ Navigateur lancé avec succès")
        
        # Test de navigation
        print("🌐 Test de navigation...")
        driver.get("https://www.google.com")
        title = driver.title
        print(f"✅ Page chargée: {title}")
        
        # Test de screenshot
        print("📸 Test de screenshot...")
        screenshot_path = "test_screenshot.png"
        driver.save_screenshot(screenshot_path)
        if os.path.exists(screenshot_path):
            print(f"✅ Screenshot créé: {screenshot_path}")
            os.remove(screenshot_path)  # Nettoyer
        else:
            print("❌ Échec du screenshot")
        
        driver.quit()
        print("✅ Test Selenium réussi")
        return True
        
    except Exception as e:
        print(f"❌ Erreur Selenium: {e}")
        return False

def main():
    """Fonction principale"""
    print("🔍 Diagnostic Chromium sur WSL")
    print("=" * 50)
    
    # Informations système
    print(f"OS: {platform.system()}")
    print(f"Architecture: {platform.machine()}")
    print(f"WSL: {'Oui' if check_wsl() else 'Non'}")
    
    # Tests
    if not test_chromium_basic():
        print("\n❌ Test basique échoué")
        return 1
    
    if not test_selenium_chromium():
        print("\n❌ Test Selenium échoué")
        return 1
    
    print("\n🎉 Tous les tests sont passés !")
    print("Vous pouvez maintenant utiliser Chromium avec votre script principal.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 