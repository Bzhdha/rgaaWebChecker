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
    def __init__(self, driver, logger, tab_delay=0.0):
        self.driver = driver
        self.logger = logger
        self.tab_results = []
        self.tab_delay = tab_delay  # Délai en secondes entre les snapshots

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
            
            # Attendre le délai configuré si activé
            if self.tab_delay > 0:
                log_with_step(self.logger, logging.INFO, "TABULATION", f"Attente de {self.tab_delay} seconde(s) avant la seconde capture...")
                time.sleep(self.tab_delay)
            
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

    def _get_element_xpath(self, element):
        """Génère le XPath unique de l'élément pour la liaison avec l'analyse DOM"""
        try:
            # Utiliser JavaScript pour générer un XPath unique
            xpath = self.driver.execute_script("""
                function getXPath(element) {
                    if (element.id !== '') {
                        return 'id("' + element.id + '")';
                    }
                    if (element === document.body) {
                        return element.tagName.toLowerCase();
                    }
                    
                    var ix = 0;
                    var siblings = element.parentNode.childNodes;
                    
                    for (var i = 0; i < siblings.length; i++) {
                        var sibling = siblings[i];
                        if (sibling === element) {
                            return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                        }
                        if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                            ix++;
                        }
                    }
                }
                return getXPath(arguments[0]);
            """, element)
            return xpath
        except:
            return "unknown"

    def _get_element_selector(self, element):
        """Génère un sélecteur CSS unique de l'élément"""
        try:
            selector = self.driver.execute_script("""
                function getSelector(element) {
                    if (element.id) {
                        return '#' + element.id;
                    }
                    if (element.className) {
                        var classes = element.className.split(' ').filter(function(c) { return c.length > 0; });
                        if (classes.length > 0) {
                            return element.tagName.toLowerCase() + '.' + classes.join('.');
                        }
                    }
                    return element.tagName.toLowerCase();
                }
                return getSelector(arguments[0]);
            """, element)
            return selector
        except:
            return "unknown"

    def _get_accessible_name(self, element):
        """Détermine le nom accessible de l'élément selon l'ordre de priorité"""
        try:
            # 1️⃣ aria-labelledby (priorité absolue)
            aria_labelledby = element.get_attribute('aria-labelledby')
            if aria_labelledby:
                try:
                    labelledby_ids = aria_labelledby.split()
                    accessible_name = ""
                    for label_id in labelledby_ids:
                        label_element = self.driver.find_element("id", label_id)
                        if label_element:
                            label_text = label_element.text.strip()
                            if label_text:
                                accessible_name += label_text + " "
                    if accessible_name.strip():
                        return {
                            'name': accessible_name.strip(),
                            'source': 'aria-labelledby',
                            'priority': 1
                        }
                except:
                    pass
            
            # 2️⃣ aria-label
            aria_label = element.get_attribute('aria-label')
            if aria_label and aria_label.strip():
                return {
                    'name': aria_label.strip(),
                    'source': 'aria-label',
                    'priority': 2
                }
            
            # 3️⃣ Contenu textuel
            text_content = element.text.strip() if element.text else ''
            if text_content:
                return {
                    'name': text_content,
                    'source': 'text_content',
                    'priority': 3
                }
            
            # 4️⃣ Attribut alt (spécifique aux images)
            if element.tag_name.lower() == 'img':
                alt_text = element.get_attribute('alt')
                if alt_text and alt_text.strip():
                    return {
                        'name': alt_text.strip(),
                        'source': 'alt',
                        'priority': 4
                    }
            
            # 5️⃣ Nom accessible hérité d'une image enfant (cas des liens avec logo)
            if element.tag_name.lower() == 'a':
                try:
                    img = element.find_element("tag name", 'img')
                    if img:
                        alt_text = img.get_attribute('alt')
                        if alt_text and alt_text.strip():
                            return {
                                'name': alt_text.strip(),
                                'source': 'alt (img enfant)',
                                'priority': 4
                            }
                except Exception:
                    pass
            
            # Aucun nom accessible trouvé
            return {
                'name': '',
                'source': 'none',
                'priority': 0
            }
            
        except Exception as e:
            log_with_step(self.logger, logging.WARNING, "TABULATION", f"Erreur lors de la détermination du nom accessible : {str(e)}")
            return {
                'name': '',
                'source': 'error',
                'priority': 0
            }

    def run(self):
        log_with_step(self.logger, logging.INFO, "TABULATION", "\nSimulation de navigation réelle au clavier...")
        try:
            # Vérifier que le driver est valide
            if not self.driver:
                raise Exception("Le driver n'est pas initialisé")
            
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
                    
                    # Obtenir les informations de base de l'élément
                    tag = active.tag_name
                    text = active.text.strip() or active.get_attribute("alt") or active.get_attribute("title")
                    href = active.get_attribute("href")
                    
                    # Générer les identifiants uniques pour la liaison avec l'analyse DOM
                    xpath = self._get_element_xpath(active)
                    css_selector = self._get_element_selector(active)
                    
                    # Obtenir le nom accessible
                    accessible_name = self._get_accessible_name(active)
                    
                    # Récupérer les informations ARIA complètes
                    aria_attributes = {}
                    aria_attrs_list = [
                        'role', 'aria-label', 'aria-labelledby', 'aria-describedby', 'aria-hidden',
                        'aria-expanded', 'aria-controls', 'aria-current', 'aria-pressed', 'aria-checked',
                        'aria-selected', 'aria-disabled', 'aria-required', 'aria-invalid', 'aria-live',
                        'aria-atomic', 'aria-relevant', 'aria-busy', 'aria-level', 'aria-posinset',
                        'aria-setsize', 'aria-valuemin', 'aria-valuemax', 'aria-valuenow', 'aria-valuetext',
                        'aria-haspopup', 'aria-multiline', 'aria-multiselectable', 'aria-orientation',
                        'aria-placeholder', 'aria-roledescription', 'aria-keyshortcuts', 'aria-details',
                        'aria-errormessage', 'aria-flowto', 'aria-owns'
                    ]
                    
                    for attr in aria_attrs_list:
                        value = active.get_attribute(attr)
                        if value:
                            aria_attributes[attr] = value
                    
                    # Récupérer les attributs de base
                    basic_attributes = {
                        'id': active.get_attribute('id'),
                        'class': active.get_attribute('class'),
                        'title': active.get_attribute('title'),
                        'alt': active.get_attribute('alt'),
                        'type': active.get_attribute('type'),
                        'value': active.get_attribute('value'),
                        'placeholder': active.get_attribute('placeholder'),
                        'tabindex': active.get_attribute('tabindex')
                    }
                    
                    # Prendre les captures d'écran
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
            
            # Générer les rapports de navigation tabulaire
            self._generate_tab_reports()
            
            return self.tab_results
            
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
