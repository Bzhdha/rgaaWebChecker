from core.config import Config
from core.crawler import AccessibilityCrawler
from utils.log_utils import setup_logger, log_with_step
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
import subprocess
import logging

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
    parser.add_argument('--browser', choices=['chrome', 'chromium', 'auto'], default='auto', 
                      help='Navigateur à utiliser (chrome, chromium, ou auto pour détection automatique)')
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
    
    # Vérifier si Chrome est installé
    chrome_installed = False
    chromium_installed = False
    chrome_paths = [
        'google-chrome',
        'google-chrome-stable',
        'google-chrome-beta',
        'google-chrome-dev',
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable'
    ]
    
    chromium_paths = [
        'chromium-browser',
        'chromium',
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium'
    ]
    
    # Vérifier Chrome
    for chrome_path in chrome_paths:
        try:
            result = subprocess.run([chrome_path, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                chrome_installed = True
                log_with_step(logger, logging.INFO, "NAVIGATEUR", f"Chrome trouvé: {result.stdout.strip()}")
                break
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            continue
    
    # Vérifier Chromium
    for chromium_path in chromium_paths:
        try:
            result = subprocess.run([chromium_path, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                chromium_installed = True
                log_with_step(logger, logging.INFO, "NAVIGATEUR", f"Chromium trouvé: {result.stdout.strip()}")
                break
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            continue
    
    # Déterminer quel navigateur utiliser selon l'option --browser
    use_chrome = False
    use_chromium = False
    
    if args.browser == 'chrome':
        if chrome_installed:
            use_chrome = True
            log_with_step(logger, logging.INFO, "NAVIGATEUR", "Utilisation de Chrome (choix explicite)")
        else:
            log_with_step(logger, logging.ERROR, "NAVIGATEUR", "Chrome demandé mais non installé")
            log_with_step(logger, logging.ERROR, "NAVIGATEUR", "Installer Chrome : chmod +x install_chrome.sh && ./install_chrome.sh")
            sys.exit(1)
    elif args.browser == 'chromium':
        if chromium_installed:
            use_chromium = True
            log_with_step(logger, logging.INFO, "NAVIGATEUR", "Utilisation de Chromium (choix explicite)")
        else:
            log_with_step(logger, logging.ERROR, "NAVIGATEUR", "Chromium demandé mais non installé")
            log_with_step(logger, logging.ERROR, "NAVIGATEUR", "Installer Chromium : chmod +x install_chromium.sh && ./install_chromium.sh")
            sys.exit(1)
    else:  # auto
        # Priorité : Chrome puis Chromium
        if chrome_installed:
            use_chrome = True
            log_with_step(logger, logging.INFO, "NAVIGATEUR", "Utilisation de Chrome (détection automatique)")
        elif chromium_installed:
            use_chromium = True
            log_with_step(logger, logging.INFO, "NAVIGATEUR", "Utilisation de Chromium (détection automatique)")
    
    if not use_chrome and not use_chromium:
        log_with_step(logger, logging.ERROR, "NAVIGATEUR", "Aucun navigateur compatible (Chrome ou Chromium) n'est installé sur ce système.")
        log_with_step(logger, logging.ERROR, "NAVIGATEUR", "Solutions :")
        log_with_step(logger, logging.ERROR, "NAVIGATEUR", "1. Installer Chrome : chmod +x install_chrome.sh && ./install_chrome.sh")
        log_with_step(logger, logging.ERROR, "NAVIGATEUR", "2. Installer Chromium : chmod +x install_chromium.sh && ./install_chromium.sh")
        log_with_step(logger, logging.ERROR, "NAVIGATEUR", "3. Utiliser Firefox : sudo apt install firefox")
        log_with_step(logger, logging.ERROR, "NAVIGATEUR", "4. Utiliser le mode headless avec un navigateur portable")
        
        # Proposer d'installer un navigateur automatiquement
        try:
            print("\nQuel navigateur voulez-vous installer ?")
            print("1. Chrome (recommandé)")
            print("2. Chromium (plus léger)")
            print("3. Aucun (quitter)")
            
            response = input("Votre choix (1-3): ").strip()
            
            if response == "1":
                log_with_step(logger, logging.INFO, "INSTALLATION", "Installation automatique de Chrome...")
                install_script = "./install_chrome.sh"
                if os.path.exists(install_script):
                    subprocess.run(["chmod", "+x", install_script])
                    result = subprocess.run([install_script], check=True)
                    if result.returncode == 0:
                        log_with_step(logger, logging.INFO, "INSTALLATION", "Chrome installé avec succès, redémarrage du script...")
                        # Redémarrer le script
                        os.execv(sys.executable, ['python'] + sys.argv)
                    else:
                        log_with_step(logger, logging.ERROR, "INSTALLATION", "Échec de l'installation automatique de Chrome")
                        sys.exit(1)
                else:
                    log_with_step(logger, logging.ERROR, "INSTALLATION", "Script d'installation Chrome non trouvé")
                    sys.exit(1)
            elif response == "2":
                log_with_step(logger, logging.INFO, "INSTALLATION", "Installation automatique de Chromium...")
                install_script = "./install_chromium.sh"
                if os.path.exists(install_script):
                    subprocess.run(["chmod", "+x", install_script])
                    result = subprocess.run([install_script], check=True)
                    if result.returncode == 0:
                        log_with_step(logger, logging.INFO, "INSTALLATION", "Chromium installé avec succès, redémarrage du script...")
                        # Redémarrer le script
                        os.execv(sys.executable, ['python'] + sys.argv)
                    else:
                        log_with_step(logger, logging.ERROR, "INSTALLATION", "Échec de l'installation automatique de Chromium")
                        sys.exit(1)
                else:
                    log_with_step(logger, logging.ERROR, "INSTALLATION", "Script d'installation Chromium non trouvé")
                    sys.exit(1)
            else:
                log_with_step(logger, logging.ERROR, "INSTALLATION", "Aucun navigateur sélectionné, arrêt du script")
                sys.exit(1)
        except KeyboardInterrupt:
            log_with_step(logger, logging.ERROR, "INSTALLATION", "Installation annulée par l'utilisateur")
            sys.exit(1)
    
    # Configuration pour WSL (mode headless si nécessaire)
    if os.path.exists('/proc/version') and 'microsoft' in open('/proc/version').read().lower():
        log_with_step(logger, logging.INFO, "WSL", "WSL détecté, configuration pour mode headless")
        chrome_options.add_argument('--headless=new')  # Nouvelle version headless
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        # Options spécifiques pour éviter l'erreur DevToolsActivePort
        chrome_options.add_argument('--remote-debugging-port=0')  # Port 0 = port aléatoire
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-setuid-sandbox')
        chrome_options.add_argument('--silent')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # Options supplémentaires pour WSL
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--disable-translate')
    
    try:
        # Essayer d'abord Chrome, puis Chromium
        if use_chrome:
            log_with_step(logger, logging.INFO, "DRIVER", "Utilisation de Chrome")
            driver_dir = os.path.dirname(ChromeDriverManager().install())
        elif use_chromium:
            log_with_step(logger, logging.INFO, "DRIVER", "Utilisation de Chromium")
            # Pour Chromium, forcer une version compatible
            try:
                # Essayer d'abord de télécharger une version compatible
                driver_dir = os.path.dirname(ChromeDriverManager(version="137.0.7151.119").install())
                log_with_step(logger, logging.INFO, "DRIVER", "ChromeDriver version 137 téléchargé pour Chromium")
            except Exception as e:
                log_with_step(logger, logging.WARNING, "DRIVER", f"Impossible de télécharger la version spécifique: {e}")
                # Fallback vers la version automatique
                driver_dir = os.path.dirname(ChromeDriverManager().install())
                log_with_step(logger, logging.INFO, "DRIVER", "Utilisation de la version automatique du ChromeDriver")
        else:
            raise Exception("Aucun navigateur compatible trouvé")
        
        chromedriver_path = None
        for f in glob.glob(os.path.join(driver_dir, "chromedriver*")):
            if not f.endswith('.txt') and not f.endswith('.chromedriver') and not 'THIRD_PARTY' in f:
                chromedriver_path = f
                break
        
        if not chromedriver_path:
            raise FileNotFoundError("Aucun binaire chromedriver trouvé dans " + driver_dir)
        
        # Rendre le ChromeDriver exécutable
        log_with_step(logger, logging.INFO, "DRIVER", f"ChromeDriver trouvé: {chromedriver_path}")
        try:
            # Vérifier si le fichier est déjà exécutable
            if not os.access(chromedriver_path, os.X_OK):
                log_with_step(logger, logging.INFO, "DRIVER", "Rendre le ChromeDriver exécutable...")
                os.chmod(chromedriver_path, 0o755)
                log_with_step(logger, logging.INFO, "DRIVER", "Permissions du ChromeDriver mises à jour")
            else:
                log_with_step(logger, logging.INFO, "DRIVER", "ChromeDriver déjà exécutable")
        except Exception as e:
            log_with_step(logger, logging.WARNING, "DRIVER", f"Impossible de modifier les permissions du ChromeDriver: {e}")
            # Essayer de continuer quand même
        
        # Vérifier que le ChromeDriver est maintenant exécutable
        if not os.access(chromedriver_path, os.X_OK):
            raise FileNotFoundError(f"ChromeDriver non exécutable: {chromedriver_path}")
        
        service = Service(chromedriver_path)
        
        # Utiliser Chrome ou Chromium selon ce qui est disponible
        if use_chrome:
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # Pour Chromium, spécifier le binaire et ajouter des options supplémentaires
            # Chercher le bon chemin de Chromium
            chromium_binary = None
            chromium_paths = [
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/snap/bin/chromium",
                "/usr/bin/google-chrome-stable"
            ]
            
            for path in chromium_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    chromium_binary = path
                    log_with_step(logger, logging.INFO, "DRIVER", f"Binaire Chromium trouvé: {chromium_binary}")
                    break
            
            if chromium_binary:
                chrome_options.binary_location = chromium_binary
                # Options supplémentaires pour Chromium
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-setuid-sandbox')
                chrome_options.add_argument('--disable-web-security')
                chrome_options.add_argument('--allow-running-insecure-content')
                chrome_options.add_argument('--disable-features=VizDisplayCompositor')
                chrome_options.add_argument('--disable-background-timer-throttling')
                chrome_options.add_argument('--disable-backgrounding-occluded-windows')
                chrome_options.add_argument('--disable-renderer-backgrounding')
                chrome_options.add_argument('--disable-features=TranslateUI')
                chrome_options.add_argument('--disable-ipc-flooding-protection')
                
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                raise Exception("Binaire Chromium non trouvé")
        
        log_with_step(logger, logging.INFO, "DRIVER", "Driver initialisé avec succès.")
    except Exception as e:
        log_with_step(logger, logging.ERROR, "DRIVER", f"Erreur lors de l'initialisation du driver: {e}")
        log_with_step(logger, logging.ERROR, "DRIVER", "Solutions alternatives :")
        log_with_step(logger, logging.ERROR, "DRIVER", "1. Vérifier que Chrome/Chromium est installé")
        log_with_step(logger, logging.ERROR, "DRIVER", "2. Réinstaller Chrome : ./install_chrome.sh")
        log_with_step(logger, logging.ERROR, "DRIVER", "3. Réinstaller Chromium : ./install_chromium.sh")
        log_with_step(logger, logging.ERROR, "DRIVER", "4. Utiliser un autre navigateur (Firefox)")
        log_with_step(logger, logging.ERROR, "DRIVER", "5. Nettoyer le cache webdriver-manager : rm -rf ~/.wdm")
        sys.exit(1)
    
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
                        log_with_step(logger, logging.INFO, "DRIVER", f"Bouton '{args.cookie_banner}' trouvé via élément focus.")
                        btn.click()
                        time.sleep(2)
                        driver.refresh()  # recharge la page après clic
                        WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
                        log_with_step(logger, logging.INFO, "DRIVER", "Page rechargée après clic sur le bouton cookie.")
                        break
            except Exception as e:
                log_with_step(logger, logging.WARNING, "DRIVER", f"Erreur lors de l'analyse des boutons dans l'élément focus: {e}")
            
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
                log_with_step(logger, logging.INFO, "DRIVER", f"Bouton '{args.cookie_banner}' trouvé: {continue_button.get_attribute('outerHTML')}")
                
                if not continue_button.is_enabled():
                    log_with_step(logger, logging.WARNING, "DRIVER", "Le bouton n'est pas interactif")
                    raise Exception("Le bouton n'est pas interactif")
                
                continue_button.click()
                log_with_step(logger, logging.INFO, "DRIVER", f"Clic sur le bouton '{args.cookie_banner}'.")

                time.sleep(2)
                driver.refresh()
                WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
                log_with_step(logger, logging.INFO, "DRIVER", "Page rechargée après le clic sur le bouton cookie.")

                
                # Attendre la disparition de la popin
                try:
                    WebDriverWait(driver, 10).until(
                        EC.invisibility_of_element_located(("id", "popin_tc_privacy"))
                    )
                    log_with_step(logger, logging.INFO, "DRIVER", "Popup de cookies disparue.")
                    
                    # Vérifier que la popin est vraiment disparue
                    popin_elements = driver.find_elements("id", "popin_tc_privacy")
                    if not popin_elements or not popin_elements[0].is_displayed():
                        log_with_step(logger, logging.INFO, "DRIVER", "Vérification : la popin est bien invisible")
                        
                        # Simuler des tabulations
                        actions = ActionChains(driver)
                        actions.send_keys(Keys.TAB).perform()  # Tabulation avant
                        log_with_step(logger, logging.INFO, "DRIVER", "Tabulation avant effectuée")
                        time.sleep(1)
                        actions.send_keys(Keys.SHIFT + Keys.TAB).perform()  # Tabulation arrière
                        log_with_step(logger, logging.INFO, "DRIVER", "Tabulation arrière effectuée")
                        
                        # Vérifier où se trouve le focus
                        focused_after_popup = driver.switch_to.active_element
                        log_with_step(logger, logging.INFO, "DRIVER", f"Focus après tabulations: {focused_after_popup.get_attribute('outerHTML')}")
                        
                        # Attendre un délai aléatoire
                        wait_time = random.uniform(2, 4)
                        log_with_step(logger, logging.INFO, "DRIVER", f"Attente de {wait_time:.1f} secondes...")
                        time.sleep(wait_time)
                        
                        # Vérifier une dernière fois que la popin n'est pas revenue
                        popin_elements = driver.find_elements("id", "popin_tc_privacy")
                        if not popin_elements or not popin_elements[0].is_displayed():
                            log_with_step(logger, logging.INFO, "DRIVER", "Vérification finale : la popin est toujours invisible")
                            
                            # Attendre que la page soit complètement chargée
                            WebDriverWait(driver, 10).until(
                                lambda d: d.execute_script('return document.readyState') == 'complete'
                            )
                            log_with_step(logger, logging.INFO, "DRIVER", "Page complètement chargée")
                            
                            # Vérifier que les éléments principaux sont présents et stables
                            try:
                                WebDriverWait(driver, 10).until(
                                    lambda d: len(d.find_elements("tag name", "body")) > 0 and
                                            len(d.find_elements("tag name", "main")) > 0
                                )
                                log_with_step(logger, logging.INFO, "DRIVER", "Éléments principaux de la page chargés")
                                
                                # Attendre que le DOM soit stable
                                time.sleep(2)
                                log_with_step(logger, logging.INFO, "DRIVER", "DOM stable, prêt pour l'analyse")
                                
                            except Exception as e:
                                log_with_step(logger, logging.ERROR, "DRIVER", f"Erreur lors de la vérification de la page : {str(e)}")
                                raise
                        else:
                            log_with_step(logger, logging.ERROR, "DRIVER", "La popin est toujours visible malgré l'attente")
                            raise Exception("La popin est toujours visible")
                    
                except Exception as e:
                    log_with_step(logger, logging.ERROR, "DRIVER", f"Erreur lors de la gestion de la popin : {str(e)}")
                    raise
            except Exception as e:
                log_with_step(logger, logging.WARNING, "DRIVER", f"Bouton '{args.cookie_banner}' non trouvé : {e}")
        
        # Forcer l'encodage UTF-8 pour le contenu de la page
        driver.execute_script("""
            document.characterSet = 'UTF-8';
            document.charset = 'UTF-8';
        """)
        
        # Vérifier si l'accès est bloqué
        if "Accès non autorisé" in driver.page_source or "Access denied" in driver.page_source:
            log_with_step(logger, logging.ERROR, "DRIVER", "Accès au site bloqué. Le site détecte l'automatisation.")
            driver.quit()
            sys.exit(1)
            
        log_with_step(logger, logging.INFO, "DRIVER", f"Page visitée: {url}")
        crawler = AccessibilityCrawler(config, logger)
        crawler.set_driver(driver)
        log_with_step(logger, logging.INFO, "DRIVER", "Driver assigné au crawler.")
        crawler.crawl()
        crawler.generate_report()

        # Initialiser l'analyseur DOM
        dom_analyzer = DOMAnalyzer(driver, logger)
        dom_results = dom_analyzer.run()
        
        # Vérifier que les résultats DOM ne sont pas None
        if dom_results is None:
            dom_results = []
            log_with_step(logger, logging.WARNING, "DRIVER", "Aucun résultat d'analyse DOM obtenu, utilisation d'une liste vide")
        
        # Si l'analyse des images est activée
        if 'image' in args.modules:
            image_analyzer = ImageAnalyzer(driver, logger, args.url, args.output_dir)
            image_results = image_analyzer.run()
            
            # Vérifier que les résultats d'images ne sont pas None
            if image_results is None:
                image_results = []
                log_with_step(logger, logging.WARNING, "DRIVER", "Aucun résultat d'analyse d'images obtenu, utilisation d'une liste vide")
    except Exception as e:
        log_with_step(logger, logging.ERROR, "DRIVER", f"Erreur lors de l'analyse: {str(e)}")
    finally:
        driver.quit()
