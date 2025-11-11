#!/usr/bin/env python3
"""
Test simple pour Chromium sur WSL
"""

import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import glob

def test_chromium_wsl():
    print("🔍 Test Chromium sur WSL")
    print("=" * 40)
    
    # Vérifier WSL
    is_wsl = os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower()
    print(f"WSL détecté: {is_wsl}")
    
    # Configuration Chrome
    chrome_options = Options()
    
    if is_wsl:
        print("Configuration WSL...")
        # Options essentielles pour WSL
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        # Options pour résoudre DevToolsActivePort
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--remote-debugging-address=0.0.0.0')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-setuid-sandbox')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--disable-translate')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-javascript')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--silent')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--disable-dev-tools')
        
        # Options spécifiques pour éviter les problèmes de port
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--metrics-recording-only')
        chrome_options.add_argument('--no-default-browser-check')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--safebrowsing-disable-auto-update')
        chrome_options.add_argument('--disable-component-update')
        chrome_options.add_argument('--disable-domain-reliability')
        chrome_options.add_argument('--disable-features=AudioServiceOutOfProcess')
        
        # Masquer l'automatisation
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # Configuration Chromium
    chrome_options.binary_location = "/usr/bin/chromium-browser"
    
    try:
        # Trouver ChromeDriver
        driver_dir = os.path.dirname(ChromeDriverManager().install())
        chromedriver_path = None
        for f in glob.glob(os.path.join(driver_dir, "chromedriver*")):
            if not f.endswith('.txt') and not f.endswith('.chromedriver') and 'THIRD_PARTY' not in f:
                chromedriver_path = f
                break
        
        if not chromedriver_path:
            raise Exception("ChromeDriver non trouvé")
        
        print(f"ChromeDriver: {chromedriver_path}")
        
        # Corriger les permissions
        if not os.access(chromedriver_path, os.X_OK):
            os.chmod(chromedriver_path, 0o755)
            print("Permissions corrigées")
        
        # Test de lancement
        print("Lancement du navigateur...")
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ Navigateur lancé")
        
        # Test de navigation
        print("Test de navigation...")
        driver.get("https://www.google.com")
        title = driver.title
        print(f"✅ Page chargée: {title}")
        
        driver.quit()
        print("✅ Test réussi !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = test_chromium_wsl()
    sys.exit(0 if success else 1) 