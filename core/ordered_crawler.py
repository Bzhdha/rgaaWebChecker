from modules.contrast_checker import ContrastChecker
from modules.color_simulator import ColorSimulator
from modules.tab_navigator import TabNavigator
from modules.enhanced_tab_navigator import EnhancedTabNavigator
from modules.screen_reader import ScreenReader
from modules.enhanced_screen_reader import EnhancedScreenReader
from modules.hierarchical_screen_reader import HierarchicalScreenReader
from modules.image_analyzer import ImageAnalyzer
from modules.navigation import NavigationModule
from utils.log_utils import setup_logger
from core.shared_data import SharedData

class OrderedAccessibilityCrawler:
    def __init__(self, config, use_hierarchy=False):
        self.config = config
        self.driver = None
        self.logger = setup_logger()
        self.shared_data = SharedData()
        self.use_hierarchy = use_hierarchy
        self.css_marker = None
        
        # Définir l'ordre d'exécution optimal
        self.execution_order = {
            'screen_reader': 1,      # DOIT être en premier pour collecter les données ARIA
            'tab_navigation': 2,     # DOIT être en second pour utiliser les données ARIA
            'contrast': 3,           # Peut s'exécuter en parallèle
            'daltonism': 3,          # Peut s'exécuter en parallèle
            'image_analyzer': 3,     # Peut s'exécuter en parallèle
            'navigation': 3,        # Peut s'exécuter en parallèle
            'dom_analyzer': 4       # En dernier car il analyse tout le DOM
        }
        
        self.modules_by_priority = {}

    def _load_modules(self):
        """Charge les modules dans l'ordre optimal"""
        enabled_modules = self.config.get_enabled_modules()
        self.logger.info(f"Modules activés détectés: {enabled_modules}")
        
        # Phase 1: ScreenReader (collecte des données ARIA)
        if 'screen_reader' in enabled_modules:
            if self.use_hierarchy:
                screen_reader = HierarchicalScreenReader(self.driver, self.logger, enable_css_marking=self.css_marker is not None)
                self.logger.info("✓ HierarchicalScreenReader chargé (Phase 1 - Collecte des données ARIA avec algorithme hiérarchique)")
            else:
                screen_reader = EnhancedScreenReader(self.driver, self.logger, enable_css_marking=self.css_marker is not None)
                self.logger.info("✓ EnhancedScreenReader chargé (Phase 1 - Collecte des données ARIA)")
            
            screen_reader.shared_data = self.shared_data
            if self.css_marker:
                screen_reader.css_marker = self.css_marker
                if self.use_hierarchy:
                    self.logger.info("🎨 CSSMarker configuré pour HierarchicalScreenReader")
                else:
                    self.logger.info("🎨 CSSMarker configuré pour EnhancedScreenReader")
                self.logger.debug(f"CSSMarker instance: {self.css_marker}")
                self.logger.debug(f"ScreenReader CSSMarker: {screen_reader.css_marker}")
            self.modules_by_priority[1] = [screen_reader]
        
        # Phase 2: TabNavigator (utilise les données ARIA)
        if 'tab_navigation' in enabled_modules:
            tab_navigator = EnhancedTabNavigator(
                self.driver, 
                self.logger, 
                self.config.get_max_screenshots(),
                self.shared_data
            )
            if 2 not in self.modules_by_priority:
                self.modules_by_priority[2] = []
            self.modules_by_priority[2].append(tab_navigator)
            self.logger.info("✓ TabNavigator chargé (Phase 2 - Utilisation des données ARIA)")
        
        # Phase 3: Modules parallèles (peuvent s'exécuter en même temps)
        phase_3_modules = []
        
        if 'contrast' in enabled_modules:
            phase_3_modules.append(ContrastChecker(self.driver, self.logger))
            self.logger.info("✓ ContrastChecker chargé (Phase 3)")
            
        if 'daltonism' in enabled_modules:
            phase_3_modules.append(ColorSimulator(self.driver, self.logger))
            self.logger.info("✓ ColorSimulator chargé (Phase 3)")
            
        if 'image_analyzer' in enabled_modules:
            phase_3_modules.append(ImageAnalyzer(
                self.driver, 
                self.logger, 
                self.config.base_url, 
                self.config.output_dir
            ))
            self.logger.info("✓ ImageAnalyzer chargé (Phase 3)")
            
        if 'navigation' in enabled_modules:
            phase_3_modules.append(NavigationModule(self.driver, self.logger))
            self.logger.info("✓ NavigationModule chargé (Phase 3)")
        
        if phase_3_modules:
            self.modules_by_priority[3] = phase_3_modules
        
        # Phase 4: DOM Analyzer (en dernier)
        if 'dom' in enabled_modules:
            from modules.dom_analyzer import DOMAnalyzer
            dom_analyzer = DOMAnalyzer(self.driver, self.logger, enable_css_marking=self.css_marker is not None)
            if self.css_marker:
                dom_analyzer.css_marker = self.css_marker
            self.modules_by_priority[4] = [dom_analyzer]
            self.logger.info("✓ DOMAnalyzer chargé (Phase 4)")

    def crawl(self, export_csv=False, csv_filename=None):
        """Exécute les modules dans l'ordre optimal"""
        if self.driver is None:
            raise ValueError("Le driver n'est pas initialisé.")
        
        self.logger.info("\n🚀 Démarrage de l'analyse d'accessibilité avec ordre optimisé")
        self.logger.info("=" * 60)
        
        # Exécuter les modules par phase dans l'ordre
        for phase in sorted(self.modules_by_priority.keys()):
            modules = self.modules_by_priority[phase]
            
            if phase == 1:
                self.logger.info(f"\n📊 PHASE {phase}: COLLECTE DES DONNÉES ARIA")
                self.logger.info("Collecte des données ARIA de tous les éléments de la page...")
                
            elif phase == 2:
                self.logger.info(f"\n🎯 PHASE {phase}: NAVIGATION TABULAIRE AVEC DONNÉES ARIA")
                self.logger.info("Navigation au clavier avec analyse ARIA enrichie...")
                
            elif phase == 3:
                self.logger.info(f"\n⚡ PHASE {phase}: ANALYSES PARALLÈLES")
                self.logger.info("Exécution des autres modules d'analyse...")
                
            elif phase == 4:
                self.logger.info(f"\n🔍 PHASE {phase}: ANALYSE DOM COMPLÈTE")
                self.logger.info("Analyse finale de la structure DOM...")
            
            # Exécuter les modules de cette phase
            for module in modules:
                try:
                    module_name = module.__class__.__name__
                    self.logger.info(f"\n▶️  Exécution de {module_name}...")
                    
                    # Exécuter le module
                    result = module.run()
                    
                    # Si c'est le ScreenReader, extraire les données ARIA
                    if isinstance(module, EnhancedScreenReader):
                        self._extract_aria_data_from_screen_reader(module)
                        self.logger.info(f"✅ {module_name} terminé - Données ARIA collectées")
                    else:
                        self.logger.info(f"✅ {module_name} terminé")
                        
                except Exception as e:
                    self.logger.error(f"❌ Erreur dans {module_name}: {str(e)}")
                    continue
            
            # Afficher le statut des données partagées après chaque phase
            if phase >= 2:  # Après la phase 1 (ScreenReader)
                aria_count = len(self.shared_data.aria_data)
                self.logger.info(f"📈 Données ARIA disponibles: {aria_count} éléments")
        
        self.logger.info("\n🎉 Analyse terminée avec succès !")
        self.logger.info("=" * 60)
        
        # Générer le rapport final avec export CSV si demandé
        self.generate_report(export_csv, csv_filename)

    def _extract_aria_data_from_screen_reader(self, screen_reader):
        """Extrait les données ARIA du ScreenReader"""
        try:
            # Récupérer toutes les données ARIA collectées
            aria_data = screen_reader.get_all_aria_data()
            
            if aria_data:
                self.logger.info(f"📥 Extraction de {len(aria_data)} éléments avec données ARIA...")
                
                # Stocker les données dans le système de partage
                for element_id, data in aria_data.items():
                    self.shared_data.add_aria_data(element_id, data)
                
                self.logger.info(f"✅ {len(aria_data)} éléments ARIA stockés dans les données partagées")
            else:
                self.logger.warning("⚠️  Aucune donnée ARIA trouvée par le ScreenReader")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'extraction des données ARIA: {e}")

    def generate_report(self, export_csv=False, csv_filename=None):
        """Génère le rapport final"""
        self.logger.info("\n📋 Génération du rapport d'analyse...")
        
        # Statistiques des données partagées
        aria_count = len(self.shared_data.aria_data)
        focusable_count = len(self.shared_data.focusable_elements)
        
        self.logger.info(f"📊 Statistiques finales:")
        self.logger.info(f"   - Éléments avec données ARIA: {aria_count}")
        self.logger.info(f"   - Éléments focusables: {focusable_count}")
        
        # Export CSV si demandé
        if export_csv:
            try:
                from utils.csv_exporter import CSVExporter
                exporter = CSVExporter()
                
                if aria_count > 0 or focusable_count > 0:
                    filepath = exporter.export_complete_data(self.shared_data, csv_filename)
                    self.logger.info(f"📄 Données exportées en CSV: {filepath}")
                else:
                    self.logger.warning("⚠️  Aucune donnée à exporter en CSV")
                    
            except Exception as e:
                self.logger.error(f"❌ Erreur lors de l'export CSV: {e}")
        
        self.logger.info("✅ Rapport généré avec succès.")

    def set_driver(self, driver):
        """Initialise le driver et charge les modules"""
        self.driver = driver
        self._load_modules()

    def get_shared_data(self):
        """Retourne les données partagées"""
        return self.shared_data

    def get_execution_summary(self):
        """Retourne un résumé de l'ordre d'exécution"""
        summary = []
        for phase in sorted(self.modules_by_priority.keys()):
            modules = self.modules_by_priority[phase]
            module_names = [m.__class__.__name__ for m in modules]
            summary.append(f"Phase {phase}: {', '.join(module_names)}")
        return summary
    
    def set_css_marker(self, css_marker):
        """Définit le CSSMarker pour le crawler"""
        self.css_marker = css_marker
        if self.css_marker:
            self.logger.info("🎨 CSSMarker configuré pour le crawler")
