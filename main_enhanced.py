# Version améliorée de main.py avec intégration des données ARIA
from core.config import Config
from core.enhanced_crawler import EnhancedAccessibilityCrawler
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

    parser = argparse.ArgumentParser(description="Analyseur d'accessibilité web avec intégration ARIA")
    parser.add_argument('url', help='URL de la page à analyser')
    parser.add_argument('--debug', action='store_true', help='Afficher les logs sur la console')
    parser.add_argument('--encoding', choices=['cp1252', 'utf-8'], default='utf-8', help="Encodage du rapport (utf-8 par défaut, ou cp1252)")
    parser.add_argument('--cookie-banner', help='Texte du bouton de la bannière de cookies à cliquer (ex: "Accepter tout")')
    parser.add_argument('--cookies', nargs='*', help='Cookies de consentement à définir au format "nom=valeur" (ex: "consent=accepted" "analytics=true")')
    parser.add_argument('--modules', nargs='+', choices=['contrast', 'dom', 'daltonism', 'tab', 'screen', 'image', 'navigation'], 
                      help='Liste des modules à activer (contrast=1, dom=2, daltonism=4, tab=8, screen=16, image=32, navigation=64)')
    parser.add_argument('--output-dir', default='site_images', help='Répertoire de sortie pour les images (défaut: site_images)')
    parser.add_argument('--max-screenshots', type=int, default=50, help='Limite maximale de screenshots pour la navigation au clavier (défaut: 50)')
    parser.add_argument('--export-csv', action='store_true', help='Exporter les données collectées en CSV')
    parser.add_argument('--csv-filename', help='Nom du fichier CSV pour l\'export (optionnel)')
    args = parser.parse_args()
    
    url = args.url
    logger = setup_logger(debug=args.debug, encoding=args.encoding)
    config = Config()
    config.set_base_url(url)
    config.set_output_dir(args.output_dir)
    config.set_max_screenshots(args.max_screenshots)
    
    # Configuration des modules
    if args.modules:
        module_flags = parse_module_flags(args.modules)
        config.set_modules(module_flags)
    else:
        # Par défaut, activer tous les modules
        config.set_modules(127)  # 1 + 2 + 4 + 8 + 16 + 32 + 64
    
    chrome_options = Options()
    # Ajout des en-têtes pour simuler un navigateur réel
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--window-position=0,0')  # Forcer la position de la fenêtre sur l'écran principal
    chrome_options.add_argument('--force-device-scale-factor=1')  # Éviter les problèmes de zoom
    
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
        # Définir les cookies de consentement avant la navigation si spécifiés
        if args.cookies:
            logger.info("Définition des cookies de consentement...")
            # Aller d'abord sur le domaine pour pouvoir définir les cookies
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            driver.get(domain_url)
            
            # Définir chaque cookie
            for cookie_str in args.cookies:
                if '=' in cookie_str:
                    cookie_name, cookie_value = cookie_str.split('=', 1)
                    try:
                        # Définir le cookie pour le domaine
                        driver.add_cookie({
                            'name': cookie_name.strip(),
                            'value': cookie_value.strip(),
                            'domain': parsed_url.netloc
                        })
                        logger.info(f"Cookie défini: {cookie_name.strip()} = {cookie_value.strip()}")
                    except Exception as e:
                        logger.warning(f"Impossible de définir le cookie {cookie_name}: {e}")
                else:
                    logger.warning(f"Format de cookie invalide: {cookie_str} (attendu: nom=valeur)")
            
            logger.info("Cookies de consentement définis avec succès")
        
        # Maintenant naviguer vers l'URL cible
        driver.get(url)
        
        # Forcer la fenêtre à rester sur l'écran principal
        try:
            driver.set_window_position(0, 0)
            driver.set_window_size(1920, 1080)
            logger.info("Position de la fenêtre forcée sur l'écran principal")
        except Exception as e:
            logger.warning(f"Impossible de forcer la position de la fenêtre: {e}")
        
        # Attendre que la page soit chargée
        time.sleep(10)
        
        # Analyser le focus initial sans l'afficher
        focused_element = driver.switch_to.active_element

        if args.cookie_banner:
            try:
                # Vérifie si l'élément focus contient un bouton avec le texte voulu
                buttons_in_focus = focused_element.find_elements("tag name", "button")
                for btn in buttons_in_focus:
                    if args.cookie_banner.lower() in btn.text.lower():
                        logger.info(f"Bouton '{args.cookie_banner}' trouvé via élément focus.")
                        # Attendre un délai pour s'assurer que le bouton est bien interactif
                        time.sleep(1)
                        btn.click()
                        time.sleep(2)
                        driver.refresh()  # recharge la page après clic
                        WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
                        logger.info("Page rechargée après clic sur le bouton cookie.")
                        break
            except Exception as e:
                logger.warning(f"Erreur lors de l'analyse des boutons dans l'élément focus: {e}")
        
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
        
        # Utiliser le crawler amélioré avec intégration ARIA
        crawler = EnhancedAccessibilityCrawler(config)
        crawler.set_driver(driver)
        logger.info("Driver assigné au crawler amélioré.")
        crawler.logger = logger
        crawler.crawl()
        crawler.generate_report(export_csv=args.export_csv, csv_filename=args.csv_filename)
        
        # Récupérer les données partagées pour affichage
        shared_data = crawler.get_shared_data()
        logger.info(f"Données ARIA partagées: {len(shared_data.aria_data)} éléments")
        
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
