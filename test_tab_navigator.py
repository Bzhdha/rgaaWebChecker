#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test du module de navigation tabulaire
Vérifie que les rapports sont générés avec les identifiants uniques (XPath)
"""

import sys
import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from modules.tab_navigator import TabNavigator
from utils.log_utils import setup_logger

def test_tab_navigator():
    """Test du module de navigation tabulaire"""
    
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
        
        # Initialiser le navigateur tabulaire
        tab_navigator = TabNavigator(driver, logger, tab_delay=0.5)  # Test avec délai de 0.5 seconde
        
        # Exécuter l'analyse de navigation tabulaire
        logger.info("Démarrage de l'analyse de navigation tabulaire...")
        results = tab_navigator.run()
        
        # Vérifier les résultats
        if results:
            logger.info(f"✅ Analyse terminée avec succès. {len(results)} éléments analysés.")
            
            # Vérifier que les fichiers de rapport ont été créés
            csv_file = "rapport_analyse_tab.csv"
            json_file = "rapport_analyse_tab.json"
            
            if os.path.exists(csv_file):
                logger.info(f"✅ Fichier CSV créé: {csv_file}")
            else:
                logger.error(f"❌ Fichier CSV manquant: {csv_file}")
            
            if os.path.exists(json_file):
                logger.info(f"✅ Fichier JSON créé: {json_file}")
            else:
                logger.error(f"❌ Fichier JSON manquant: {json_file}")
            
            # Afficher quelques exemples d'éléments avec leurs XPath
            logger.info("\n📋 Exemples d'éléments capturés:")
            for i, result in enumerate(results[:5]):  # Afficher les 5 premiers
                logger.info(f"  {i+1}. {result['tag']} - XPath: {result['xpath']}")
                if result['accessible_name']['name']:
                    logger.info(f"     Nom accessible: {result['accessible_name']['name']}")
                else:
                    logger.info(f"     Aucun nom accessible")
            
            # Vérifier la présence des identifiants uniques
            elements_with_xpath = [r for r in results if r['xpath'] and r['xpath'] != 'unknown']
            logger.info(f"\n🔗 Éléments avec XPath unique: {len(elements_with_xpath)}/{len(results)}")
            
            # Vérifier les noms accessibles
            elements_with_accessible_name = [r for r in results if r['accessible_name']['name']]
            logger.info(f"📝 Éléments avec nom accessible: {len(elements_with_accessible_name)}/{len(results)}")
            
        else:
            logger.warning("⚠️ Aucun élément capturé lors de l'analyse")
        
        # Fermer le driver
        driver.quit()
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Test du module de navigation tabulaire")
    print("=" * 50)
    
    success = test_tab_navigator()
    
    if success:
        print("\n✅ Test réussi !")
        print("📁 Vérifiez les fichiers générés:")
        print("   - rapport_analyse_tab.csv")
        print("   - rapport_analyse_tab.json")
        print("   - reports/focus_screenshots/ (captures d'écran)")
    else:
        print("\n❌ Test échoué !")
        sys.exit(1) 