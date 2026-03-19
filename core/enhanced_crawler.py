from modules.contrast_checker import ContrastChecker
from modules.color_simulator import ColorSimulator
from modules.tab_navigator import TabNavigator
from modules.enhanced_tab_navigator import EnhancedTabNavigator
from modules.screen_reader import ScreenReader
from modules.image_analyzer import ImageAnalyzer
from modules.navigation import NavigationModule
from utils.log_utils import setup_logger
from core.shared_data import SharedData

class EnhancedAccessibilityCrawler:
    def __init__(self, config):
        self.config = config
        self.modules = []
        self.driver = None
        self.logger = setup_logger()
        self.shared_data = SharedData()  # Système de partage de données

    def _load_modules(self):
        if 'contrast' in self.config.get_enabled_modules():
            self.modules.append(ContrastChecker(self.driver, self.logger))
        if 'accessibility' in self.config.get_enabled_modules():
            # Passer les données partagées au ScreenReader
            screen_reader = ScreenReader(self.driver, self.logger)
            screen_reader.shared_data = self.shared_data
            self.modules.append(screen_reader)
        if 'daltonism' in self.config.get_enabled_modules():
            self.modules.append(ColorSimulator(self.driver, self.logger))
        if 'tab_navigation' in self.config.get_enabled_modules():
            # Utiliser l'EnhancedTabNavigator avec partage de données
            self.modules.append(EnhancedTabNavigator(
                self.driver,
                self.logger,
                self.config.get_max_screenshots(),
                self.shared_data,
                second_screenshot=self.config.get_focus_second_screenshot(),
                second_screenshot_delay=self.config.get_focus_second_screenshot_delay(),
            ))
        if 'image_analyzer' in self.config.get_enabled_modules():
            self.modules.append(ImageAnalyzer(self.driver, self.logger, self.config.base_url, self.config.output_dir))
        if 'navigation' in self.config.get_enabled_modules():
            self.modules.append(NavigationModule(self.driver, self.logger))

    def crawl(self):
        if self.driver is None:
            raise ValueError("Le driver n'est pas initialisé. Assurez-vous que crawler.driver est défini avant d'appeler crawl().")
        
        # Exécuter les modules dans l'ordre optimal
        for module in self.modules:
            if hasattr(module, 'shared_data'):
                module.shared_data = self.shared_data
            module.run()
            
            # Si c'est le ScreenReader, récupérer ses données ARIA
            if isinstance(module, ScreenReader):
                self._extract_aria_data_from_screen_reader(module)

    def _extract_aria_data_from_screen_reader(self, screen_reader):
        """Extrait les données ARIA du ScreenReader et les stocke dans les données partagées"""
        try:
            # Le ScreenReader stocke ses données dans csv_lines et non_conformites
            if hasattr(screen_reader, 'csv_lines') and screen_reader.csv_lines:
                self.logger.info("Extraction des données ARIA du ScreenReader...")
                
                # Parser les données CSV pour extraire les informations ARIA
                for line in screen_reader.csv_lines[1:]:  # Skip header
                    if line.strip():
                        parts = line.split(';')
                        if len(parts) >= 14:  # Vérifier qu'on a assez de colonnes
                            # Extraire les informations de base
                            element_type = parts[0]
                            selector = parts[1]
                            html_extract = parts[2]
                            role = parts[3]
                            aria_label = parts[4]
                            text = parts[5]
                            alt = parts[6]
                            title = parts[7]
                            visible = parts[8]
                            focusable = parts[9]
                            element_id = parts[10]
                            main_xpath = parts[11]
                            
                            # Créer un identifiant unique pour l'élément
                            element_identifier = f"{element_type}_{selector}_{element_id}"
                            
                            # Stocker les données ARIA
                            aria_data = {
                                'Type': element_type,
                                'Sélecteur': selector,
                                'Rôle': role,
                                'Aria-label': aria_label,
                                'Text': text,
                                'Alt': alt,
                                'Title': title,
                                'Visible': visible,
                                'Focusable': focusable,
                                'Id': element_id,
                                'XPath': main_xpath
                            }
                            
                            # Ajouter toutes les propriétés ARIA détectées par le ScreenReader
                            # (ces données sont déjà dans le ScreenReader, on les récupère)
                            self.shared_data.add_aria_data(element_identifier, aria_data)
                
                self.logger.info(f"Données ARIA extraites et stockées pour {len(self.shared_data.aria_data)} éléments")
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'extraction des données ARIA: {e}")

    def generate_report(self, export_csv=False, csv_filename=None):
        self.logger.info("Génération du rapport d'analyse...")
        
        # Export CSV si demandé
        if export_csv:
            try:
                from utils.csv_exporter import CSVExporter
                exporter = CSVExporter()
                
                aria_count = len(self.shared_data.aria_data)
                focusable_count = len(self.shared_data.focusable_elements)
                
                if aria_count > 0 or focusable_count > 0:
                    filepath = exporter.export_complete_data(self.shared_data, csv_filename)
                    self.logger.info(f"📄 Données exportées en CSV: {filepath}")
                    self.logger.info(f"📊 Données exportées: {aria_count} éléments ARIA, {focusable_count} éléments focusables")
                else:
                    self.logger.warning("⚠️  Aucune donnée à exporter en CSV")
                    
            except Exception as e:
                self.logger.error(f"❌ Erreur lors de l'export CSV: {e}")
        
        self.logger.info("Rapport généré avec succès.")

    def set_driver(self, driver):
        self.driver = driver
        self._load_modules()  # Charger les modules après l'initialisation du driver

    def get_shared_data(self):
        """Retourne les données partagées entre les modules"""
        return self.shared_data
