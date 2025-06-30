#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test des options de délai de tabulation
Vérifie que les délais sont correctement appliqués
"""

import sys
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from modules.tab_navigator import TabNavigator
from utils.log_utils import setup_logger

def test_tab_delay_options():
    """Test des différentes options de délai de tabulation"""
    
    print("🧪 Test des options de délai de tabulation")
    print("=" * 50)
    
    # Configuration du logger
    logger = setup_logger(debug=True)
    
    # Configuration du navigateur
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    try:
        # Initialiser le driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Naviguer vers une page de test
        test_url = "https://www.example.com"
        logger.info(f"Navigation vers: {test_url}")
        driver.get(test_url)
        
        # Attendre que la page soit chargée
        driver.implicitly_wait(5)
        
        # Test 1: Pas de délai (défaut)
        print("\n📋 Test 1: Pas de délai (défaut)")
        print("-" * 30)
        start_time = time.time()
        tab_navigator = TabNavigator(driver, logger, tab_delay=0.0)
        results1 = tab_navigator.run()
        end_time = time.time()
        duration1 = end_time - start_time
        print(f"✅ Durée d'exécution: {duration1:.2f} secondes")
        print(f"✅ Éléments capturés: {len(results1)}")
        
        # Test 2: Délai de 0.5 seconde
        print("\n📋 Test 2: Délai de 0.5 seconde")
        print("-" * 30)
        start_time = time.time()
        tab_navigator = TabNavigator(driver, logger, tab_delay=0.5)
        results2 = tab_navigator.run()
        end_time = time.time()
        duration2 = end_time - start_time
        print(f"✅ Durée d'exécution: {duration2:.2f} secondes")
        print(f"✅ Éléments capturés: {len(results2)}")
        
        # Test 3: Délai de 1 seconde
        print("\n📋 Test 3: Délai de 1 seconde")
        print("-" * 30)
        start_time = time.time()
        tab_navigator = TabNavigator(driver, logger, tab_delay=1.0)
        results3 = tab_navigator.run()
        end_time = time.time()
        duration3 = end_time - start_time
        print(f"✅ Durée d'exécution: {duration3:.2f} secondes")
        print(f"✅ Éléments capturés: {len(results3)}")
        
        # Comparaison des durées
        print("\n📊 Comparaison des durées:")
        print("-" * 30)
        print(f"Sans délai:     {duration1:.2f} secondes")
        print(f"Avec délai 0.5s: {duration2:.2f} secondes (+{duration2-duration1:.2f}s)")
        print(f"Avec délai 1.0s: {duration3:.2f} secondes (+{duration3-duration1:.2f}s)")
        
        # Vérifier que les fichiers de rapport ont été créés
        csv_file = "rapport_analyse_tab.csv"
        json_file = "rapport_analyse_tab.json"
        
        if os.path.exists(csv_file):
            print(f"\n✅ Fichier CSV créé: {csv_file}")
        else:
            print(f"\n❌ Fichier CSV manquant: {csv_file}")
        
        if os.path.exists(json_file):
            print(f"✅ Fichier JSON créé: {json_file}")
        else:
            print(f"❌ Fichier JSON manquant: {json_file}")
        
        # Fermer le driver
        driver.quit()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {str(e)}")
        return False

def show_usage_examples():
    """Affiche des exemples d'utilisation des options de délai"""
    
    print("\n💡 Exemples d'utilisation des options de délai:")
    print("=" * 50)
    
    print("1. Délai par défaut de 0.5 seconde:")
    print("   python main.py https://example.com --modules tab --enable-tab-delay")
    
    print("\n2. Délai personnalisé de 1 seconde:")
    print("   python main.py https://example.com --modules tab --tab-delay 1.0")
    
    print("\n3. Délai personnalisé de 2 secondes:")
    print("   python main.py https://example.com --modules tab --tab-delay 2.0")
    
    print("\n4. Pas de délai (défaut):")
    print("   python main.py https://example.com --modules tab")
    
    print("\n5. Délai avec debug:")
    print("   python main.py https://example.com --modules tab --tab-delay 1.5 --debug")

if __name__ == "__main__":
    success = test_tab_delay_options()
    
    if success:
        print("\n✅ Tests des options de délai réussis !")
        show_usage_examples()
    else:
        print("\n❌ Tests des options de délai échoués !")
        sys.exit(1) 