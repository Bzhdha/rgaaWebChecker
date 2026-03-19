from modules.contrast_checker import ContrastChecker
from modules.color_simulator import ColorSimulator
from modules.tab_navigator import TabNavigator
from modules.screen_reader import ScreenReader
from modules.image_analyzer import ImageAnalyzer
from modules.navigation import NavigationModule
from modules.dom_analyzer import DOMAnalyzer
from modules.titles_analyzer import TitlesAnalyzer
from utils.log_utils import setup_logger

class AccessibilityCrawler:
    def __init__(self, config, logger=None, tab_delay=0.0):
        self.config = config
        self.modules = []
        self.driver = None
        self.logger = logger if logger else setup_logger()
        self.results = {}  # Stockage des résultats
        self.tab_delay = tab_delay  # Délai pour la navigation tabulaire

    def _load_modules(self):
        if 'contrast' in self.config.get_enabled_modules():
            self.modules.append(ContrastChecker(self.driver, self.logger))
        if 'dom_analyzer' in self.config.get_enabled_modules():
            self.modules.append(DOMAnalyzer(self.driver, self.logger))
        if 'screen_reader' in self.config.get_enabled_modules():
            self.modules.append(ScreenReader(self.driver, self.logger))
        if 'daltonism' in self.config.get_enabled_modules():
            self.modules.append(ColorSimulator(self.driver, self.logger))
        if 'tab_navigation' in self.config.get_enabled_modules():
            self.modules.append(TabNavigator(self.driver, self.logger, self.config.get_max_screenshots()))
        if 'image_analyzer' in self.config.get_enabled_modules():
            self.modules.append(ImageAnalyzer(self.driver, self.logger, self.config.base_url, self.config.output_dir))
        if 'navigation' in self.config.get_enabled_modules():
            self.modules.append(NavigationModule(self.driver, self.logger))
        if 'titles' in self.config.get_enabled_modules():
            self.modules.append(TitlesAnalyzer(self.driver, self.logger))

    def crawl(self):
        if self.driver is None:
            raise ValueError("Le driver n'est pas initialisé. Assurez-vous que crawler.driver est défini avant d'appeler crawl().")
        
        for module in self.modules:
            module.run()

    def generate_report(self, export_csv=False, csv_filename=None):
        self.logger.info("Génération du rapport d'analyse...")
        
        # Export CSV si demandé
        if export_csv:
            try:
                from utils.csv_exporter import CSVExporter
                exporter = CSVExporter()
                
                # Collecter les données des modules qui en ont
                aria_data = {}
                focusable_elements = []
                
                for module in self.modules:
                    if hasattr(module, 'get_all_aria_data'):
                        module_aria_data = module.get_all_aria_data()
                        if module_aria_data:
                            aria_data.update(module_aria_data)
                    
                    if hasattr(module, 'focusable_elements'):
                        focusable_elements.extend(module.focusable_elements)
                
                if aria_data or focusable_elements:
                    # Créer un objet mock pour partager les données
                    class MockSharedData:
                        def __init__(self, aria_data, focusable_elements):
                            self.aria_data = aria_data
                            self.focusable_elements = focusable_elements
                    
                    mock_shared_data = MockSharedData(aria_data, focusable_elements)
                    filepath = exporter.export_complete_data(mock_shared_data, csv_filename)
                    self.logger.info(f"📄 Données exportées en CSV: {filepath}")
                else:
                    self.logger.warning("⚠️  Aucune donnée à exporter en CSV")
                    
            except Exception as e:
                self.logger.error(f"❌ Erreur lors de l'export CSV: {e}")
        
        self.logger.info("Rapport généré avec succès.")

    def set_driver(self, driver):
        self.driver = driver
        self._load_modules()  # Charger les modules après l'initialisation du driver
