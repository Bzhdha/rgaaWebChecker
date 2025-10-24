#!/usr/bin/env python3
"""
Démonstration du système de marquage CSS
Script simple pour tester le marquage CSS sur une page web
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

def setup_logging():
    """Configure le système de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def setup_driver():
    """Configure le driver Selenium"""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Erreur Chrome : {e}")
        try:
            chrome_options.binary_location = "/usr/bin/chromium-browser"
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e2:
            print(f"Erreur Chromium : {e2}")
            raise

def create_demo_page():
    """Crée une page de démonstration"""
    return """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Démonstration CSS Marker</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 20px; 
                line-height: 1.6;
            }
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
            }
            .section { 
                margin: 30px 0; 
                padding: 20px; 
                border: 1px solid #ddd; 
                border-radius: 8px;
                background: #f9f9f9;
            }
            .grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                gap: 20px; 
                margin: 20px 0;
            }
            .card { 
                border: 1px solid #ccc; 
                padding: 15px; 
                border-radius: 5px; 
                background: white;
            }
            h1, h2 { color: #333; }
            .demo-button {
                background: #007cba;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                margin: 5px;
            }
            .demo-button:hover {
                background: #005a87;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header role="banner">
                <h1>🎨 Démonstration du système de marquage CSS</h1>
                <p>Cette page démontre les fonctionnalités du système de marquage CSS pour l'analyse d'accessibilité.</p>
            </header>
            
            <main role="main">
                <section class="section">
                    <h2>📸 Section Images</h2>
                    <div class="grid">
                        <div class="card">
                            <h3>Image conforme</h3>
                            <img src="https://via.placeholder.com/200x150/4CAF50/white?text=Image+OK" 
                                 alt="Image de démonstration avec attribut alt" 
                                 id="img-conforme">
                            <p>Cette image a un attribut alt approprié.</p>
                        </div>
                        
                        <div class="card">
                            <h3>Image non conforme</h3>
                            <img src="https://via.placeholder.com/200x150/F44336/white?text=Image+KO" 
                                 id="img-non-conforme">
                            <p>Cette image n'a pas d'attribut alt.</p>
                        </div>
                    </div>
                </section>
                
                <section class="section">
                    <h2>🔗 Section Liens</h2>
                    <div class="grid">
                        <div class="card">
                            <h3>Liens conformes</h3>
                            <a href="https://example.com" id="lien-texte">Lien avec texte visible</a><br>
                            <a href="https://example.com" aria-label="Lien avec aria-label" id="lien-aria">Lien ARIA</a>
                        </div>
                        
                        <div class="card">
                            <h3>Liens non conformes</h3>
                            <a href="https://example.com" id="lien-vide"></a>
                            <p>Lien sans texte visible</p>
                        </div>
                    </div>
                </section>
                
                <section class="section">
                    <h2>🔘 Section Boutons</h2>
                    <div class="grid">
                        <div class="card">
                            <h3>Boutons conformes</h3>
                            <button class="demo-button" id="btn-normal">Bouton normal</button>
                            <button class="demo-button" aria-label="Bouton avec aria-label" id="btn-aria">Bouton ARIA</button>
                        </div>
                        
                        <div class="card">
                            <h3>Boutons avec problèmes</h3>
                            <button class="demo-button" id="btn-disabled" disabled>Bouton désactivé</button>
                        </div>
                    </div>
                </section>
                
                <section class="section">
                    <h2>📝 Section Formulaires</h2>
                    <form id="demo-form">
                        <div class="grid">
                            <div class="card">
                                <h3>Champs conformes</h3>
                                <label for="nom">Nom complet :</label>
                                <input type="text" id="nom" name="nom" required>
                                
                                <label for="email">Email :</label>
                                <input type="email" id="email" name="email" required>
                            </div>
                            
                            <div class="card">
                                <h3>Champs avec problèmes</h3>
                                <input type="text" id="sans-label" placeholder="Champ sans label">
                                
                                <label>Label sans for :</label>
                                <input type="text" id="input-sans-for">
                            </div>
                        </div>
                        
                        <button type="submit" class="demo-button">Envoyer le formulaire</button>
                    </form>
                </section>
                
                <section class="section">
                    <h2>🏗️ Section Landmarks</h2>
                    <div class="grid">
                        <div class="card">
                            <nav role="navigation" id="nav-demo">
                                <h3>Navigation</h3>
                                <ul>
                                    <li><a href="#home">Accueil</a></li>
                                    <li><a href="#about">À propos</a></li>
                                    <li><a href="#contact">Contact</a></li>
                                </ul>
                            </nav>
                        </div>
                        
                        <div class="card">
                            <aside role="complementary" id="aside-demo">
                                <h3>Contenu complémentaire</h3>
                                <p>Informations supplémentaires</p>
                            </aside>
                        </div>
                    </div>
                </section>
                
                <section class="section">
                    <h2>🎭 Section ARIA</h2>
                    <div class="grid">
                        <div class="card">
                            <div role="button" tabindex="0" id="div-button">
                                <h3>Div avec rôle button</h3>
                                <p>Élément div avec rôle ARIA button</p>
                            </div>
                        </div>
                        
                        <div class="card">
                            <div role="alert" id="div-alert">
                                <h3>Zone d'alerte</h3>
                                <p>Contenu d'alerte important</p>
                            </div>
                        </div>
                    </div>
                </section>
            </main>
            
            <footer role="contentinfo">
                <p>&copy; 2024 Démonstration CSS Marker - RGAA Web Checker</p>
            </footer>
        </div>
    </body>
    </html>
    """

def demo_basic_marking():
    """Démonstration du marquage basique"""
    logger = setup_logging()
    driver = None
    
    try:
        logger.info("🚀 Démarrage de la démonstration CSS Marker")
        
        # Configuration
        driver = setup_driver()
        
        # Charger la page de démonstration
        demo_html = create_demo_page()
        driver.get("data:text/html;charset=utf-8," + demo_html)
        
        # Attendre le chargement
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        logger.info("📄 Page de démonstration chargée")
        
        # Initialiser le CSSMarker
        css_marker = CSSMarker(driver, logger)
        
        # Phase 1: Marquage des images
        logger.info("🔍 Phase 1: Marquage des images")
        
        # Image conforme
        img_conforme = driver.find_element(By.ID, "img-conforme")
        css_marker.mark_element(
            element=img_conforme,
            element_type="image",
            issues=[],
            compliant=True,
            info="✅ Image conforme - attribut alt présent"
        )
        
        # Image non conforme
        img_non_conforme = driver.find_element(By.ID, "img-non-conforme")
        css_marker.mark_element(
            element=img_non_conforme,
            element_type="image",
            issues=["Image sans attribut alt"],
            compliant=False,
            info="❌ Image non conforme - attribut alt manquant"
        )
        
        time.sleep(2)
        
        # Phase 2: Marquage des liens
        logger.info("🔍 Phase 2: Marquage des liens")
        
        # Liens conformes
        lien_texte = driver.find_element(By.ID, "lien-texte")
        css_marker.mark_element(
            element=lien_texte,
            element_type="link",
            issues=[],
            compliant=True,
            info="✅ Lien conforme - texte visible"
        )
        
        lien_aria = driver.find_element(By.ID, "lien-aria")
        css_marker.mark_element(
            element=lien_aria,
            element_type="link",
            issues=[],
            compliant=True,
            info="✅ Lien conforme - aria-label présent"
        )
        
        # Lien non conforme
        lien_vide = driver.find_element(By.ID, "lien-vide")
        css_marker.mark_element(
            element=lien_vide,
            element_type="link",
            issues=["Lien sans texte visible"],
            compliant=False,
            info="❌ Lien non conforme - pas de texte visible"
        )
        
        time.sleep(2)
        
        # Phase 3: Marquage des boutons
        logger.info("🔍 Phase 3: Marquage des boutons")
        
        # Boutons conformes
        btn_normal = driver.find_element(By.ID, "btn-normal")
        css_marker.mark_element(
            element=btn_normal,
            element_type="button",
            issues=[],
            compliant=True,
            info="✅ Bouton conforme - texte visible"
        )
        
        btn_aria = driver.find_element(By.ID, "btn-aria")
        css_marker.mark_element(
            element=btn_aria,
            element_type="button",
            issues=[],
            compliant=True,
            info="✅ Bouton conforme - aria-label présent"
        )
        
        # Bouton avec problème
        btn_disabled = driver.find_element(By.ID, "btn-disabled")
        css_marker.mark_element(
            element=btn_disabled,
            element_type="button",
            issues=["Bouton désactivé"],
            compliant=False,
            info="⚠️ Bouton désactivé - non accessible"
        )
        
        time.sleep(2)
        
        # Phase 4: Marquage des landmarks
        logger.info("🔍 Phase 4: Marquage des landmarks")
        
        # Navigation
        nav = driver.find_element(By.ID, "nav-demo")
        css_marker.mark_element(
            element=nav,
            element_type="landmark",
            issues=[],
            compliant=True,
            info="✅ Navigation landmark - conforme"
        )
        
        # Aside
        aside = driver.find_element(By.ID, "aside-demo")
        css_marker.mark_element(
            element=aside,
            element_type="landmark",
            issues=[],
            compliant=True,
            info="✅ Aside landmark - conforme"
        )
        
        time.sleep(2)
        
        # Phase 5: Marquage des éléments ARIA
        logger.info("🔍 Phase 5: Marquage des éléments ARIA")
        
        # Div avec rôle button
        div_button = driver.find_element(By.ID, "div-button")
        css_marker.mark_element(
            element=div_button,
            element_type="aria",
            issues=[],
            compliant=True,
            info="✅ Élément ARIA - rôle button conforme"
        )
        
        # Div avec rôle alert
        div_alert = driver.find_element(By.ID, "div-alert")
        css_marker.mark_element(
            element=div_alert,
            element_type="aria",
            issues=[],
            compliant=True,
            info="✅ Élément ARIA - rôle alert conforme"
        )
        
        time.sleep(2)
        
        # Phase 6: Démonstration du mode production
        logger.info("🔍 Phase 6: Démonstration du mode production")
        
        logger.info("Activation du mode production (marquages masqués)")
        css_marker.toggle_production_mode(hide=True)
        time.sleep(3)
        
        logger.info("Désactivation du mode production (marquages visibles)")
        css_marker.toggle_production_mode(hide=False)
        time.sleep(3)
        
        # Phase 7: Informations sur les éléments marqués
        logger.info("🔍 Phase 7: Informations sur les éléments marqués")
        marked_info = css_marker.get_marked_elements_info()
        logger.info(f"Nombre d'éléments marqués : {marked_info['total_marked']}")
        logger.info(f"CSS injecté : {marked_info['css_injected']}")
        
        # Afficher les détails
        for i, element_info in enumerate(marked_info['elements'], 1):
            logger.info(f"  {i}. {element_info['element_id']} - {element_info['element_type']} - Conforme: {element_info['compliant']}")
        
        # Phase 8: Attente pour observation
        logger.info("⏳ Phase 8: Observation des marquages (10 secondes)")
        logger.info("Vous pouvez maintenant observer les marquages CSS sur la page")
        logger.info("- Éléments conformes : bordure verte avec badge ✅")
        logger.info("- Éléments non conformes : bordure rouge avec badge ⚠️")
        logger.info("- Survol des éléments pour voir les tooltips informatifs")
        
        time.sleep(10)
        
        # Phase 9: Nettoyage
        logger.info("🔍 Phase 9: Nettoyage des marquages")
        css_marker.clear_all_markings()
        logger.info("Tous les marquages ont été supprimés")
        
        time.sleep(2)
        
        logger.info("✅ Démonstration terminée avec succès !")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la démonstration : {str(e)}")
        raise
    finally:
        if driver:
            driver.quit()

def main():
    """Fonction principale"""
    print("🎨 Démonstration du système de marquage CSS")
    print("=" * 50)
    print("Cette démonstration montre comment le système de marquage CSS")
    print("permet d'identifier visuellement les éléments analysés et leurs")
    print("problèmes d'accessibilité.")
    print()
    print("Fonctionnalités démontrées :")
    print("• Marquage des différents types d'éléments")
    print("• Indication visuelle de la conformité")
    print("• Tooltips informatifs au survol")
    print("• Mode production (masquage des marquages)")
    print("• Gestion des éléments conformes et non conformes")
    print()
    
    try:
        demo_basic_marking()
        print("\n✅ Démonstration terminée avec succès !")
        print("\n📋 Résumé :")
        print("   • Système de marquage CSS fonctionnel")
        print("   • Styles visuels clairs et informatifs")
        print("   • Intégration facile avec les modules d'analyse")
        print("   • Mode production pour masquer les marquages")
        print("   • Tooltips détaillés pour le débogage")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la démonstration : {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
