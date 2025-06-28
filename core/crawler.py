from modules.contrast_checker import ContrastChecker
from modules.color_simulator import ColorSimulator
from modules.tab_navigator import TabNavigator
from modules.screen_reader import ScreenReader
from modules.image_analyzer import ImageAnalyzer
from modules.dom_analyzer import DOMAnalyzer
from utils.log_utils import setup_logger

class AccessibilityCrawler:
    def __init__(self, config, logger=None):
        self.config = config
        self.modules = []
        self.driver = None
        self.logger = logger if logger else setup_logger()

    def _load_modules(self):
        if 'contrast' in self.config.get_enabled_modules():
            self.modules.append(ContrastChecker(self.driver, self.logger))
        if 'dom_analyzer' in self.config.get_enabled_modules():
            self.modules.append(DOMAnalyzer(self.driver, self.logger))
        if 'accessibility' in self.config.get_enabled_modules():
            self.modules.append(ScreenReader(self.driver, self.logger))
        if 'daltonism' in self.config.get_enabled_modules():
            self.modules.append(ColorSimulator(self.driver, self.logger))
        if 'tab_navigation' in self.config.get_enabled_modules():
            self.modules.append(TabNavigator(self.driver, self.logger))
        if 'image_analyzer' in self.config.get_enabled_modules():
            self.modules.append(ImageAnalyzer(self.driver, self.logger, self.config.base_url, self.config.output_dir))

    def crawl(self):
        if self.driver is None:
            raise ValueError("Le driver n'est pas initialisé. Assurez-vous que crawler.driver est défini avant d'appeler crawl().")
        for module in self.modules:
            module.run()

    def generate_report(self):
        self.logger.info("Génération du rapport d'analyse...")
        self.logger.info("Rapport généré avec succès.")

    def set_driver(self, driver):
        self.driver = driver
        self._load_modules()  # Charger les modules après l'initialisation du driver
