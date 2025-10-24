from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import os
from PIL import Image, ImageDraw
import io
import time
from selenium.webdriver.support.ui import WebDriverWait
from utils.element_identifier import ElementIdentifier

class UnifiedTabNavigator:
    def __init__(self, driver, logger, max_screenshots=50, shared_data=None):
        self.driver = driver
        self.logger = logger
        self.max_screenshots = max_screenshots
        self.shared_data = shared_data
        self.aria_analysis_results = []

    def _get_aria_data_for_element(self, element):
        """Récupère les données ARIA d'un élément depuis les données partagées"""
        if not self.shared_data:
            return {}
            
        try:
            # Utiliser l'identifiant unifié
            element_id = ElementIdentifier.generate_identifier(element, self.driver, include_position=True)
            
            # Essayer de récupérer les données avec l'identifiant complet
            aria_data = self.shared_data.get_aria_data(element_id)
            
            if aria_data:
                self.logger.debug(f"Données ARIA trouvées avec identifiant complet: {element_id}")
                return aria_data
            
            # Si pas trouvé, essayer avec l'identifiant sans position
            element_id_no_pos = ElementIdentifier.generate_identifier(element, self.driver, include_position=False)
            aria_data = self.shared_data.get_aria_data(element_id_no_pos)
            
            if aria_data:
                self.logger.debug(f"Données ARIA trouvées avec identifiant sans position: {element_id_no_pos}")
                return aria_data
            
            # Si toujours pas trouvé, essayer de trouver une correspondance
            available_identifiers = list(self.shared_data.aria_data.keys())
            matching_id = ElementIdentifier.find_matching_identifier(element_id, available_identifiers)
            
            if matching_id:
                aria_data = self.shared_data.get_aria_data(matching_id)
                self.logger.debug(f"Données ARIA trouvées avec correspondance: {matching_id}")
                return aria_data
            
            self.logger.debug(f"Aucune donnée ARIA trouvée pour l'élément: {element_id}")
            return {}
                
        except Exception as e:
            self.logger.warning(f"Erreur lors de la récupération des données ARIA: {e}")
            return {}

    def _analyze_element_with_aria(self, element, index):
        """Analyse un élément avec ses données ARIA"""
        try:
            # Récupérer les données ARIA
            aria_data = self._get_aria_data_for_element(element)
            
            # Informations de base de l'élément
            tag = element.tag_name
            text = element.text.strip() or element.get_attribute("alt") or element.get_attribute("title")
            href = element.get_attribute("href")
            
            # Utiliser l'identifiant unifié
            element_id = ElementIdentifier.generate_identifier(element, self.driver, include_position=True)
            
            # Analyser les propriétés ARIA
            aria_analysis = {
                'element_id': element_id,
                'tag': tag,
                'text': text,
                'href': href,
                'aria_properties': aria_data,
                'focus_order': index + 1,
                'timestamp': time.time()
            }
            
            # Analyser les propriétés ARIA spécifiques
            if aria_data:
                # Vérifier les propriétés d'état
                aria_analysis['has_aria_label'] = bool(aria_data.get('Aria-label', '') != 'non défini')
                aria_analysis['has_aria_describedby'] = bool(aria_data.get('Aria-describedby', '') != 'non défini')
                aria_analysis['has_aria_labelledby'] = bool(aria_data.get('Aria-labelledby', '') != 'non défini')
                aria_analysis['is_aria_hidden'] = aria_data.get('Aria-hidden', '') == 'true'
                aria_analysis['is_aria_expanded'] = aria_data.get('Aria-expanded', '') == 'true'
                aria_analysis['is_aria_selected'] = aria_data.get('Aria-selected', '') == 'true'
                aria_analysis['is_aria_checked'] = aria_data.get('Aria-checked', '') == 'true'
                aria_analysis['is_aria_pressed'] = aria_data.get('Aria-pressed', '') == 'true'
                aria_analysis['is_aria_disabled'] = aria_data.get('Aria-disabled', '') == 'true'
                aria_analysis['is_aria_required'] = aria_data.get('Aria-required', '') == 'true'
                aria_analysis['is_aria_readonly'] = aria_data.get('Aria-readonly', '') == 'true'
                
                # Rôle ARIA
                aria_analysis['aria_role'] = aria_data.get('Rôle', 'non défini')
                
                # Propriétés de relation
                aria_analysis['aria_controls'] = aria_data.get('Aria-controls', 'non défini')
                aria_analysis['aria_owns'] = aria_data.get('Aria-owns', 'non défini')
                aria_analysis['aria_flowto'] = aria_data.get('Aria-flowto', 'non défini')
                
                # Propriétés de région
                aria_analysis['aria_live'] = aria_data.get('Aria-live', 'non défini')
                aria_analysis['aria_atomic'] = aria_data.get('Aria-atomic', 'non défini')
                aria_analysis['aria_relevant'] = aria_data.get('Aria-relevant', 'non défini')
                
                # Propriétés de valeur
                aria_analysis['aria_valuemin'] = aria_data.get('Aria-valuemin', 'non défini')
                aria_analysis['aria_valuemax'] = aria_data.get('Aria-valuemax', 'non défini')
                aria_analysis['aria_valuenow'] = aria_data.get('Aria-valuenow', 'non défini')
                aria_analysis['aria_valuetext'] = aria_data.get('Aria-valuetext', 'non défini')
                
                # Autres propriétés importantes
                aria_analysis['aria_placeholder'] = aria_data.get('Aria-placeholder', 'non défini')
                aria_analysis['aria_roledescription'] = aria_data.get('Aria-roledescription', 'non défini')
                aria_analysis['aria_keyshortcuts'] = aria_data.get('Aria-keyshortcuts', 'non défini')
                aria_analysis['aria_details'] = aria_data.get('Aria-details', 'non défini')
                aria_analysis['aria_errormessage'] = aria_data.get('Aria-errormessage', 'non défini')
                
            else:
                # Aucune donnée ARIA disponible
                aria_analysis['has_aria_label'] = False
                aria_analysis['has_aria_describedby'] = False
                aria_analysis['has_aria_labelledby'] = False
                aria_analysis['is_aria_hidden'] = False
                aria_analysis['is_aria_expanded'] = False
                aria_analysis['is_aria_selected'] = False
                aria_analysis['is_aria_checked'] = False
                aria_analysis['is_aria_pressed'] = False
                aria_analysis['is_aria_disabled'] = False
                aria_analysis['is_aria_required'] = False
                aria_analysis['is_aria_readonly'] = False
                aria_analysis['aria_role'] = 'non défini'
                aria_analysis['aria_controls'] = 'non défini'
                aria_analysis['aria_owns'] = 'non défini'
                aria_analysis['aria_flowto'] = 'non défini'
                aria_analysis['aria_live'] = 'non défini'
                aria_analysis['aria_atomic'] = 'non défini'
                aria_analysis['aria_relevant'] = 'non défini'
                aria_analysis['aria_valuemin'] = 'non défini'
                aria_analysis['aria_valuemax'] = 'non défini'
                aria_analysis['aria_valuenow'] = 'non défini'
                aria_analysis['aria_valuetext'] = 'non défini'
                aria_analysis['aria_placeholder'] = 'non défini'
                aria_analysis['aria_roledescription'] = 'non défini'
                aria_analysis['aria_keyshortcuts'] = 'non défini'
                aria_analysis['aria_details'] = 'non défini'
                aria_analysis['aria_errormessage'] = 'non défini'
            
            # Ajouter l'analyse à la liste des résultats
            self.aria_analysis_results.append(aria_analysis)
            
            return aria_analysis
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse ARIA de l'élément: {e}")
            return None

    def _log_aria_analysis(self, aria_analysis):
        """Affiche l'analyse ARIA dans les logs"""
        if not aria_analysis:
            return
            
        self.logger.info(f"=== Analyse ARIA pour l'élément {aria_analysis['focus_order']} ===")
        self.logger.info(f"Identifiant: {aria_analysis['element_id']}")
        self.logger.info(f"Tag: {aria_analysis['tag']}")
        self.logger.info(f"Texte: {aria_analysis['text']}")
        self.logger.info(f"Rôle ARIA: {aria_analysis['aria_role']}")
        
        # Afficher les propriétés ARIA importantes
        if aria_analysis['has_aria_label']:
            self.logger.info(f"✓ Aria-label: {aria_analysis['aria_properties'].get('Aria-label', '')}")
        if aria_analysis['has_aria_describedby']:
            self.logger.info(f"✓ Aria-describedby: {aria_analysis['aria_properties'].get('Aria-describedby', '')}")
        if aria_analysis['has_aria_labelledby']:
            self.logger.info(f"✓ Aria-labelledby: {aria_analysis['aria_properties'].get('Aria-labelledby', '')}")
            
        # Afficher les états ARIA
        states = []
        if aria_analysis['is_aria_expanded']:
            states.append("expanded")
        if aria_analysis['is_aria_selected']:
            states.append("selected")
        if aria_analysis['is_aria_checked']:
            states.append("checked")
        if aria_analysis['is_aria_pressed']:
            states.append("pressed")
        if aria_analysis['is_aria_disabled']:
            states.append("disabled")
        if aria_analysis['is_aria_required']:
            states.append("required")
        if aria_analysis['is_aria_readonly']:
            states.append("readonly")
        if aria_analysis['is_aria_hidden']:
            states.append("hidden")
            
        if states:
            self.logger.info(f"États ARIA: {', '.join(states)}")
        
        # Afficher les relations ARIA
        relations = []
        if aria_analysis['aria_controls'] != 'non défini':
            relations.append(f"controls={aria_analysis['aria_controls']}")
        if aria_analysis['aria_owns'] != 'non défini':
            relations.append(f"owns={aria_analysis['aria_owns']}")
        if aria_analysis['aria_flowto'] != 'non défini':
            relations.append(f"flowto={aria_analysis['aria_flowto']}")
            
        if relations:
            self.logger.info(f"Relations ARIA: {', '.join(relations)}")
        
        # Afficher les propriétés de région
        if aria_analysis['aria_live'] != 'non défini':
            self.logger.info(f"Région live: {aria_analysis['aria_live']}")
        
        # Afficher les propriétés de valeur
        if aria_analysis['aria_valuenow'] != 'non défini':
            self.logger.info(f"Valeur: {aria_analysis['aria_valuenow']} (min: {aria_analysis['aria_valuemin']}, max: {aria_analysis['aria_valuemax']})")
        
        self.logger.info("=" * 50)

    def run(self):
        """Exécute la navigation tabulaire avec analyse ARIA"""
        self.logger.info("\nSimulation de navigation réelle au clavier avec analyse ARIA unifiée...")
        self.logger.info("La navigation s'arrêtera automatiquement lors de la détection d'un cycle (retour sur un élément déjà visité)")
        
        try:
            # Vérifier que le driver est valide
            if not self.driver:
                raise Exception("Le driver n'est pas initialisé")
            
            elements_reached = []
            visited_elements = set()
            
            # Attendre que la page soit complètement chargée
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
            except Exception as e:
                self.logger.warning(f"Erreur lors de l'attente du chargement de la page: {str(e)}")
            
            # Attendre un peu plus pour le JavaScript
            time.sleep(2)
            
            for i in range(self.max_screenshots):
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
                    
                    # Vérifier si l'élément est vraiment focusable avant de continuer
                    if not self._is_element_focusable(active):
                        self.logger.info(f"L'élément {i+1} n'est pas focusable, passage au suivant")
                        continue
                    
                    # Utiliser l'identifiant unifié pour la détection de cycle
                    element_id = ElementIdentifier.generate_identifier(active, self.driver, include_position=True)
                    
                    # Vérifier si on a déjà visité cet élément (détection de cycle)
                    if element_id in visited_elements:
                        self.logger.info(f"Cycle détecté ! Retour sur l'élément déjà visité: {element_id}")
                        self.logger.info(f"Navigation terminée après {i+1} tabulations (cycle détecté)")
                        break
                    
                    # Ajouter l'élément à la liste des éléments visités
                    visited_elements.add(element_id)
                    
                    # Analyser l'élément avec ses données ARIA
                    aria_analysis = self._analyze_element_with_aria(active, i)
                    
                    # Afficher l'analyse ARIA dans les logs
                    self._log_aria_analysis(aria_analysis)
                    
                    # Prendre les captures d'écran
                    filename1, filename2 = self._take_screenshots(active, i+1)
                    
                    # Logger les informations avec les noms des fichiers
                    self.logger.info(f"Focus sur: {active.tag_name}, texte: {active.text.strip()}")
                    if filename1:
                        self.logger.info(f"Capture immédiate: {filename1}")
                    if filename2:
                        self.logger.info(f"Capture après délai: {filename2}")
                    
                    elements_reached.append((active.tag_name, active.text.strip(), active.get_attribute("href")))
                    
                except Exception as e:
                    self.logger.error(f"Erreur lors de la tabulation {i+1}: {str(e)}")
                    if "NoneType" in str(e):
                        self.logger.error("Le driver n'est plus valide, arrêt de l'analyse")
                        break
                    continue
            
            # Message de fin de navigation
            if len(visited_elements) > 0:
                self.logger.info(f"Navigation terminée. {len(visited_elements)} éléments uniques visités.")
                self.logger.info(f"Analyse ARIA effectuée sur {len(self.aria_analysis_results)} éléments.")
            else:
                self.logger.warning("Aucun élément focusable trouvé sur la page.")
            
            return elements_reached
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la simulation de navigation: {str(e)}")
            return []

    def get_aria_analysis_results(self):
        """Retourne les résultats de l'analyse ARIA"""
        return self.aria_analysis_results

    def generate_aria_report(self):
        """Génère un rapport des données ARIA analysées"""
        if not self.aria_analysis_results:
            self.logger.info("Aucune donnée ARIA à rapporter")
            return
        
        self.logger.info("\n=== RAPPORT D'ANALYSE ARIA UNIFIÉE ===")
        self.logger.info(f"Nombre d'éléments analysés: {len(self.aria_analysis_results)}")
        
        # Statistiques générales
        elements_with_aria = sum(1 for elem in self.aria_analysis_results if elem['aria_properties'])
        elements_without_aria = len(self.aria_analysis_results) - elements_with_aria
        
        self.logger.info(f"Éléments avec propriétés ARIA: {elements_with_aria}")
        self.logger.info(f"Éléments sans propriétés ARIA: {elements_without_aria}")
        
        # Statistiques par type de propriété
        aria_labels = sum(1 for elem in self.aria_analysis_results if elem['has_aria_label'])
        aria_describedby = sum(1 for elem in self.aria_analysis_results if elem['has_aria_describedby'])
        aria_labelledby = sum(1 for elem in self.aria_analysis_results if elem['has_aria_labelledby'])
        
        self.logger.info(f"Éléments avec aria-label: {aria_labels}")
        self.logger.info(f"Éléments avec aria-describedby: {aria_describedby}")
        self.logger.info(f"Éléments avec aria-labelledby: {aria_labelledby}")
        
        # Statistiques des rôles ARIA
        roles = {}
        for elem in self.aria_analysis_results:
            role = elem['aria_role']
            if role != 'non défini':
                roles[role] = roles.get(role, 0) + 1
        
        if roles:
            self.logger.info("Rôles ARIA détectés:")
            for role, count in sorted(roles.items()):
                self.logger.info(f"  {role}: {count} élément(s)")
        
        self.logger.info("=" * 50)

    # Méthodes héritées du TabNavigator original
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

    def _take_screenshots(self, element, index):
        """Prend des captures d'écran de l'élément focusé"""
        try:
            # Vérifier d'abord si l'élément est vraiment focusable
            if not self._is_element_focusable(element):
                self.logger.info(f"L'élément {index} n'est pas focusable, pas de capture d'écran")
                return None, None
            
            # Créer le dossier pour les captures d'écran si nécessaire
            os.makedirs('reports/focus_screenshots', exist_ok=True)
            
            # Première capture immédiate
            screenshot1 = self.driver.get_screenshot_as_png()
            highlighted_img1 = self._highlight_element(element, screenshot1)
            filename1 = f"reports/focus_screenshots/focus_{index:03d}_1.png"
            highlighted_img1.save(filename1)
            
            # Attendre 0.5 seconde pour laisser le temps au contenu de s'afficher
            time.sleep(0.5)
            
            # Seconde capture après le délai
            screenshot2 = self.driver.get_screenshot_as_png()
            highlighted_img2 = self._highlight_element(element, screenshot2)
            filename2 = f"reports/focus_screenshots/focus_{index:03d}_2.png"
            highlighted_img2.save(filename2)
            
            return filename1, filename2
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la capture d'écran {index}: {str(e)}")
            return None, None

    def _highlight_element(self, element, screenshot):
        """Met en évidence l'élément dans la capture d'écran"""
        # Convertir la capture d'écran en image PIL
        img = Image.open(io.BytesIO(screenshot))
        draw = ImageDraw.Draw(img)
        
        # Obtenir les coordonnées de l'élément
        try:
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
            self.logger.warning(f"Erreur lors du calcul des coordonnées: {e}")
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
        draw.rectangle([x1-2, y1-2, x2+2, y2+2], outline='red', width=2)
        draw.rectangle([x1-1, y1-1, x2+1, y2+1], outline='yellow', width=1)
        draw.rectangle([x1, y1, x2, y2], outline='red', width=1)
        
        return img
