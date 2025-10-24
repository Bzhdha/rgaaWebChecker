#!/usr/bin/env python3
"""
Test du système de marquage CSS pour l'analyse d'accessibilité
Démontre l'utilisation du CSSMarker pour marquer les éléments analysés
"""

import sys
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.css_marker import CSSMarker
from modules.dom_analyzer import DOMAnalyzer

def setup_logging():
    """Configure le système de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_css_marker.log')
        ]
    )
    return logging.getLogger(__name__)

def setup_driver():
    """Configure le driver Selenium"""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Optionnel : mode headless pour les tests
    # chrome_options.add_argument('--headless')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Erreur lors de l'initialisation du driver Chrome : {e}")
        print("Tentative avec Chromium...")
        try:
            chrome_options.binary_location = "/usr/bin/chromium-browser"
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e2:
            print(f"Erreur avec Chromium : {e2}")
            raise

def test_css_marker_basic():
    """Test basique du CSSMarker"""
    logger = setup_logging()
    driver = None
    
    try:
        logger.info("🚀 Démarrage du test CSSMarker basique")
        
        # Configuration du driver
        driver = setup_driver()
        
        # Créer une page de test simple
        test_html = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Test CSS Marker</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .container { max-width: 800px; margin: 0 auto; }
                h1 { color: #333; }
                .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Test du système de marquage CSS</h1>
                
                <section class="section">
                    <h2>Section 1 - Images</h2>
                    <img src="https://via.placeholder.com/150" alt="Image de test" id="test-image">
                    <img src="https://via.placeholder.com/150" id="image-sans-alt">
                </section>
                
                <section class="section">
                    <h2>Section 2 - Liens</h2>
                    <a href="https://example.com" id="lien-avec-texte">Lien avec texte</a>
                    <a href="https://example.com" id="lien-sans-texte"></a>
                </section>
                
                <section class="section">
                    <h2>Section 3 - Boutons</h2>
                    <button id="bouton-normal">Bouton normal</button>
                    <button id="bouton-aria" aria-label="Bouton avec aria-label">Bouton ARIA</button>
                </section>
                
                <section class="section">
                    <h2>Section 4 - Formulaires</h2>
                    <form id="form-test">
                        <label for="input-test">Champ de test :</label>
                        <input type="text" id="input-test" name="test">
                        <button type="submit">Envoyer</button>
                    </form>
                </section>
                
                <section class="section">
                    <h2>Section 5 - Landmarks</h2>
                    <nav role="navigation" id="nav-test">
                        <ul>
                            <li><a href="#home">Accueil</a></li>
                            <li><a href="#about">À propos</a></li>
                        </ul>
                    </nav>
                    <main role="main" id="main-test">
                        <p>Contenu principal</p>
                    </main>
                </section>
            </div>
        </body>
        </html>
        """
        
        # Charger la page de test
        driver.get("data:text/html;charset=utf-8," + test_html)
        
        # Attendre que la page soit chargée
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        logger.info("📄 Page de test chargée avec succès")
        
        # Initialiser le CSSMarker
        css_marker = CSSMarker(driver, logger)
        
        # Test 1: Marquage d'éléments individuels
        logger.info("🔍 Test 1: Marquage d'éléments individuels")
        
        # Marquer une image conforme
        image_conforme = driver.find_element(By.ID, "test-image")
        css_marker.mark_element(
            element=image_conforme,
            element_type="image",
            issues=[],
            compliant=True,
            info="Image avec attribut alt conforme"
        )
        
        # Marquer une image non conforme
        image_non_conforme = driver.find_element(By.ID, "image-sans-alt")
        css_marker.mark_element(
            element=image_non_conforme,
            element_type="image",
            issues=["Image sans attribut alt"],
            compliant=False,
            info="Image sans attribut alt - non conforme"
        )
        
        # Marquer un lien conforme
        lien_conforme = driver.find_element(By.ID, "lien-avec-texte")
        css_marker.mark_element(
            element=lien_conforme,
            element_type="link",
            issues=[],
            compliant=True,
            info="Lien avec texte visible - conforme"
        )
        
        # Marquer un lien non conforme
        lien_non_conforme = driver.find_element(By.ID, "lien-sans-texte")
        css_marker.mark_element(
            element=lien_non_conforme,
            element_type="link",
            issues=["Lien sans texte visible"],
            compliant=False,
            info="Lien sans texte visible - non conforme"
        )
        
        # Marquer un bouton
        bouton = driver.find_element(By.ID, "bouton-normal")
        css_marker.mark_element(
            element=bouton,
            element_type="button",
            issues=[],
            compliant=True,
            info="Bouton normal - conforme"
        )
        
        # Marquer un landmark
        nav = driver.find_element(By.ID, "nav-test")
        css_marker.mark_element(
            element=nav,
            element_type="landmark",
            issues=[],
            compliant=True,
            info="Navigation landmark - conforme"
        )
        
        logger.info("✅ Marquage individuel terminé")
        
        # Test 2: Marquage en lot
        logger.info("🔍 Test 2: Marquage en lot")
        
        # Récupérer tous les éléments à marquer
        elements_to_mark = []
        
        # Titres
        titres = driver.find_elements(By.TAG_NAME, "h1") + driver.find_elements(By.TAG_NAME, "h2")
        for titre in titres:
            elements_to_mark.append({
                'element': titre,
                'type': 'heading',
                'issues': [],
                'compliant': True,
                'info': f"Titre {titre.tag_name} - conforme"
            })
        
        # Boutons
        boutons = driver.find_elements(By.TAG_NAME, "button")
        for bouton in boutons:
            elements_to_mark.append({
                'element': bouton,
                'type': 'button',
                'issues': [],
                'compliant': True,
                'info': f"Bouton {bouton.get_attribute('id')} - conforme"
            })
        
        # Marquage en lot
        css_marker.mark_elements_batch(elements_to_mark)
        
        logger.info("✅ Marquage en lot terminé")
        
        # Test 3: Informations sur les éléments marqués
        logger.info("🔍 Test 3: Informations sur les éléments marqués")
        marked_info = css_marker.get_marked_elements_info()
        logger.info(f"Nombre d'éléments marqués : {marked_info['total_marked']}")
        logger.info(f"CSS injecté : {marked_info['css_injected']}")
        
        # Test 4: Mode production
        logger.info("🔍 Test 4: Mode production")
        logger.info("Activation du mode production (marquages masqués)")
        css_marker.toggle_production_mode(hide=True)
        
        time.sleep(2)
        
        logger.info("Désactivation du mode production (marquages visibles)")
        css_marker.toggle_production_mode(hide=False)
        
        # Test 5: Suppression des marquages
        logger.info("🔍 Test 5: Suppression des marquages")
        time.sleep(3)  # Laisser le temps de voir les marquages
        
        logger.info("Suppression de tous les marquages")
        css_marker.clear_all_markings()
        
        logger.info("✅ Test CSSMarker basique terminé avec succès")
        
        # Attendre un peu pour voir le résultat
        time.sleep(5)
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test : {str(e)}")
        raise
    finally:
        if driver:
            driver.quit()

def test_css_marker_with_dom_analyzer():
    """Test du CSSMarker intégré avec DOMAnalyzer"""
    logger = setup_logging()
    driver = None
    
    try:
        logger.info("🚀 Démarrage du test CSSMarker avec DOMAnalyzer")
        
        # Configuration du driver
        driver = setup_driver()
        
        # Créer une page de test plus complexe
        test_html = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Test CSS Marker avec DOM Analyzer</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .container { max-width: 1000px; margin: 0 auto; }
                .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
                .card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
                .hidden { display: none; }
                .invisible { visibility: hidden; }
            </style>
        </head>
        <body>
            <div class="container">
                <header role="banner">
                    <h1>Site de test pour l'accessibilité</h1>
                    <nav role="navigation">
                        <ul>
                            <li><a href="#home">Accueil</a></li>
                            <li><a href="#services">Services</a></li>
                            <li><a href="#contact">Contact</a></li>
                        </ul>
                    </nav>
                </header>
                
                <main role="main">
                    <section class="grid">
                        <div class="card">
                            <h2>Section 1</h2>
                            <img src="https://via.placeholder.com/200x100" alt="Image de test 1">
                            <p>Contenu de la section 1</p>
                            <button>Action 1</button>
                        </div>
                        
                        <div class="card">
                            <h2>Section 2</h2>
                            <img src="https://via.placeholder.com/200x100" id="image-sans-alt">
                            <p>Contenu de la section 2</p>
                            <a href="#" id="lien-vide"></a>
                        </div>
                    </section>
                    
                    <section>
                        <h2>Formulaires</h2>
                        <form>
                            <label for="nom">Nom :</label>
                            <input type="text" id="nom" name="nom" required>
                            
                            <label for="email">Email :</label>
                            <input type="email" id="email" name="email" required>
                            
                            <button type="submit">Envoyer</button>
                        </form>
                    </section>
                    
                    <section>
                        <h2>Éléments cachés</h2>
                        <div class="hidden">
                            <p>Contenu caché avec display: none</p>
                        </div>
                        <div class="invisible">
                            <p>Contenu invisible avec visibility: hidden</p>
                        </div>
                    </section>
                </main>
                
                <footer role="contentinfo">
                    <p>&copy; 2024 Test d'accessibilité</p>
                </footer>
            </div>
        </body>
        </html>
        """
        
        # Charger la page de test
        driver.get("data:text/html;charset=utf-8," + test_html)
        
        # Attendre que la page soit chargée
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        logger.info("📄 Page de test complexe chargée avec succès")
        
        # Initialiser le DOMAnalyzer avec marquage CSS activé
        dom_analyzer = DOMAnalyzer(driver, logger, enable_css_marking=True)
        
        # Lancer l'analyse
        logger.info("🔍 Lancement de l'analyse DOM avec marquage CSS")
        result = dom_analyzer.run()
        
        logger.info(f"✅ Analyse terminée : {result['summary']['analyzed_elements']} éléments analysés")
        logger.info(f"📊 Problèmes détectés : {result['summary']['issues_found']}")
        
        # Afficher les informations sur les éléments marqués
        if dom_analyzer.css_marker:
            marked_info = dom_analyzer.css_marker.get_marked_elements_info()
            logger.info(f"🎨 Éléments marqués : {marked_info['total_marked']}")
        
        # Attendre un peu pour voir les marquages
        logger.info("⏳ Attente de 10 secondes pour observer les marquages...")
        time.sleep(10)
        
        # Test du mode production
        logger.info("🔍 Test du mode production")
        if dom_analyzer.css_marker:
            dom_analyzer.css_marker.toggle_production_mode(hide=True)
            logger.info("Mode production activé - marquages masqués")
            time.sleep(3)
            
            dom_analyzer.css_marker.toggle_production_mode(hide=False)
            logger.info("Mode production désactivé - marquages visibles")
            time.sleep(3)
        
        logger.info("✅ Test CSSMarker avec DOMAnalyzer terminé avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test : {str(e)}")
        raise
    finally:
        if driver:
            driver.quit()

def main():
    """Fonction principale de test"""
    print("🧪 Tests du système de marquage CSS pour l'analyse d'accessibilité")
    print("=" * 70)
    
    try:
        # Test 1: CSSMarker basique
        print("\n🔍 Test 1: CSSMarker basique")
        test_css_marker_basic()
        
        print("\n" + "="*50)
        
        # Test 2: CSSMarker avec DOMAnalyzer
        print("\n🔍 Test 2: CSSMarker avec DOMAnalyzer")
        test_css_marker_with_dom_analyzer()
        
        print("\n✅ Tous les tests sont terminés avec succès !")
        print("\n📋 Résumé des fonctionnalités testées :")
        print("   • Marquage individuel d'éléments")
        print("   • Marquage en lot d'éléments")
        print("   • Styles CSS personnalisés par type d'élément")
        print("   • Tooltips informatifs")
        print("   • Mode production (masquage des marquages)")
        print("   • Intégration avec DOMAnalyzer")
        print("   • Gestion des éléments conformes et non conformes")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests : {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
