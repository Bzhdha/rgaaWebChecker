from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import time
from utils.log_utils import log_with_step
import logging

class DOMAnalyzer:
    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger

    def run(self):
        log_with_step(self.logger, logging.INFO, "DOM", "\nAnalyse des éléments d'accessibilité...")
        
        # Attendre que la page soit stable
        WebDriverWait(self.driver, 10).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        
        # Attendre un peu plus pour s'assurer que les éléments dynamiques sont chargés
        time.sleep(2)
        
        # Récupérer tous les éléments une seule fois
        elements = self.driver.find_elements(By.XPATH, "//*")
        total_elements = len(elements)
        log_with_step(self.logger, logging.INFO, "DOM", f"Nombre total d'éléments HTML à analyser : {total_elements}")
        
        # Analyser les éléments par lots pour éviter les problèmes de stale elements
        batch_size = 50
        analyzed_elements = []
        
        for i in range(0, total_elements, batch_size):
            batch = elements[i:i + batch_size]
            for element in batch:
                try:
                    # Vérifier si l'élément est toujours valide
                    if not self._is_element_stale(element):
                        element_info = self._analyze_element(element)
                        # Filtrer les éléments None pour éviter les erreurs d'itération
                        if element_info is not None:
                            analyzed_elements.append(element_info)
                except StaleElementReferenceException:
                    continue
                except Exception as e:
                    log_with_step(self.logger, logging.WARNING, "DOM", f"Erreur lors de l'analyse d'un élément : {str(e)}")
                    continue
            
            # Afficher la progression
            progress = (i + len(batch)) / total_elements * 100
            log_with_step(self.logger, logging.INFO, "DOM", f"Progression : {progress:.1f}% ({i + len(batch)}/{total_elements})")
            
            # Attendre un peu entre chaque lot pour laisser le temps à la page de se stabiliser
            time.sleep(0.5)
        
        return analyzed_elements

    def _is_element_stale(self, element):
        try:
            # Tenter d'accéder à une propriété de l'élément
            element.tag_name
            return False
        except StaleElementReferenceException:
            return True

    def _analyze_element(self, element):
        try:
            element_info = {
                'tag': element.tag_name,
                'id': element.get_attribute('id'),
                'class': element.get_attribute('class'),
                'role': element.get_attribute('role'),
                'aria_label': element.get_attribute('aria-label'),
                'text': element.text.strip() if element.text else '',
                'alt': element.get_attribute('alt'),
                'title': element.get_attribute('title'),
                'media_path': '',  # Renommé de image_path à media_path
                'media_type': ''   # Nouveau champ pour le type de média
            }
            
            tag_name = element.tag_name.lower()
            
            # Gestion des différents types de médias
            if tag_name == 'img':
                src = element.get_attribute('src')
                if src:
                    element_info['media_path'] = src
                    element_info['media_type'] = 'image'
            elif tag_name in ['frame', 'iframe']:
                src = element.get_attribute('src')
                if src:
                    element_info['media_path'] = src
                    element_info['media_type'] = 'frame'
            elif tag_name == 'video':
                # Vérifier d'abord la source directe
                src = element.get_attribute('src')
                if src:
                    element_info['media_path'] = src
                    element_info['media_type'] = 'video'
                # Vérifier aussi les sources enfants
                sources = element.find_elements(By.TAG_NAME, 'source')
                if sources:
                    element_info['media_path'] = sources[0].get_attribute('src')
                    element_info['media_type'] = 'video'
            elif tag_name == 'source':
                src = element.get_attribute('src')
                if src:
                    element_info['media_path'] = src
                    element_info['media_type'] = 'source'
            elif tag_name in ['embed', 'object']:
                src = element.get_attribute('src') or element.get_attribute('data')
                if src:
                    element_info['media_path'] = src
                    element_info['media_type'] = tag_name
            
            return element_info
        except StaleElementReferenceException:
            raise
        except Exception as e:
            log_with_step(self.logger, logging.WARNING, "DOM", f"Erreur lors de l'analyse d'un élément : {str(e)}")
            # Retourner une valeur par défaut au lieu de None
            return {
                'tag': 'unknown',
                'id': '',
                'class': '',
                'role': '',
                'aria_label': '',
                'text': '',
                'alt': '',
                'title': '',
                'media_path': '',
                'media_type': ''
            } 