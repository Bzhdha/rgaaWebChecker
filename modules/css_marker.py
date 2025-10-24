"""
Module de marquage CSS pour l'analyse d'accessibilité
Permet d'ajouter des balises CSS aux éléments analysés pour faciliter leur identification
"""

import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from utils.log_utils import log_with_step
import logging

class CSSMarker:
    """Gestionnaire de marquage CSS pour les éléments analysés"""
    
    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger
        self.marked_elements = []
        self.css_injected = False
        
    def inject_base_css(self):
        """Injecte les styles CSS de base pour le marquage des éléments"""
        if self.css_injected:
            return
            
        css_styles = """
        <style id="rgaa-analyzer-css">
        /* Styles pour les éléments analysés par RGAA Web Checker */
        
        /* Éléments analysés - marquage général */
        .rgaa-analyzed {
            position: relative !important;
            outline: 2px solid #007cba !important;
            outline-offset: 2px !important;
        }
        
        /* Éléments avec problèmes d'accessibilité */
        .rgaa-issue {
            position: relative !important;
            outline: 2px solid #dc3545 !important;
            outline-offset: 2px !important;
            background-color: rgba(220, 53, 69, 0.1) !important;
        }
        
        /* Éléments conformes */
        .rgaa-compliant {
            position: relative !important;
            outline: 2px solid #28a745 !important;
            outline-offset: 2px !important;
            background-color: rgba(40, 167, 69, 0.1) !important;
        }
        
        /* Éléments en cours d'analyse */
        .rgaa-analyzing {
            position: relative !important;
            outline: 2px solid #ffc107 !important;
            outline-offset: 2px !important;
            background-color: rgba(255, 193, 7, 0.1) !important;
        }
        
        /* Badges d'information */
        .rgaa-badge {
            position: absolute !important;
            top: -8px !important;
            right: -8px !important;
            background: #007cba !important;
            color: white !important;
            font-size: 10px !important;
            font-weight: bold !important;
            padding: 2px 6px !important;
            border-radius: 3px !important;
            z-index: 9999 !important;
            font-family: Arial, sans-serif !important;
            line-height: 1 !important;
            white-space: nowrap !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
        }
        
        /* Badges pour les problèmes */
        .rgaa-badge-issue {
            background: #dc3545 !important;
        }
        
        /* Badges pour les éléments conformes */
        .rgaa-badge-compliant {
            background: #28a745 !important;
        }
        
        /* Badges pour les éléments en cours d'analyse */
        .rgaa-badge-analyzing {
            background: #ffc107 !important;
            color: #000 !important;
        }
        
        /* Tooltips d'information */
        .rgaa-tooltip {
            position: absolute !important;
            bottom: 100% !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            background: #333 !important;
            color: white !important;
            padding: 8px 12px !important;
            border-radius: 4px !important;
            font-size: 12px !important;
            font-family: Arial, sans-serif !important;
            white-space: nowrap !important;
            z-index: 10000 !important;
            opacity: 0 !important;
            transition: opacity 0.3s ease !important;
            pointer-events: none !important;
            max-width: 300px !important;
            white-space: normal !important;
        }
        
        /* Affichage du tooltip au survol */
        .rgaa-analyzed:hover .rgaa-tooltip,
        .rgaa-issue:hover .rgaa-tooltip,
        .rgaa-compliant:hover .rgaa-tooltip {
            opacity: 1 !important;
        }
        
        /* Styles spécifiques par type d'élément */
        .rgaa-heading {
            border-left: 4px solid #007cba !important;
            padding-left: 8px !important;
        }
        
        .rgaa-image {
            border: 2px dashed #007cba !important;
        }
        
        .rgaa-link {
            border-bottom: 2px solid #007cba !important;
        }
        
        .rgaa-button {
            border: 2px solid #007cba !important;
            border-radius: 4px !important;
        }
        
        .rgaa-form {
            border: 2px solid #007cba !important;
            border-radius: 4px !important;
            padding: 8px !important;
        }
        
        /* Animation pour les éléments en cours d'analyse */
        .rgaa-analyzing {
            animation: rgaa-pulse 1.5s infinite !important;
        }
        
        @keyframes rgaa-pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        /* Styles pour les landmarks */
        .rgaa-landmark {
            border: 2px solid #6f42c1 !important;
            border-radius: 4px !important;
            background-color: rgba(111, 66, 193, 0.1) !important;
        }
        
        /* Styles pour les éléments ARIA */
        .rgaa-aria {
            border: 2px solid #fd7e14 !important;
            border-radius: 4px !important;
            background-color: rgba(253, 126, 20, 0.1) !important;
        }
        
        /* Masquer les marquages en mode production */
        .rgaa-production-hide .rgaa-analyzed,
        .rgaa-production-hide .rgaa-issue,
        .rgaa-production-hide .rgaa-compliant,
        .rgaa-production-hide .rgaa-analyzing,
        .rgaa-production-hide .rgaa-badge,
        .rgaa-production-hide .rgaa-tooltip {
            display: none !important;
        }
        </style>
        """
        
        try:
            # Injecter le CSS dans la page
            self.driver.execute_script(f"""
                var style = document.getElementById('rgaa-analyzer-css');
                if (!style) {{
                    var head = document.head || document.getElementsByTagName('head')[0];
                    head.insertAdjacentHTML('beforeend', '{css_styles}');
                }}
            """)
            
            self.css_injected = True
            log_with_step(self.logger, logging.INFO, "CSS", "Styles CSS de marquage injectés avec succès")
            
        except Exception as e:
            log_with_step(self.logger, logging.ERROR, "CSS", f"Erreur lors de l'injection des styles CSS : {str(e)}")
    
    def mark_element(self, element, element_type="analyzed", issues=None, compliant=None, info=None):
        """
        Marque un élément avec les classes CSS appropriées
        
        Args:
            element: L'élément Selenium à marquer
            element_type: Type d'élément (analyzed, heading, image, link, button, form, landmark, aria)
            issues: Liste des problèmes détectés (optionnel)
            compliant: Booléen indiquant si l'élément est conforme (optionnel)
            info: Informations supplémentaires à afficher (optionnel)
        """
        try:
            # S'assurer que les styles CSS sont injectés
            self.inject_base_css()
            
            # Générer un identifiant unique pour l'élément
            element_id = self._generate_element_id(element)
            
            # Déterminer les classes CSS à appliquer
            css_classes = ["rgaa-analyzed"]
            
            if element_type in ["heading", "image", "link", "button", "form", "landmark", "aria"]:
                css_classes.append(f"rgaa-{element_type}")
            
            # Déterminer le statut de conformité
            if issues and len(issues) > 0:
                css_classes.append("rgaa-issue")
                badge_class = "rgaa-badge-issue"
                badge_text = f"⚠️ {len(issues)} problème(s)"
            elif compliant is True:
                css_classes.append("rgaa-compliant")
                badge_class = "rgaa-badge-compliant"
                badge_text = "✅ Conforme"
            else:
                badge_class = "rgaa-badge"
                badge_text = "🔍 Analysé"
            
            # Appliquer les classes CSS
            self.driver.execute_script(f"""
                var element = arguments[0];
                var classes = arguments[1];
                var badgeClass = arguments[2];
                var badgeText = arguments[3];
                var elementId = arguments[4];
                var info = arguments[5];
                
                // Ajouter les classes CSS
                element.classList.add(...classes);
                
                // Créer le badge d'information
                var badge = document.createElement('div');
                badge.className = badgeClass;
                badge.textContent = badgeText;
                badge.setAttribute('data-rgaa-element-id', elementId);
                
                // Créer le tooltip si des informations sont fournies
                if (info) {{
                    var tooltip = document.createElement('div');
                    tooltip.className = 'rgaa-tooltip';
                    tooltip.innerHTML = info;
                    element.appendChild(tooltip);
                }}
                
                // Ajouter le badge à l'élément
                element.appendChild(badge);
                
                // Stocker l'ID de l'élément
                element.setAttribute('data-rgaa-element-id', elementId);
            """, element, css_classes, badge_class, badge_text, element_id, info)
            
            # Enregistrer l'élément marqué
            self.marked_elements.append({
                'element_id': element_id,
                'element_type': element_type,
                'issues': issues or [],
                'compliant': compliant,
                'info': info,
                'timestamp': time.time()
            })
            
            log_with_step(self.logger, logging.DEBUG, "CSS", f"Élément marqué : {element_id} ({element_type})")
            
        except StaleElementReferenceException:
            log_with_step(self.logger, logging.WARNING, "CSS", "Élément devenu obsolète lors du marquage")
        except Exception as e:
            log_with_step(self.logger, logging.ERROR, "CSS", f"Erreur lors du marquage de l'élément : {str(e)}")
    
    def mark_elements_batch(self, elements_data):
        """
        Marque plusieurs éléments en lot pour optimiser les performances
        
        Args:
            elements_data: Liste de dictionnaires contenant les informations des éléments
        """
        try:
            # S'assurer que les styles CSS sont injectés
            self.inject_base_css()
            
            # Préparer les données pour l'injection JavaScript
            js_data = []
            for element_data in elements_data:
                element = element_data['element']
                element_type = element_data.get('type', 'analyzed')
                issues = element_data.get('issues', [])
                compliant = element_data.get('compliant')
                info = element_data.get('info')
                
                element_id = self._generate_element_id(element)
                
                # Déterminer les classes CSS
                css_classes = ["rgaa-analyzed"]
                if element_type in ["heading", "image", "link", "button", "form", "landmark", "aria"]:
                    css_classes.append(f"rgaa-{element_type}")
                
                # Déterminer le badge
                if issues and len(issues) > 0:
                    css_classes.append("rgaa-issue")
                    badge_class = "rgaa-badge-issue"
                    badge_text = f"⚠️ {len(issues)}"
                elif compliant is True:
                    css_classes.append("rgaa-compliant")
                    badge_class = "rgaa-badge-compliant"
                    badge_text = "✅"
                else:
                    badge_class = "rgaa-badge"
                    badge_text = "🔍"
                
                js_data.append({
                    'element': element,
                    'classes': css_classes,
                    'badge_class': badge_class,
                    'badge_text': badge_text,
                    'element_id': element_id,
                    'info': info
                })
            
            # Appliquer le marquage en lot
            self.driver.execute_script("""
                var elementsData = arguments[0];
                
                for (var i = 0; i < elementsData.length; i++) {
                    var data = elementsData[i];
                    var element = data.element;
                    var classes = data.classes;
                    var badgeClass = data.badge_class;
                    var badgeText = data.badge_text;
                    var elementId = data.element_id;
                    var info = data.info;
                    
                    try {
                        // Ajouter les classes CSS
                        element.classList.add(...classes);
                        
                        // Créer le badge
                        var badge = document.createElement('div');
                        badge.className = badgeClass;
                        badge.textContent = badgeText;
                        badge.setAttribute('data-rgaa-element-id', elementId);
                        
                        // Créer le tooltip si nécessaire
                        if (info) {
                            var tooltip = document.createElement('div');
                            tooltip.className = 'rgaa-tooltip';
                            tooltip.innerHTML = info;
                            element.appendChild(tooltip);
                        }
                        
                        // Ajouter le badge
                        element.appendChild(badge);
                        element.setAttribute('data-rgaa-element-id', elementId);
                        
                    } catch (e) {
                        console.warn('Erreur lors du marquage d\'un élément:', e);
                    }
                }
            """, js_data)
            
            # Enregistrer les éléments marqués
            for element_data in elements_data:
                self.marked_elements.append({
                    'element_id': self._generate_element_id(element_data['element']),
                    'element_type': element_data.get('type', 'analyzed'),
                    'issues': element_data.get('issues', []),
                    'compliant': element_data.get('compliant'),
                    'info': element_data.get('info'),
                    'timestamp': time.time()
                })
            
            log_with_step(self.logger, logging.INFO, "CSS", f"Lot de {len(elements_data)} éléments marqués avec succès")
            
        except Exception as e:
            log_with_step(self.logger, logging.ERROR, "CSS", f"Erreur lors du marquage en lot : {str(e)}")
    
    def unmark_element(self, element):
        """Supprime le marquage CSS d'un élément"""
        try:
            self.driver.execute_script("""
                var element = arguments[0];
                
                // Supprimer les classes CSS
                element.classList.remove('rgaa-analyzed', 'rgaa-issue', 'rgaa-compliant', 'rgaa-analyzing');
                element.classList.remove('rgaa-heading', 'rgaa-image', 'rgaa-link', 'rgaa-button', 'rgaa-form', 'rgaa-landmark', 'rgaa-aria');
                
                // Supprimer le badge
                var badge = element.querySelector('.rgaa-badge, .rgaa-badge-issue, .rgaa-badge-compliant, .rgaa-badge-analyzing');
                if (badge) {
                    badge.remove();
                }
                
                // Supprimer le tooltip
                var tooltip = element.querySelector('.rgaa-tooltip');
                if (tooltip) {
                    tooltip.remove();
                }
                
                // Supprimer l'attribut data-rgaa-element-id
                element.removeAttribute('data-rgaa-element-id');
            """, element)
            
        except Exception as e:
            log_with_step(self.logger, logging.ERROR, "CSS", f"Erreur lors de la suppression du marquage : {str(e)}")
    
    def clear_all_markings(self):
        """Supprime tous les marquages CSS de la page"""
        try:
            self.driver.execute_script("""
                // Supprimer tous les éléments avec les classes RGAA
                var elements = document.querySelectorAll('.rgaa-analyzed, .rgaa-issue, .rgaa-compliant, .rgaa-analyzing');
                elements.forEach(function(element) {
                    element.classList.remove('rgaa-analyzed', 'rgaa-issue', 'rgaa-compliant', 'rgaa-analyzing');
                    element.classList.remove('rgaa-heading', 'rgaa-image', 'rgaa-link', 'rgaa-button', 'rgaa-form', 'rgaa-landmark', 'rgaa-aria');
                });
                
                // Supprimer tous les badges
                var badges = document.querySelectorAll('.rgaa-badge, .rgaa-badge-issue, .rgaa-badge-compliant, .rgaa-badge-analyzing');
                badges.forEach(function(badge) {
                    badge.remove();
                });
                
                // Supprimer tous les tooltips
                var tooltips = document.querySelectorAll('.rgaa-tooltip');
                tooltips.forEach(function(tooltip) {
                    tooltip.remove();
                });
                
                // Supprimer tous les attributs data-rgaa-element-id
                var elementsWithId = document.querySelectorAll('[data-rgaa-element-id]');
                elementsWithId.forEach(function(element) {
                    element.removeAttribute('data-rgaa-element-id');
                });
            """)
            
            self.marked_elements.clear()
            log_with_step(self.logger, logging.INFO, "CSS", "Tous les marquages CSS ont été supprimés")
            
        except Exception as e:
            log_with_step(self.logger, logging.ERROR, "CSS", f"Erreur lors de la suppression des marquages : {str(e)}")
    
    def toggle_production_mode(self, hide=True):
        """Active/désactive le mode production pour masquer/afficher les marquages"""
        try:
            if hide:
                self.driver.execute_script("document.body.classList.add('rgaa-production-hide')")
                log_with_step(self.logger, logging.INFO, "CSS", "Mode production activé - marquages masqués")
            else:
                self.driver.execute_script("document.body.classList.remove('rgaa-production-hide')")
                log_with_step(self.logger, logging.INFO, "CSS", "Mode production désactivé - marquages visibles")
        except Exception as e:
            log_with_step(self.logger, logging.ERROR, "CSS", f"Erreur lors du changement de mode : {str(e)}")
    
    def get_marked_elements_info(self):
        """Retourne les informations sur les éléments marqués"""
        return {
            'total_marked': len(self.marked_elements),
            'elements': self.marked_elements,
            'css_injected': self.css_injected
        }
    
    def _generate_element_id(self, element):
        """Génère un identifiant unique pour un élément"""
        try:
            # Essayer d'utiliser l'ID existant
            element_id = element.get_attribute('id')
            if element_id:
                return f"rgaa-{element_id}"
            
            # Utiliser le tag et la position
            tag = element.tag_name.lower()
            position = self.driver.execute_script("""
                var element = arguments[0];
                var rect = element.getBoundingClientRect();
                return Math.round(rect.left) + ',' + Math.round(rect.top);
            """, element)
            
            return f"rgaa-{tag}-{position}"
            
        except:
            # Fallback avec hash
            return f"rgaa-{hash(str(element))}"
    
    def create_info_tooltip(self, element_info):
        """Crée le contenu HTML pour un tooltip d'information"""
        if not element_info:
            return ""
        
        info_html = "<div style='text-align: left;'>"
        
        # Informations de base
        if element_info.get('tag'):
            info_html += f"<strong>Élément:</strong> {element_info['tag']}<br>"
        
        if element_info.get('id'):
            info_html += f"<strong>ID:</strong> {element_info['id']}<br>"
        
        if element_info.get('class'):
            info_html += f"<strong>Classes:</strong> {element_info['class']}<br>"
        
        # Rôle ARIA
        if element_info.get('role'):
            info_html += f"<strong>Rôle:</strong> {element_info['role']}<br>"
        
        # Texte accessible
        if element_info.get('accessible_name'):
            info_html += f"<strong>Nom accessible:</strong> {element_info['accessible_name']}<br>"
        
        # Problèmes détectés
        if element_info.get('issues') and len(element_info['issues']) > 0:
            info_html += "<strong>Problèmes:</strong><ul>"
            for issue in element_info['issues']:
                info_html += f"<li>{issue}</li>"
            info_html += "</ul>"
        
        # Statut de conformité
        if element_info.get('compliant') is not None:
            status = "✅ Conforme" if element_info['compliant'] else "❌ Non conforme"
            info_html += f"<strong>Statut:</strong> {status}<br>"
        
        info_html += "</div>"
        return info_html
