from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import os
from PIL import Image, ImageDraw
import io
import time
from selenium.webdriver.support.ui import WebDriverWait
from utils.log_utils import log_with_step
import logging

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
                log_with_step(self.logger, logging.WARNING, "TABULATION", f"L'élément n'est plus valide pour la capture {index}")
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
                log_with_step(self.logger, logging.WARNING, "TABULATION", f"L'élément n'est plus valide pour la seconde capture {index}")
                return filename1, None
            
            # Seconde capture après le délai
            screenshot2 = self.driver.get_screenshot_as_png()
            highlighted_img2 = self._highlight_element(element, screenshot2)
            filename2 = f"reports/focus_screenshots/focus_{index:03d}_2.png"
            highlighted_img2.save(filename2)
            
            return filename1, filename2
            
        except Exception as e:
            log_with_step(self.logger, logging.ERROR, "TABULATION", f"Erreur lors de la capture d'écran {index}: {str(e)}")
            return None, None

    def _is_element_stale(self, element):
        """Vérifie si l'élément est toujours valide"""
        try:
            element.tag_name
            return False
        except:
            return True

    def run(self):
        log_with_step(self.logger, logging.INFO, "TABULATION", "\nSimulation de navigation réelle au clavier...")
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
                log_with_step(self.logger, logging.WARNING, "TABULATION", f"Erreur lors de l'attente du chargement de la page: {str(e)}")
            
            # Attendre un peu plus pour le JavaScript
            time.sleep(2)
            
            for i in range(50):
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
                        log_with_step(self.logger, logging.WARNING, "TABULATION", "Aucun élément actif trouvé")
                        continue
                    
                    # Vérifier que l'élément est toujours valide
                    if self._is_element_stale(active):
                        log_with_step(self.logger, logging.WARNING, "TABULATION", f"L'élément actif n'est plus valide à l'itération {i+1}")
                        continue
                    
                    # Obtenir les informations de l'élément
                    tag = active.tag_name
                    text = active.text.strip() or active.get_attribute("alt") or active.get_attribute("title")
                    href = active.get_attribute("href")
                    
                    # Récupérer les informations ARIA
                    aria_label = active.get_attribute("aria-label")
                    aria_labelledby = active.get_attribute("aria-labelledby")
                    aria_describedby = active.get_attribute("aria-describedby")
                    role = active.get_attribute("role")
                    aria_hidden = active.get_attribute("aria-hidden")
                    aria_expanded = active.get_attribute("aria-expanded")
                    aria_controls = active.get_attribute("aria-controls")
                    aria_current = active.get_attribute("aria-current")
                    aria_pressed = active.get_attribute("aria-pressed")
                    aria_checked = active.get_attribute("aria-checked")
                    aria_selected = active.get_attribute("aria-selected")
                    aria_disabled = active.get_attribute("aria-disabled")
                    aria_required = active.get_attribute("aria-required")
                    aria_invalid = active.get_attribute("aria-invalid")
                    aria_live = active.get_attribute("aria-live")
                    aria_atomic = active.get_attribute("aria-atomic")
                    aria_relevant = active.get_attribute("aria-relevant")
                    aria_busy = active.get_attribute("aria-busy")
                    aria_level = active.get_attribute("aria-level")
                    aria_posinset = active.get_attribute("aria-posinset")
                    aria_setsize = active.get_attribute("aria-setsize")
                    aria_valuemin = active.get_attribute("aria-valuemin")
                    aria_valuemax = active.get_attribute("aria-valuemax")
                    aria_valuenow = active.get_attribute("aria-valuenow")
                    aria_valuetext = active.get_attribute("aria-valuetext")
                    aria_haspopup = active.get_attribute("aria-haspopup")
                    aria_multiline = active.get_attribute("aria-multiline")
                    aria_multiselectable = active.get_attribute("aria-multiselectable")
                    aria_orientation = active.get_attribute("aria-orientation")
                    aria_placeholder = active.get_attribute("aria-placeholder")
                    aria_roledescription = active.get_attribute("aria-roledescription")
                    aria_keyshortcuts = active.get_attribute("aria-keyshortcuts")
                    aria_details = active.get_attribute("aria-details")
                    aria_errormessage = active.get_attribute("aria-errormessage")
                    aria_flowto = active.get_attribute("aria-flowto")
                    aria_owns = active.get_attribute("aria-owns")
                    
                    # Prendre les captures d'écran avant de logger les informations
                    filename1, filename2 = self._take_screenshots(active, i+1)
                    
                    # Logger les informations de base
                    log_with_step(self.logger, logging.INFO, "TABULATION", f"Focus sur: {tag}, texte: {text}, href: {href}")
                    
                    # Logger les informations ARIA importantes
                    aria_info = []
                    if role:
                        aria_info.append(f"role={role}")
                    if aria_label:
                        aria_info.append(f"aria-label={aria_label}")
                    if aria_labelledby:
                        aria_info.append(f"aria-labelledby={aria_labelledby}")
                    if aria_describedby:
                        aria_info.append(f"aria-describedby={aria_describedby}")
                    if aria_hidden:
                        aria_info.append(f"aria-hidden={aria_hidden}")
                    if aria_expanded:
                        aria_info.append(f"aria-expanded={aria_expanded}")
                    if aria_controls:
                        aria_info.append(f"aria-controls={aria_controls}")
                    if aria_current:
                        aria_info.append(f"aria-current={aria_current}")
                    if aria_pressed:
                        aria_info.append(f"aria-pressed={aria_pressed}")
                    if aria_checked:
                        aria_info.append(f"aria-checked={aria_checked}")
                    if aria_selected:
                        aria_info.append(f"aria-selected={aria_selected}")
                    if aria_disabled:
                        aria_info.append(f"aria-disabled={aria_disabled}")
                    if aria_required:
                        aria_info.append(f"aria-required={aria_required}")
                    if aria_invalid:
                        aria_info.append(f"aria-invalid={aria_invalid}")
                    if aria_live:
                        aria_info.append(f"aria-live={aria_live}")
                    if aria_atomic:
                        aria_info.append(f"aria-atomic={aria_atomic}")
                    if aria_relevant:
                        aria_info.append(f"aria-relevant={aria_relevant}")
                    if aria_busy:
                        aria_info.append(f"aria-busy={aria_busy}")
                    if aria_level:
                        aria_info.append(f"aria-level={aria_level}")
                    if aria_posinset:
                        aria_info.append(f"aria-posinset={aria_posinset}")
                    if aria_setsize:
                        aria_info.append(f"aria-setsize={aria_setsize}")
                    if aria_valuemin:
                        aria_info.append(f"aria-valuemin={aria_valuemin}")
                    if aria_valuemax:
                        aria_info.append(f"aria-valuemax={aria_valuemax}")
                    if aria_valuenow:
                        aria_info.append(f"aria-valuenow={aria_valuenow}")
                    if aria_valuetext:
                        aria_info.append(f"aria-valuetext={aria_valuetext}")
                    if aria_haspopup:
                        aria_info.append(f"aria-haspopup={aria_haspopup}")
                    if aria_multiline:
                        aria_info.append(f"aria-multiline={aria_multiline}")
                    if aria_multiselectable:
                        aria_info.append(f"aria-multiselectable={aria_multiselectable}")
                    if aria_orientation:
                        aria_info.append(f"aria-orientation={aria_orientation}")
                    if aria_placeholder:
                        aria_info.append(f"aria-placeholder={aria_placeholder}")
                    if aria_roledescription:
                        aria_info.append(f"aria-roledescription={aria_roledescription}")
                    if aria_keyshortcuts:
                        aria_info.append(f"aria-keyshortcuts={aria_keyshortcuts}")
                    if aria_details:
                        aria_info.append(f"aria-details={aria_details}")
                    if aria_errormessage:
                        aria_info.append(f"aria-errormessage={aria_errormessage}")
                    if aria_flowto:
                        aria_info.append(f"aria-flowto={aria_flowto}")
                    if aria_owns:
                        aria_info.append(f"aria-owns={aria_owns}")
                    
                    # Afficher les informations ARIA si elles existent
                    if aria_info:
                        log_with_step(self.logger, logging.INFO, "TABULATION", f"Attributs ARIA: {', '.join(aria_info)}")
                    else:
                        # Afficher un message pour indiquer qu'il n'y a pas d'attributs ARIA
                        log_with_step(self.logger, logging.INFO, "TABULATION", "Aucun attribut ARIA détecté")
                    
                    # Debug: afficher quelques attributs de base pour vérification
                    debug_info = []
                    if active.get_attribute("id"):
                        debug_info.append(f"id={active.get_attribute('id')}")
                    if active.get_attribute("class"):
                        debug_info.append(f"class={active.get_attribute('class')}")
                    if active.get_attribute("title"):
                        debug_info.append(f"title={active.get_attribute('title')}")
                    if active.get_attribute("alt"):
                        debug_info.append(f"alt={active.get_attribute('alt')}")
                    
                    if debug_info:
                        log_with_step(self.logger, logging.DEBUG, "TABULATION", f"Attributs de base: {', '.join(debug_info)}")
                    
                    # Test spécial pour vérifier si l'élément a des attributs ARIA
                    all_aria_attrs = []
                    for attr_name in dir(active):
                        if attr_name.startswith('aria_') or attr_name == 'role':
                            try:
                                attr_value = active.get_attribute(attr_name)
                                if attr_value:
                                    all_aria_attrs.append(f"{attr_name}={attr_value}")
                            except:
                                pass
                    
                    if all_aria_attrs:
                        log_with_step(self.logger, logging.INFO, "TABULATION", f"Tous les attributs ARIA trouvés: {', '.join(all_aria_attrs)}")
                    else:
                        log_with_step(self.logger, logging.INFO, "TABULATION", "Aucun attribut ARIA trouvé sur cet élément")
                    
                    if filename1:
                        log_with_step(self.logger, logging.INFO, "TABULATION", f"Capture immédiate: {filename1}")
                    if filename2:
                        log_with_step(self.logger, logging.INFO, "TABULATION", f"Capture après délai: {filename2}")
                    
                    elements_reached.append((tag, text, href))
                    
                except Exception as e:
                    log_with_step(self.logger, logging.ERROR, "TABULATION", f"Erreur lors de la tabulation {i+1}: {str(e)}")
                    # Si l'erreur est liée au driver, on arrête la boucle
                    if "NoneType" in str(e):
                        log_with_step(self.logger, logging.ERROR, "TABULATION", "Le driver n'est plus valide, arrêt de l'analyse")
                        break
                    continue
                
            return elements_reached
            
        except Exception as e:
            log_with_step(self.logger, logging.ERROR, "TABULATION", f"Erreur lors de la simulation de navigation: {str(e)}")
            return []
