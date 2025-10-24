from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import os
from PIL import Image, ImageDraw
import io
import time
from selenium.webdriver.support.ui import WebDriverWait
from utils.log_utils import log_with_step
import logging
import csv
import json

class TabNavigator:
    def __init__(self, driver, logger, max_screenshots=50):
        self.driver = driver
        self.logger = logger
        self.max_screenshots = max_screenshots

    def _highlight_element(self, element, screenshot):
        # Convertir la capture d'écran en image PIL
        img = Image.open(io.BytesIO(screenshot))
        draw = ImageDraw.Draw(img)
        
        # Obtenir les coordonnées de l'élément avec une méthode plus robuste
        try:
            # Utiliser getBoundingClientRect() pour des coordonnées relatives au viewport
            rect = self.driver.execute_script("""
                var element = arguments[0];
                var rect = element.getBoundingClientRect();
                return {
                    x: Math.round(rect.left),
                    y: Math.round(rect.top),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                };
            """, element)
            
            x1, y1 = rect['x'], rect['y']
            x2, y2 = x1 + rect['width'], y1 + rect['height']
            
        except Exception as e:
            # Fallback sur la méthode Selenium classique
            self.logger.warning(f"Erreur lors du calcul des coordonnées avec getBoundingClientRect: {e}")
            location = element.location
            size = element.size
            x1, y1 = location['x'], location['y']
            x2, y2 = x1 + size['width'], y1 + size['height']
        
        # Vérifier que les coordonnées sont dans les limites de l'image
        img_width, img_height = img.size
        x1 = max(0, min(x1, img_width))
        y1 = max(0, min(y1, img_height))
        x2 = max(0, min(x2, img_width))
        y2 = max(0, min(y2, img_height))
        
        # Dessiner un rectangle rouge/jaune/rouge autour de l'élément
        # Rectangle rouge extérieur
        draw.rectangle([x1-2, y1-2, x2+2, y2+2], outline='red', width=2)
        # Rectangle jaune
        draw.rectangle([x1-1, y1-1, x2+1, y2+1], outline='yellow', width=1)
        # Rectangle rouge intérieur
        draw.rectangle([x1, y1, x2, y2], outline='red', width=1)
        
        return img

    def _validate_window_position(self):
        """Valide que la fenêtre du navigateur est bien positionnée sur l'écran principal"""
        try:
            # Obtenir la position et la taille de la fenêtre
            window_position = self.driver.execute_script("return {x: window.screenX, y: window.screenY};")
            window_size = self.driver.execute_script("return {width: window.outerWidth, height: window.outerHeight};")
            
            # Vérifier que la fenêtre ne déborde pas sur un second écran
            # (en supposant que l'écran principal fait au moins 1920x1080)
            if window_position['x'] < 0 or window_position['y'] < 0:
                self.logger.warning(f"Fenêtre positionnée en dehors de l'écran principal: x={window_position['x']}, y={window_position['y']}")
                return False
            
            # Vérifier que la fenêtre ne déborde pas à droite ou en bas
            if (window_position['x'] + window_size['width'] > 1920 or 
                window_position['y'] + window_size['height'] > 1080):
                self.logger.warning(f"Fenêtre déborde de l'écran principal: position=({window_position['x']}, {window_position['y']}), taille=({window_size['width']}, {window_size['height']})")
                return False
                
            return True
        except Exception as e:
            self.logger.warning(f"Impossible de valider la position de la fenêtre: {e}")
            return True  # On continue même si on ne peut pas valider

    def _scroll_to_element(self, element):
        """Scroll vers l'élément pour s'assurer qu'il est visible dans le viewport"""
        try:
            # Utiliser scrollIntoView pour centrer l'élément dans le viewport
            self.driver.execute_script("""
                arguments[0].scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'center'
                });
            """, element)
            
            # Attendre un peu pour que le scroll se termine
            time.sleep(0.3)
            
            # Vérifier que l'élément est bien visible
            is_visible = self.driver.execute_script("""
                var element = arguments[0];
                var rect = element.getBoundingClientRect();
                var viewportHeight = window.innerHeight;
                var viewportWidth = window.innerWidth;
                
                return rect.top >= 0 && 
                       rect.left >= 0 && 
                       rect.bottom <= viewportHeight && 
                       rect.right <= viewportWidth;
            """, element)
            
            if not is_visible:
                self.logger.warning("L'élément n'est pas entièrement visible après le scroll")
            
            return True
        except Exception as e:
            self.logger.warning(f"Erreur lors du scroll vers l'élément: {e}")
            return False

    def _is_element_in_viewport(self, element):
        """Vérifie si l'élément est visible dans le viewport"""
        try:
            return self.driver.execute_script("""
                var element = arguments[0];
                var rect = element.getBoundingClientRect();
                var viewportHeight = window.innerHeight;
                var viewportWidth = window.innerWidth;
                
                return rect.top >= 0 && 
                       rect.left >= 0 && 
                       rect.bottom <= viewportHeight && 
                       rect.right <= viewportWidth;
            """, element)
        except Exception as e:
            self.logger.warning(f"Impossible de vérifier la visibilité de l'élément: {e}")
            return False

    def _get_viewport_screenshot(self):
        """Capture d'écran du viewport visible uniquement"""
        try:
            # Prendre une capture d'écran du viewport visible
            screenshot = self.driver.get_screenshot_as_png()
            return screenshot
        except Exception as e:
            self.logger.warning(f"Erreur lors de la capture du viewport: {e}")
            return self.driver.get_screenshot_as_png()

    def _take_screenshots(self, element, index):
        try:
            # Vérifier d'abord si l'élément est vraiment focusable
            if not self._is_element_focusable(element):
                self.logger.info(f"L'élément {index} n'est pas focusable, pas de capture d'écran")
                return None, None
            
            # Créer le dossier pour les captures d'écran si nécessaire
            os.makedirs('reports/focus_screenshots', exist_ok=True)
            
            # Valider la position de la fenêtre
            if not self._validate_window_position():
                self.logger.warning(f"Position de fenêtre invalide détectée pour la capture {index}")
            
            # Vérifier que l'élément est toujours valide
            if self._is_element_stale(element):
                log_with_step(self.logger, logging.WARNING, "TABULATION", f"L'élément n'est plus valide pour la capture {index}")
                return None, None
            
            # S'assurer que l'élément est visible dans le viewport
            if not self._is_element_in_viewport(element):
                self.logger.info(f"L'élément n'est pas visible, scroll vers l'élément pour la capture {index}")
                self._scroll_to_element(element)
            
            # Première capture immédiate (viewport visible)
            screenshot1 = self._get_viewport_screenshot()
            highlighted_img1 = self._highlight_element(element, screenshot1)
            filename1 = f"reports/focus_screenshots/focus_{index:03d}_1.png"
            highlighted_img1.save(filename1)
            
            # Attendre le délai configuré si activé
            if self.tab_delay > 0:
                log_with_step(self.logger, logging.INFO, "TABULATION", f"Attente de {self.tab_delay} seconde(s) avant la seconde capture...")
                time.sleep(self.tab_delay)
            
            # Vérifier à nouveau que l'élément est toujours valide
            if self._is_element_stale(element):
                log_with_step(self.logger, logging.WARNING, "TABULATION", f"L'élément n'est plus valide pour la seconde capture {index}")
                return filename1, None
            
            # S'assurer que l'élément est toujours visible pour la seconde capture
            if not self._is_element_in_viewport(element):
                self._scroll_to_element(element)
            
            # Seconde capture après le délai (viewport visible)
            screenshot2 = self._get_viewport_screenshot()
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

    def _is_element_focusable(self, element):
        """Vérifie si un élément est vraiment focusable (pas juste tabbable)"""
        try:
            # Vérifier si l'élément est visible et interactif
            is_visible = self.driver.execute_script("""
                var element = arguments[0];
                var rect = element.getBoundingClientRect();
                var style = window.getComputedStyle(element);
                return !(style.display === 'none' || 
                        style.visibility === 'hidden' || 
                        rect.width === 0 || 
                        rect.height === 0);
            """, element)
            
            if not is_visible:
                return False
            
            # Vérifier si l'élément est interactif
            is_interactive = self.driver.execute_script("""
                var element = arguments[0];
                var tag = element.tagName.toLowerCase();
                var tabIndex = element.tabIndex;
                var disabled = element.disabled;
                
                // Éléments naturellement focusables
                if (['a', 'button', 'input', 'select', 'textarea'].includes(tag)) {
                    return !disabled;
                }
                
                // Éléments avec tabindex >= 0
                if (tabIndex >= 0) {
                    return !disabled;
                }
                
                // Éléments avec role interactif
                var role = element.getAttribute('role');
                var interactiveRoles = ['button', 'link', 'menuitem', 'tab', 'option', 
                                      'checkbox', 'radio', 'textbox', 'combobox', 
                                      'slider', 'spinbutton'];
                if (interactiveRoles.includes(role)) {
                    return !disabled;
                }
                
                return false;
            """, element)
            
            return is_interactive
            
        except Exception as e:
            self.logger.warning(f"Erreur lors de la vérification de la focusabilité: {e}")
            return False

    def _get_element_identifier(self, element):
        """Génère un identifiant unique pour un élément basé sur ses propriétés"""
        try:
            # Obtenir les propriétés de l'élément
            tag = element.tag_name
            text = element.text.strip() or ""
            href = element.get_attribute("href") or ""
            id_attr = element.get_attribute("id") or ""
            class_attr = element.get_attribute("class") or ""
            type_attr = element.get_attribute("type") or ""
            
            # Créer un identifiant basé sur les propriétés les plus stables
            identifier_parts = [tag]
            
            if id_attr:
                identifier_parts.append(f"id={id_attr}")
            elif text:
                identifier_parts.append(f"text={text[:50]}")  # Limiter la longueur
            elif href:
                identifier_parts.append(f"href={href[:50]}")
            elif class_attr:
                identifier_parts.append(f"class={class_attr[:30]}")
            elif type_attr:
                identifier_parts.append(f"type={type_attr}")
            
            # Ajouter la position pour différencier les éléments similaires
            try:
                rect = self.driver.execute_script("""
                    var element = arguments[0];
                    var rect = element.getBoundingClientRect();
                    return Math.round(rect.left) + ',' + Math.round(rect.top);
                """, element)
                identifier_parts.append(f"pos={rect}")
            except:
                pass
            
            return "|".join(identifier_parts)
        except Exception as e:
            self.logger.warning(f"Erreur lors de la génération de l'identifiant: {e}")
            return f"unknown_{hash(str(element))}"

    def run(self):
        self.logger.info("\nSimulation de navigation réelle au clavier...")
        self.logger.info("La navigation s'arrêtera automatiquement lors de la détection d'un cycle (retour sur un élément déjà visité)")
        try:
            # Vérifier que le driver est valide
            if not self.driver:
                raise Exception("Le driver n'est pas initialisé")
            
            elements_reached = []
            visited_elements = set()  # Ensemble pour stocker les identifiants des éléments visités
            
            # Attendre que la page soit complètement chargée
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
            except Exception as e:
                log_with_step(self.logger, logging.WARNING, "TABULATION", f"Erreur lors de l'attente du chargement de la page: {str(e)}")
            
            # Attendre un peu plus pour le JavaScript
            time.sleep(2)
            
            for i in range(self.max_screenshots):  # Limite configurable
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
                    
                    # Vérifier si l'élément est vraiment focusable avant de continuer
                    if not self._is_element_focusable(active):
                        self.logger.info(f"L'élément {i+1} n'est pas focusable, passage au suivant")
                        continue
                    
                    # Générer un identifiant unique pour l'élément actif
                    element_id = self._get_element_identifier(active)
                    
                    # Vérifier si on a déjà visité cet élément (détection de cycle)
                    if element_id in visited_elements:
                        self.logger.info(f"Cycle détecté ! Retour sur l'élément déjà visité: {element_id}")
                        self.logger.info(f"Navigation terminée après {i+1} tabulations (cycle détecté)")
                        break
                    
                    # Ajouter l'élément à la liste des éléments visités
                    visited_elements.add(element_id)
                    
                    # Obtenir les informations de l'élément
                    tag = active.tag_name
                    text = active.text.strip() or active.get_attribute("alt") or active.get_attribute("title")
                    href = active.get_attribute("href")
                    
                    # Obtenir les coordonnées de l'élément pour le débogage
                    try:
                        location = active.location
                        size = active.size
                        self.logger.debug(f"Coordonnées Selenium - x: {location['x']}, y: {location['y']}, w: {size['width']}, h: {size['height']}")
                        
                        # Obtenir aussi les coordonnées via getBoundingClientRect
                        rect = self.driver.execute_script("""
                            var element = arguments[0];
                            var rect = element.getBoundingClientRect();
                            return {
                                x: Math.round(rect.left),
                                y: Math.round(rect.top),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height)
                            };
                        """, active)
                        self.logger.debug(f"Coordonnées getBoundingClientRect - x: {rect['x']}, y: {rect['y']}, w: {rect['width']}, h: {rect['height']}")
                    except Exception as e:
                        self.logger.debug(f"Impossible d'obtenir les coordonnées: {e}")
                    
                    # Prendre les captures d'écran avant de logger les informations
                    filename1, filename2 = self._take_screenshots(active, i+1)
                    
                    # Créer l'objet de données complet pour la liaison avec l'analyse DOM
                    element_data = {
                        'tab_index': i + 1,
                        'tag': tag,
                        'text': text,
                        'href': href,
                        'xpath': xpath,  # Identifiant unique principal
                        'css_selector': css_selector,  # Identifiant unique secondaire
                        'accessible_name': accessible_name,
                        'aria_attributes': aria_attributes,
                        'basic_attributes': basic_attributes,
                        'screenshots': {
                            'immediate': filename1,
                            'delayed': filename2
                        },
                        'position': {
                            'x': active.location['x'] if active.location else 0,
                            'y': active.location['y'] if active.location else 0,
                            'width': active.size['width'] if active.size else 0,
                            'height': active.size['height'] if active.size else 0
                        },
                        'is_visible': active.is_displayed() if hasattr(active, 'is_displayed') else False,
                        'is_enabled': active.is_enabled() if hasattr(active, 'is_enabled') else False,
                        'timestamp': time.time()
                    }
                    
                    # Ajouter aux résultats
                    self.tab_results.append(element_data)
                    
                    # Logger les informations de base
                    log_with_step(self.logger, logging.INFO, "TABULATION", f"Focus {i+1}: {tag}, texte: {text}, XPath: {xpath}")
                    
                    # Logger le nom accessible
                    if accessible_name['name']:
                        log_with_step(self.logger, logging.INFO, "TABULATION", f"Nom accessible: {accessible_name['name']} (source: {accessible_name['source']})")
                    else:
                        log_with_step(self.logger, logging.WARNING, "TABULATION", "Aucun nom accessible détecté")
                    
                    # Logger les attributs ARIA importants
                    important_aria = []
                    for attr in ['role', 'aria-label', 'aria-labelledby', 'aria-describedby', 'aria-hidden']:
                        if attr in aria_attributes:
                            important_aria.append(f"{attr}={aria_attributes[attr]}")
                    
                    if important_aria:
                        log_with_step(self.logger, logging.INFO, "TABULATION", f"Attributs ARIA: {', '.join(important_aria)}")
                    
                    # Logger les captures d'écran
                    if filename1:
                        log_with_step(self.logger, logging.INFO, "TABULATION", f"Capture immédiate: {filename1}")
                    if filename2:
                        log_with_step(self.logger, logging.INFO, "TABULATION", f"Capture après délai: {filename2}")
                    
                except Exception as e:
                    log_with_step(self.logger, logging.ERROR, "TABULATION", f"Erreur lors de la tabulation {i+1}: {str(e)}")
                    # Si l'erreur est liée au driver, on arrête la boucle
                    if "NoneType" in str(e):
                        log_with_step(self.logger, logging.ERROR, "TABULATION", "Le driver n'est plus valide, arrêt de l'analyse")
                        break
                    continue
            
            # Message de fin de navigation
            if len(visited_elements) > 0:
                self.logger.info(f"Navigation terminée. {len(visited_elements)} éléments uniques visités.")
            else:
                self.logger.warning("Aucun élément focusable trouvé sur la page.")
                
            return elements_reached
            
        except Exception as e:
            log_with_step(self.logger, logging.ERROR, "TABULATION", f"Erreur lors de la simulation de navigation: {str(e)}")
            return []

    def _generate_tab_reports(self):
        """Génère les rapports CSV et JSON pour la navigation tabulaire"""
        try:
            # Créer le dossier reports s'il n'existe pas
            os.makedirs('reports', exist_ok=True)
            
            # Générer le rapport CSV
            csv_filename = 'rapport_analyse_tab.csv'
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'tab_index', 'tag', 'text', 'href', 'xpath', 'css_selector',
                    'accessible_name', 'accessible_name_source', 'accessible_name_priority',
                    'role', 'aria_label', 'aria_labelledby', 'aria_describedby', 'aria_hidden',
                    'id', 'class', 'title', 'alt', 'type', 'value', 'placeholder', 'tabindex',
                    'position_x', 'position_y', 'position_width', 'position_height',
                    'is_visible', 'is_enabled', 'screenshot_immediate', 'screenshot_delayed'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in self.tab_results:
                    row = {
                        'tab_index': result['tab_index'],
                        'tag': result['tag'],
                        'text': result['text'],
                        'href': result['href'],
                        'xpath': result['xpath'],
                        'css_selector': result['css_selector'],
                        'accessible_name': result['accessible_name']['name'],
                        'accessible_name_source': result['accessible_name']['source'],
                        'accessible_name_priority': result['accessible_name']['priority'],
                        'role': result['aria_attributes'].get('role', ''),
                        'aria_label': result['aria_attributes'].get('aria-label', ''),
                        'aria_labelledby': result['aria_attributes'].get('aria-labelledby', ''),
                        'aria_describedby': result['aria_attributes'].get('aria-describedby', ''),
                        'aria_hidden': result['aria_attributes'].get('aria-hidden', ''),
                        'id': result['basic_attributes']['id'],
                        'class': result['basic_attributes']['class'],
                        'title': result['basic_attributes']['title'],
                        'alt': result['basic_attributes']['alt'],
                        'type': result['basic_attributes']['type'],
                        'value': result['basic_attributes']['value'],
                        'placeholder': result['basic_attributes']['placeholder'],
                        'tabindex': result['basic_attributes']['tabindex'],
                        'position_x': result['position']['x'],
                        'position_y': result['position']['y'],
                        'position_width': result['position']['width'],
                        'position_height': result['position']['height'],
                        'is_visible': result['is_visible'],
                        'is_enabled': result['is_enabled'],
                        'screenshot_immediate': result['screenshots']['immediate'],
                        'screenshot_delayed': result['screenshots']['delayed']
                    }
                    writer.writerow(row)
            
            # Générer le rapport JSON
            json_filename = 'rapport_analyse_tab.json'
            with open(json_filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(self.tab_results, jsonfile, indent=2, ensure_ascii=False)
            
            log_with_step(self.logger, logging.INFO, "TABULATION", f"Rapport CSV généré: {csv_filename}")
            log_with_step(self.logger, logging.INFO, "TABULATION", f"Rapport JSON généré: {json_filename}")
            
        except Exception as e:
            log_with_step(self.logger, logging.ERROR, "TABULATION", f"Erreur lors de la génération des rapports: {str(e)}")

    def get_results_for_dom_linking(self):
        """Retourne les résultats formatés pour la liaison avec l'analyse DOM"""
        return {
            'tabulation_elements': self.tab_results,
            'summary': {
                'total_elements_reached': len(self.tab_results),
                'elements_with_accessible_names': len([r for r in self.tab_results if r['accessible_name']['name']]),
                'elements_with_aria': len([r for r in self.tab_results if r['aria_attributes']]),
                'visible_elements': len([r for r in self.tab_results if r['is_visible']]),
                'enabled_elements': len([r for r in self.tab_results if r['is_enabled']])
            }
        }
