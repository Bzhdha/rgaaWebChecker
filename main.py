from core.config import Config
from core.crawler import AccessibilityCrawler
from utils.log_utils import setup_logger
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import glob
import sys
import time
import argparse
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from modules.dom_analyzer import DOMAnalyzer
from modules.image_analyzer import ImageAnalyzer

def parse_module_flags(module_list):
    """
    Convertit une liste de noms de modules en valeur binaire
    """
    if not module_list:
        return 0
    
    config = Config()
    module_names = config.get_module_names()
    total = 0
    
    for module in module_list:
        if module in module_names:
            total |= module_names[module]
    
    return total

if __name__ == "__main__":
    # Forcer l'encodage UTF-8 pour stdout et stderr
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Analyseur d'accessibilité web")
    parser.add_argument('url', help='URL de la page à analyser')
    parser.add_argument('--debug', action='store_true', help='Afficher les logs sur la console')
    parser.add_argument('--encoding', choices=['cp1252', 'utf-8'], default='utf-8', help="Encodage du rapport (utf-8 par défaut, ou cp1252)")
    parser.add_argument('--cookie-banner', help='Texte du bouton de la bannière de cookies à cliquer (ex: "Accepter tout")')
    parser.add_argument('--modules', nargs='+', choices=['contrast', 'dom', 'daltonism', 'tab', 'screen', 'image'], 
                      help='Liste des modules à activer (contrast=1, dom=2, daltonism=4, tab=8, screen=16, image=32)')
    parser.add_argument('--output-dir', default='site_images', help='Répertoire de sortie pour les images (défaut: site_images)')
    args = parser.parse_args()
    
    url = args.url
    logger = setup_logger(debug=args.debug, encoding=args.encoding)
    config = Config()
    config.set_base_url(url)
    config.set_output_dir(args.output_dir)
    
    # Configuration des modules
    if args.modules:
        module_flags = parse_module_flags(args.modules)
        config.set_modules(module_flags)
    else:
        # Par défaut, activer tous les modules
        config.set_modules(63)  # 1 + 2 + 4 + 8 + 16 + 32
    
    chrome_options = Options()
    # Ajout des en-têtes pour simuler un navigateur réel
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Masquer l'automatisation
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Ajouter des préférences pour simuler un navigateur normal
    chrome_options.add_experimental_option('prefs', {
        'profile.default_content_setting_values.notifications': 2,
        'credentials_enable_service': False,
        'profile.password_manager_enabled': False,
        'profile.default_content_settings.popups': 0,
        'profile.managed_default_content_settings.images': 1,
        'profile.default_content_setting_values.cookies': 1
    })
    
    driver_dir = os.path.dirname(ChromeDriverManager().install())
    chromedriver_path = None
    for f in glob.glob(os.path.join(driver_dir, "chromedriver*")):
        if os.access(f, os.X_OK) and not f.endswith('.txt') and not f.endswith('.chromedriver'):
            chromedriver_path = f
            break
    if not chromedriver_path:
        raise FileNotFoundError("Aucun binaire chromedriver exécutable trouvé dans " + driver_dir)
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    logger.info("Driver initialisé avec succès.")
    
    try:
        driver.get(url)
        # Attendre que la page soit chargée
        time.sleep(5)
        
        # Analyser le focus initial sans l'afficher
        focused_element = driver.switch_to.active_element

        if args.cookie_banner:
            try:
                # Vérifie si l'élément focus contient un bouton avec le texte voulu
                buttons_in_focus = focused_element.find_elements("tag name", "button")
                for btn in buttons_in_focus:
                    if args.cookie_banner.lower() in btn.text.lower():
                        logger.info(f"Bouton '{args.cookie_banner}' trouvé via élément focus.")
                        btn.click()
                        time.sleep(2)
                        driver.refresh()  # recharge la page après clic
                        WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
                        logger.info("Page rechargée après clic sur le bouton cookie.")
                        break
            except Exception as e:
                logger.warning(f"Erreur lors de l'analyse des boutons dans l'élément focus: {e}")
            
        # Vérifier si le mode debug est activé
        # if not args.debug:
        #     logger.info("Pour voir les détails du focus, relancez avec l'option --debug")
        # else:
            # En mode debug, afficher le contenu de la bannière de cookies chaque seconde pendant 10 secondes
            #logger.info("Affichage du contenu de la bannière de cookies pendant 10 secondes...")
            
            # Attendre que la bannière de cookies soit chargée
            # try:
            #     WebDriverWait(driver, 10).until(
            #         lambda d: len(d.find_elements("xpath", "//div[@id='usercentrics-root']//button")) > 0
            #     )
            #     logger.info("Bannière de cookies chargée avec succès")
            # except Exception as e:
            #    logger.warning(f"La bannière de cookies n'a pas été chargée : {str(e)}")
            
            # for i in range(10):
            #     try:
            #         # Récupérer la bannière de cookies
            #         cookie_banner = driver.find_element("id", "usercentrics-root")
            #         logger.info(f"\nSeconde {i+1} - Contenu de la bannière de cookies:")
            #         logger.info("=" * 50)
                    
            #         # Récupérer tous les boutons
            #         buttons = driver.find_elements("xpath", "//div[@id='usercentrics-root']//button")
            #         logger.info(f"Nombre de boutons trouvés : {len(buttons)}")
                    
            #         # Afficher les détails de chaque bouton
            #         for j, button in enumerate(buttons, 1):
            #             logger.info(f"\nBouton {j}:")
            #             logger.info(f"HTML: {button.get_attribute('outerHTML')}")
            #             logger.info(f"Texte: {button.text}")
            #             logger.info(f"Classes: {button.get_attribute('class')}")
            #             logger.info(f"ID: {button.get_attribute('id')}")
                    
            #         # Afficher le contenu complet de la bannière
            #         logger.info("\nContenu complet de la bannière:")
            #         logger.info(cookie_banner.get_attribute('innerHTML'))
            #         logger.info("=" * 50)
                    
            #         # Afficher aussi l'élément focusé
            #         focused = driver.switch_to.active_element
            #         logger.info(f"\nÉlément focusé à la seconde {i+1}:")
            #         logger.info(focused.get_attribute('outerHTML'))
            #     except Exception as e:
            #         logger.warning(f"Erreur à la seconde {i+1}: {str(e)}")
            #     time.sleep(1)

        
        # Traiter la bannière de cookies seulement si un texte est spécifié
        if args.cookie_banner:
            try:
                # Chercher le bouton avec le texte spécifié dans le texte visible ou les attributs d'accessibilité
                button_xpath = f"""
                    //button[
                        contains(text(), '{args.cookie_banner}') or
                        contains(@aria-label, '{args.cookie_banner}') or
                        contains(@title, '{args.cookie_banner}')
                    ]
                """
                continue_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(("xpath", button_xpath))
                )
                logger.info(f"Bouton '{args.cookie_banner}' trouvé: {continue_button.get_attribute('outerHTML')}")
                
                if not continue_button.is_enabled():
                    logger.warning("Le bouton n'est pas interactif")
                    raise Exception("Le bouton n'est pas interactif")
                
                continue_button.click()
                logger.info(f"Clic sur le bouton '{args.cookie_banner}'.")

                time.sleep(2)
                driver.refresh()
                WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
                logger.info("Page rechargée après le clic sur le bouton cookie.")

                
                # Attendre la disparition de la popin
                try:
                    WebDriverWait(driver, 10).until(
                        EC.invisibility_of_element_located(("id", "popin_tc_privacy"))
                    )
                    logger.info("Popup de cookies disparue.")
                    
                    # Vérifier que la popin est vraiment disparue
                    popin_elements = driver.find_elements("id", "popin_tc_privacy")
                    if not popin_elements or not popin_elements[0].is_displayed():
                        logger.info("Vérification : la popin est bien invisible")
                        
                        # Simuler des tabulations
                        actions = ActionChains(driver)
                        actions.send_keys(Keys.TAB).perform()  # Tabulation avant
                        logger.info("Tabulation avant effectuée")
                        time.sleep(1)
                        actions.send_keys(Keys.SHIFT + Keys.TAB).perform()  # Tabulation arrière
                        logger.info("Tabulation arrière effectuée")
                        
                        # Vérifier où se trouve le focus
                        focused_after_popup = driver.switch_to.active_element
                        logger.info(f"Focus après tabulations: {focused_after_popup.get_attribute('outerHTML')}")
                        
                        # Attendre un délai aléatoire
                        wait_time = random.uniform(2, 4)
                        logger.info(f"Attente de {wait_time:.1f} secondes...")
                        time.sleep(wait_time)
                        
                        # Vérifier une dernière fois que la popin n'est pas revenue
                        popin_elements = driver.find_elements("id", "popin_tc_privacy")
                        if not popin_elements or not popin_elements[0].is_displayed():
                            logger.info("Vérification finale : la popin est toujours invisible")
                            
                            # Attendre que la page soit complètement chargée
                            WebDriverWait(driver, 10).until(
                                lambda d: d.execute_script('return document.readyState') == 'complete'
                            )
                            logger.info("Page complètement chargée")
                            
                            # Vérifier que les éléments principaux sont présents et stables
                            try:
                                WebDriverWait(driver, 10).until(
                                    lambda d: len(d.find_elements("tag name", "body")) > 0 and
                                            len(d.find_elements("tag name", "main")) > 0
                                )
                                logger.info("Éléments principaux de la page chargés")
                                
                                # Attendre que le DOM soit stable
                                time.sleep(2)
                                logger.info("DOM stable, prêt pour l'analyse")
                                
                            except Exception as e:
                                logger.error(f"Erreur lors de la vérification de la page : {str(e)}")
                                raise
                        else:
                            logger.error("La popin est toujours visible malgré l'attente")
                            raise Exception("La popin est toujours visible")
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la gestion de la popin : {str(e)}")
                    raise
            except Exception as e:
                logger.warning(f"Bouton '{args.cookie_banner}' non trouvé : {e}")
        
        # Forcer l'encodage UTF-8 pour le contenu de la page
        driver.execute_script("""
            document.characterSet = 'UTF-8';
            document.charset = 'UTF-8';
        """)
        
        # Vérifier si l'accès est bloqué
        if "Accès non autorisé" in driver.page_source or "Access denied" in driver.page_source:
            logger.error("Accès au site bloqué. Le site détecte l'automatisation.")
            driver.quit()
            sys.exit(1)
            
        logger.info(f"Page visitée: {url}")
        crawler = AccessibilityCrawler(config)
        crawler.set_driver(driver)
        logger.info("Driver assigné au crawler.")
        crawler.logger = logger
        crawler.crawl()
        crawler.generate_report()

        # Initialiser l'analyseur DOM
        dom_analyzer = DOMAnalyzer(driver, logger)
        dom_results = dom_analyzer.run()
        
        # Si l'analyse des images est activée
        if 'image' in args.modules:
            image_analyzer = ImageAnalyzer(driver, logger, args.url, args.output_dir)
            image_results = image_analyzer.run()
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {str(e)}")
    finally:
        driver.quit()
