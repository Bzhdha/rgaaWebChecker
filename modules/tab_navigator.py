from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import os
from PIL import Image, ImageDraw
import io
import time
from selenium.webdriver.support.ui import WebDriverWait

class TabNavigator:
    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger

    def _highlight_element(self, element, screenshot):
        # Convertir la capture d'écran en image PIL
        img = Image.open(io.BytesIO(screenshot))
        draw = ImageDraw.Draw(img)
        
        # Obtenir les coordonnées de l'élément
        location = element.location
        size = element.size
        
        # Dessiner un rectangle rouge/jaune/rouge autour de l'élément
        x1, y1 = location['x'], location['y']
        x2, y2 = x1 + size['width'], y1 + size['height']
        
        # Rectangle rouge extérieur
        draw.rectangle([x1-2, y1-2, x2+2, y2+2], outline='red', width=2)
        # Rectangle jaune
        draw.rectangle([x1-1, y1-1, x2+1, y2+1], outline='yellow', width=1)
        # Rectangle rouge intérieur
        draw.rectangle([x1, y1, x2, y2], outline='red', width=1)
        
        return img

    def _take_screenshots(self, element, index):
        try:
            # Créer le dossier pour les captures d'écran si nécessaire
            os.makedirs('reports/focus_screenshots', exist_ok=True)
            
            # Vérifier que l'élément est toujours valide
            if self._is_element_stale(element):
                self.logger.warning(f"L'élément n'est plus valide pour la capture {index}")
                return None, None
            
            # Première capture immédiate
            screenshot1 = self.driver.get_screenshot_as_png()
            highlighted_img1 = self._highlight_element(element, screenshot1)
            filename1 = f"reports/focus_screenshots/focus_{index:03d}_1.png"
            highlighted_img1.save(filename1)
            
            # Attendre 0.5 seconde pour laisser le temps au contenu de s'afficher
            time.sleep(0.5)
            
            # Vérifier à nouveau que l'élément est toujours valide
            if self._is_element_stale(element):
                self.logger.warning(f"L'élément n'est plus valide pour la seconde capture {index}")
                return filename1, None
            
            # Seconde capture après le délai
            screenshot2 = self.driver.get_screenshot_as_png()
            highlighted_img2 = self._highlight_element(element, screenshot2)
            filename2 = f"reports/focus_screenshots/focus_{index:03d}_2.png"
            highlighted_img2.save(filename2)
            
            return filename1, filename2
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la capture d'écran {index}: {str(e)}")
            return None, None

    def _is_element_stale(self, element):
        """Vérifie si l'élément est toujours valide"""
        try:
            element.tag_name
            return False
        except:
            return True

    def run(self):
        self.logger.info("\nSimulation de navigation réelle au clavier...")
        try:
            # Vérifier que le driver est valide
            if not self.driver:
                raise Exception("Le driver n'est pas initialisé")
            
            elements_reached = []
            
            # Attendre que la page soit complètement chargée
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
            except Exception as e:
                self.logger.warning(f"Erreur lors de l'attente du chargement de la page: {str(e)}")
            
            # Attendre un peu plus pour le JavaScript
            time.sleep(2)
            
            for i in range(50):  # Limite à 50 tabulations
                try:
                    # Créer une nouvelle instance d'ActionChains à chaque itération
                    action = ActionChains(self.driver)
                    
                    # Envoyer la touche TAB
                    action.send_keys(Keys.TAB)
                    action.perform()
                    
                    # Attendre un court instant pour que le focus soit appliqué
                    time.sleep(0.1)
                    
                    # Récupérer l'élément actif
                    active = self.driver.execute_script("return document.activeElement;")
                    
                    if not active:
                        self.logger.warning("Aucun élément actif trouvé")
                        continue
                    
                    # Vérifier que l'élément est toujours valide
                    if self._is_element_stale(active):
                        self.logger.warning(f"L'élément actif n'est plus valide à l'itération {i+1}")
                        continue
                    
                    # Obtenir les informations de l'élément
                    tag = active.tag_name
                    text = active.text.strip() or active.get_attribute("alt") or active.get_attribute("title")
                    href = active.get_attribute("href")
                    
                    # Prendre les captures d'écran avant de logger les informations
                    filename1, filename2 = self._take_screenshots(active, i+1)
                    
                    # Logger les informations avec les noms des fichiers
                    self.logger.info(f"Focus sur: {tag}, texte: {text}, href: {href}")
                    if filename1:
                        self.logger.info(f"Capture immédiate: {filename1}")
                    if filename2:
                        self.logger.info(f"Capture après délai: {filename2}")
                    
                    elements_reached.append((tag, text, href))
                    
                except Exception as e:
                    self.logger.error(f"Erreur lors de la tabulation {i+1}: {str(e)}")
                    # Si l'erreur est liée au driver, on arrête la boucle
                    if "NoneType" in str(e):
                        self.logger.error("Le driver n'est plus valide, arrêt de l'analyse")
                        break
                    continue
                
            return elements_reached
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la simulation de navigation: {str(e)}")
            return []
