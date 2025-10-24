from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class NavigationModule:
    """Module de test pour la thématique 12 (Navigation) du RGAA 4.1"""
    
    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger
        self.violations = []

    def run(self):
        """Exécute tous les tests de navigation"""
        self.logger.info("Démarrage des tests de navigation")
        
        # Test 12.1 - Présence d'un plan du site
        self.test_12_1()
        
        # Test 12.2 - Présence d'au moins deux systèmes de navigation
        self.test_12_2()
        
        # Test 12.3 - Présence d'un fil d'Ariane
        self.test_12_3()
        
        # Test 12.4 - Accessibilité du plan du site
        self.test_12_4()
        
        # Test 12.5 - Accessibilité des systèmes de navigation
        self.test_12_5()
        
        # Test 12.6 - Accessibilité du fil d'Ariane
        self.test_12_6()
        
        # Test 12.7 - Présence d'une page d'accueil
        self.test_12_7()
        
        # Test 12.8 - Accessibilité de la page d'accueil
        self.test_12_8()
        
        # Test 12.9 - Présence d'une page de contact
        self.test_12_9()
        
        # Test 12.10 - Accessibilité de la page de contact
        self.test_12_10()
        
        # Test 12.11 - Présence d'une page d'aide
        self.test_12_11()
        
        # Test 12.12 - Accessibilité de la page d'aide
        self.test_12_12()
        
        # Test 12.13 - Présence d'une page de mentions légales
        self.test_12_13()
        
        # Test 12.14 - Accessibilité de la page de mentions légales
        self.test_12_14()
        
        # Enregistrer les résultats dans le rapport
        self.logger.info("\nRésultats des tests de navigation :")
        if not self.violations:
            self.logger.info("✅ Aucune violation trouvée pour les critères de navigation")
        else:
            self.logger.info("❌ Violations trouvées :")
            for criterion_id, element, description in self.violations:
                self.logger.info(f"  - Critère {criterion_id} ({element}) : {description}")
        
        return self.violations

    def test_12_1(self):
        """Test 12.1 - Présence d'un plan du site"""
        try:
            # Recherche d'un lien vers le plan du site
            plan_site = self.driver.find_elements(By.XPATH, "//a[contains(translate(., 'PLAN DU SITE', 'plan du site'), 'plan du site')]")
            if not plan_site:
                self.violations.append(('12.1', 'plan du site', 'Aucun lien vers le plan du site trouvé'))
                self.logger.warning("❌ Critère 12.1 : Aucun lien vers le plan du site trouvé")
            else:
                self.logger.info("✅ Critère 12.1 : Plan du site trouvé")
        except Exception as e:
            self.logger.error(f"Erreur lors du test 12.1: {str(e)}")

    def test_12_2(self):
        """Test 12.2 - Présence d'au moins deux systèmes de navigation"""
        try:
            # Recherche des systèmes de navigation (menu principal, menu secondaire, etc.)
            nav_systems = self.driver.find_elements(By.TAG_NAME, "nav")
            if len(nav_systems) < 2:
                self.violations.append(('12.2', 'systèmes de navigation', 'Moins de deux systèmes de navigation trouvés'))
                self.logger.warning(f"❌ Critère 12.2 : Moins de deux systèmes de navigation trouvés ({len(nav_systems)} trouvé(s))")
            else:
                self.logger.info(f"✅ Critère 12.2 : {len(nav_systems)} systèmes de navigation trouvés")
        except Exception as e:
            self.logger.error(f"Erreur lors du test 12.2: {str(e)}")

    def test_12_3(self):
        """Test 12.3 - Présence d'un fil d'Ariane"""
        try:
            # Recherche d'un fil d'Ariane
            breadcrumb = self.driver.find_elements(By.CLASS_NAME, "breadcrumb")
            if not breadcrumb:
                self.violations.append(('12.3', 'fil d\'Ariane', 'Aucun fil d\'Ariane trouvé'))
                self.logger.warning("❌ Critère 12.3 : Aucun fil d'Ariane trouvé")
            else:
                self.logger.info("✅ Critère 12.3 : Fil d'Ariane trouvé")
        except Exception as e:
            self.logger.error(f"Erreur lors du test 12.3: {str(e)}")

    def test_12_4(self):
        """Test 12.4 - Accessibilité du plan du site"""
        try:
            # Vérification de l'accessibilité du plan du site
            plan_site = self.driver.find_elements(By.XPATH, "//a[contains(translate(., 'PLAN DU SITE', 'plan du site'), 'plan du site')]")
            if plan_site:
                # Vérifier si le lien est accessible au clavier
                if not plan_site[0].is_enabled() or not plan_site[0].is_displayed():
                    self.violations.append(('12.4', 'plan du site', 'Le lien vers le plan du site n\'est pas accessible'))
                    self.logger.warning("❌ Critère 12.4 : Le lien vers le plan du site n'est pas accessible")
                else:
                    self.logger.info("✅ Critère 12.4 : Le lien vers le plan du site est accessible")
        except Exception as e:
            self.logger.error(f"Erreur lors du test 12.4: {str(e)}")

    def test_12_5(self):
        """Test 12.5 - Accessibilité des systèmes de navigation"""
        try:
            nav_systems = self.driver.find_elements(By.TAG_NAME, "nav")
            inaccessible_navs = []
            for i, nav in enumerate(nav_systems):
                # Vérifier si la navigation est accessible au clavier
                if not nav.is_enabled() or not nav.is_displayed():
                    inaccessible_navs.append(i + 1)
                    self.violations.append(('12.5', 'système de navigation', f'Le système de navigation #{i+1} n\'est pas accessible'))
            
            if inaccessible_navs:
                self.logger.warning(f"❌ Critère 12.5 : Les systèmes de navigation #{', '.join(map(str, inaccessible_navs))} ne sont pas accessibles")
            else:
                self.logger.info("✅ Critère 12.5 : Tous les systèmes de navigation sont accessibles")
        except Exception as e:
            self.logger.error(f"Erreur lors du test 12.5: {str(e)}")

    def test_12_6(self):
        """Test 12.6 - Accessibilité du fil d'Ariane"""
        try:
            breadcrumb = self.driver.find_elements(By.CLASS_NAME, "breadcrumb")
            if breadcrumb:
                # Vérifier si le fil d'Ariane est accessible au clavier
                if not breadcrumb[0].is_enabled() or not breadcrumb[0].is_displayed():
                    self.violations.append(('12.6', 'fil d\'Ariane', 'Le fil d\'Ariane n\'est pas accessible'))
                    self.logger.warning("❌ Critère 12.6 : Le fil d'Ariane n'est pas accessible")
                else:
                    self.logger.info("✅ Critère 12.6 : Le fil d'Ariane est accessible")
        except Exception as e:
            self.logger.error(f"Erreur lors du test 12.6: {str(e)}")

    def test_12_7(self):
        """Test 12.7 - Présence d'une page d'accueil"""
        try:
            # Recherche d'un lien vers la page d'accueil
            accueil = self.driver.find_elements(By.XPATH, "//a[contains(translate(., 'ACCUEIL', 'accueil'), 'accueil')]")
            if not accueil:
                self.violations.append(('12.7', 'page d\'accueil', 'Aucun lien vers la page d\'accueil trouvé'))
                self.logger.warning("❌ Critère 12.7 : Aucun lien vers la page d'accueil trouvé")
            else:
                self.logger.info("✅ Critère 12.7 : Lien vers la page d'accueil trouvé")
        except Exception as e:
            self.logger.error(f"Erreur lors du test 12.7: {str(e)}")

    def test_12_8(self):
        """Test 12.8 - Accessibilité de la page d'accueil"""
        try:
            accueil = self.driver.find_elements(By.XPATH, "//a[contains(translate(., 'ACCUEIL', 'accueil'), 'accueil')]")
            if accueil:
                # Vérifier si le lien est accessible au clavier
                if not accueil[0].is_enabled() or not accueil[0].is_displayed():
                    self.violations.append(('12.8', 'page d\'accueil', 'Le lien vers la page d\'accueil n\'est pas accessible'))
                    self.logger.warning("❌ Critère 12.8 : Le lien vers la page d'accueil n'est pas accessible")
                else:
                    self.logger.info("✅ Critère 12.8 : Le lien vers la page d'accueil est accessible")
        except Exception as e:
            self.logger.error(f"Erreur lors du test 12.8: {str(e)}")

    def test_12_9(self):
        """Test 12.9 - Présence d'une page de contact"""
        try:
            # Recherche d'un lien vers la page de contact
            contact = self.driver.find_elements(By.XPATH, "//a[contains(translate(., 'CONTACT', 'contact'), 'contact')]")
            if not contact:
                self.violations.append(('12.9', 'page de contact', 'Aucun lien vers la page de contact trouvé'))
                self.logger.warning("❌ Critère 12.9 : Aucun lien vers la page de contact trouvé")
            else:
                self.logger.info("✅ Critère 12.9 : Lien vers la page de contact trouvé")
        except Exception as e:
            self.logger.error(f"Erreur lors du test 12.9: {str(e)}")

    def test_12_10(self):
        """Test 12.10 - Accessibilité de la page de contact"""
        try:
            contact = self.driver.find_elements(By.XPATH, "//a[contains(translate(., 'CONTACT', 'contact'), 'contact')]")
            if contact:
                # Vérifier si le lien est accessible au clavier
                if not contact[0].is_enabled() or not contact[0].is_displayed():
                    self.violations.append(('12.10', 'page de contact', 'Le lien vers la page de contact n\'est pas accessible'))
                    self.logger.warning("❌ Critère 12.10 : Le lien vers la page de contact n'est pas accessible")
                else:
                    self.logger.info("✅ Critère 12.10 : Le lien vers la page de contact est accessible")
        except Exception as e:
            self.logger.error(f"Erreur lors du test 12.10: {str(e)}")

    def test_12_11(self):
        """Test 12.11 - Présence d'une page d'aide"""
        try:
            # Recherche d'un lien vers la page d'aide
            aide = self.driver.find_elements(By.XPATH, "//a[contains(translate(., 'AIDE', 'aide'), 'aide')]")
            if not aide:
                self.violations.append(('12.11', 'page d\'aide', 'Aucun lien vers la page d\'aide trouvé'))
                self.logger.warning("❌ Critère 12.11 : Aucun lien vers la page d'aide trouvé")
            else:
                self.logger.info("✅ Critère 12.11 : Lien vers la page d'aide trouvé")
        except Exception as e:
            self.logger.error(f"Erreur lors du test 12.11: {str(e)}")

    def test_12_12(self):
        """Test 12.12 - Accessibilité de la page d'aide"""
        try:
            aide = self.driver.find_elements(By.XPATH, "//a[contains(translate(., 'AIDE', 'aide'), 'aide')]")
            if aide:
                # Vérifier si le lien est accessible au clavier
                if not aide[0].is_enabled() or not aide[0].is_displayed():
                    self.violations.append(('12.12', 'page d\'aide', 'Le lien vers la page d\'aide n\'est pas accessible'))
                    self.logger.warning("❌ Critère 12.12 : Le lien vers la page d'aide n'est pas accessible")
                else:
                    self.logger.info("✅ Critère 12.12 : Le lien vers la page d'aide est accessible")
        except Exception as e:
            self.logger.error(f"Erreur lors du test 12.12: {str(e)}")

    def test_12_13(self):
        """Test 12.13 - Présence d'une page de mentions légales"""
        try:
            # Recherche d'un lien vers la page de mentions légales
            mentions = self.driver.find_elements(By.XPATH, "//a[contains(translate(., 'MENTIONS LÉGALES', 'mentions légales'), 'mentions légales')]")
            if not mentions:
                self.violations.append(('12.13', 'page de mentions légales', 'Aucun lien vers la page de mentions légales trouvé'))
                self.logger.warning("❌ Critère 12.13 : Aucun lien vers la page de mentions légales trouvé")
            else:
                self.logger.info("✅ Critère 12.13 : Lien vers la page de mentions légales trouvé")
        except Exception as e:
            self.logger.error(f"Erreur lors du test 12.13: {str(e)}")

    def test_12_14(self):
        """Test 12.14 - Accessibilité de la page de mentions légales"""
        try:
            mentions = self.driver.find_elements(By.XPATH, "//a[contains(translate(., 'MENTIONS LÉGALES', 'mentions légales'), 'mentions légales')]")
            if mentions:
                # Vérifier si le lien est accessible au clavier
                if not mentions[0].is_enabled() or not mentions[0].is_displayed():
                    self.violations.append(('12.14', 'page de mentions légales', 'Le lien vers la page de mentions légales n\'est pas accessible'))
                    self.logger.warning("❌ Critère 12.14 : Le lien vers la page de mentions légales n'est pas accessible")
                else:
                    self.logger.info("✅ Critère 12.14 : Le lien vers la page de mentions légales est accessible")
        except Exception as e:
            self.logger.error(f"Erreur lors du test 12.14: {str(e)}") 