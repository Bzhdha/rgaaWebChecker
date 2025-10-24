from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import time
import csv
import json
from utils.log_utils import log_with_step
import logging
from modules.css_marker import CSSMarker

class DOMAnalyzer:
    def __init__(self, driver, logger, enable_css_marking=True):
        self.driver = driver
        self.logger = logger
        self.issues = []
        self.css_marker = CSSMarker(driver, logger) if enable_css_marking else None

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
                            # Analyser les problèmes d'accessibilité
                            self._check_accessibility_issues(element, element_info)
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
        
        # Retourner à la fois les éléments analysés et les problèmes détectés
        result = {
            'elements': analyzed_elements,
            'issues': self.issues,
            'summary': {
                'total_elements': total_elements,
                'analyzed_elements': len(analyzed_elements),
                'issues_found': len(self.issues)
            }
        }
        
        # Afficher un résumé détaillé
        self._display_detailed_summary(result)
        
        # Générer un rapport CSV détaillé
        self._generate_detailed_csv_report(result)
        
        # Générer un rapport JSON détaillé
        self._generate_detailed_json_report(result)
        
        return result

    def _is_element_stale(self, element):
        try:
            # Tenter d'accéder à une propriété de l'élément
            element.tag_name
            return False
        except StaleElementReferenceException:
            return True

    def _analyze_element(self, element):
        try:
            # Informations de base
            element_info = {
                'tag': element.tag_name,
                'id': element.get_attribute('id'),
                'class': element.get_attribute('class'),
                'role': element.get_attribute('role'),
                'aria_label': element.get_attribute('aria-label'),
                'aria_describedby': element.get_attribute('aria-describedby'),
                'aria_hidden': element.get_attribute('aria-hidden'),
                'aria_expanded': element.get_attribute('aria-expanded'),
                'aria_controls': element.get_attribute('aria-controls'),
                'aria_labelledby': element.get_attribute('aria-labelledby'),
                'text': element.text.strip() if element.text else '',
                'alt': element.get_attribute('alt'),
                'title': element.get_attribute('title'),
                'href': element.get_attribute('href'),
                'src': element.get_attribute('src'),
                'type': element.get_attribute('type'),
                'value': element.get_attribute('value'),
                'placeholder': element.get_attribute('placeholder'),
                'media_path': '',
                'media_type': '',
                'xpath': self._get_element_xpath(element),
                'css_selector': self._get_element_selector(element),
                'is_visible': False,
                'is_displayed': False,
                'is_enabled': False,
                'is_focusable': False,
                'position': {'x': 0, 'y': 0, 'width': 0, 'height': 0},
                'computed_style': {},
                'accessible_name': {
                    'name': '',
                    'source': 'none',
                    'priority': 0
                }
            }
            
            # Vérifier la visibilité et l'état
            try:
                element_info['is_displayed'] = element.is_displayed()
                element_info['is_enabled'] = element.is_enabled()
                element_info['is_visible'] = element_info['is_displayed']
                
                # Vérifier si l'élément est focusable
                if element_info['tag'].lower() in ['a', 'button', 'input', 'textarea', 'select', 'area']:
                    element_info['is_focusable'] = True
                else:
                    # Vérifier le tabindex
                    tabindex = element.get_attribute('tabindex')
                    if tabindex and tabindex != '-1':
                        element_info['is_focusable'] = True
                
                # Récupérer la position et les dimensions
                if element_info['is_displayed']:
                    try:
                        location = element.location
                        size = element.size
                        element_info['position'] = {
                            'x': location['x'],
                            'y': location['y'],
                            'width': size['width'],
                            'height': size['height']
                        }
                    except:
                        pass
                        
            except Exception as e:
                log_with_step(self.logger, logging.WARNING, "DOM", f"Erreur lors de la vérification de l'état de l'élément : {str(e)}")
            
            # Récupérer les styles calculés pour les éléments visibles
            if element_info['is_displayed']:
                try:
                    element_info['computed_style'] = {
                        'display': element.value_of_css_property('display'),
                        'visibility': element.value_of_css_property('visibility'),
                        'opacity': element.value_of_css_property('opacity'),
                        'position': element.value_of_css_property('position'),
                        'z_index': element.value_of_css_property('z-index'),
                        'background_color': element.value_of_css_property('background-color'),
                        'color': element.value_of_css_property('color'),
                        'font_size': element.value_of_css_property('font-size'),
                        'font_weight': element.value_of_css_property('font-weight')
                    }
                except:
                    pass
            
            # Déterminer le nom accessible selon l'ordre de priorité
            element_info['accessible_name'] = self._get_accessible_name(element, element_info)
            
            tag_name = element_info['tag'].lower()
            
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
            
            # Marquer l'élément avec CSS si activé
            if self.css_marker:
                self._mark_element_with_css(element, element_info)
            
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
                'aria_describedby': '',
                'aria_hidden': '',
                'aria_expanded': '',
                'aria_controls': '',
                'aria_labelledby': '',
                'text': '',
                'alt': '',
                'title': '',
                'href': '',
                'src': '',
                'type': '',
                'value': '',
                'placeholder': '',
                'media_path': '',
                'media_type': '',
                'xpath': '',
                'css_selector': 'unknown',
                'is_visible': False,
                'is_displayed': False,
                'is_enabled': False,
                'is_focusable': False,
                'position': {'x': 0, 'y': 0, 'width': 0, 'height': 0},
                'computed_style': {},
                'accessible_name': {
                    'name': '',
                    'source': 'none',
                    'priority': 0
                }
            }

    def _check_accessibility_issues(self, element, element_info):
        """Vérifie les problèmes d'accessibilité pour un élément"""
        try:
            tag_name = element_info['tag'].lower()
            selector = self._get_element_selector(element)
            
            # Critère 1.1 - Images sans alternative textuelle
            if tag_name == 'img':
                alt = element_info['alt']
                role = element_info['role']
                if not alt and role != 'presentation':
                    self.issues.append({
                        'type': 'Image sans alternative textuelle',
                        'element': selector,
                        'severity': 'critical',
                        'message': f"Image sans attribut alt ou role='presentation'",
                        'recommendation': 'Ajouter un attribut alt descriptif ou role="presentation" si l\'image est décorative'
                    })
                elif alt and alt.endswith(('.jpg', '.png', '.svg', '.gif')):
                    self.issues.append({
                        'type': 'Image avec nom de fichier comme alternative',
                        'element': selector,
                        'severity': 'high',
                        'message': f"L'attribut alt contient un nom de fichier: {alt}",
                        'recommendation': 'Remplacer le nom de fichier par une description pertinente de l\'image'
                    })
            
            # Critère 1.2 - Liens sans texte explicite
            elif tag_name == 'a':
                text = element_info['text']
                aria_label = element_info['aria_label']
                if not text and not aria_label:
                    self.issues.append({
                        'type': 'Lien sans texte explicite',
                        'element': selector,
                        'severity': 'critical',
                        'message': 'Lien sans texte visible ni aria-label',
                        'recommendation': 'Ajouter un texte descriptif au lien ou un aria-label'
                    })
                elif text and len(text.strip()) < 3:
                    self.issues.append({
                        'type': 'Lien avec texte insuffisant',
                        'element': selector,
                        'severity': 'medium',
                        'message': f'Texte du lien trop court: "{text}"',
                        'recommendation': 'Ajouter un texte plus descriptif pour le lien'
                    })
            
            # Critère 1.3 - Boutons sans texte
            elif tag_name == 'button':
                text = element_info['text']
                aria_label = element_info['aria_label']
                if not text and not aria_label:
                    self.issues.append({
                        'type': 'Bouton sans texte',
                        'element': selector,
                        'severity': 'critical',
                        'message': 'Bouton sans texte visible ni aria-label',
                        'recommendation': 'Ajouter un texte descriptif au bouton ou un aria-label'
                    })
            
            # Critère 1.4 - Formulaires sans labels
            elif tag_name in ['input', 'textarea', 'select']:
                id_attr = element_info['id']
                aria_label = element_info['aria_label']
                title = element_info['title']
                
                # Vérifier s'il y a un label associé
                has_label = False
                if id_attr:
                    try:
                        label = self.driver.find_element(By.CSS_SELECTOR, f'label[for="{id_attr}"]')
                        has_label = True
                    except:
                        pass
                
                if not has_label and not aria_label and not title:
                    self.issues.append({
                        'type': 'Champ de formulaire sans label',
                        'element': selector,
                        'severity': 'critical',
                        'message': f'Champ {tag_name} sans label associé',
                        'recommendation': 'Ajouter un label, aria-label ou title pour identifier le champ'
                    })
            
            # Critère 1.5 - Titres masqués
            elif tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                class_attr = element_info['class']
                if class_attr and ('sr-only' in class_attr or 'visually-hidden' in class_attr):
                    self.issues.append({
                        'type': 'Titre masqué visuellement',
                        'element': selector,
                        'severity': 'medium',
                        'message': f'Titre {tag_name} masqué visuellement',
                        'recommendation': 'Vérifier que le titre est pertinent pour la structure du document'
                    })
            
            # Critère 1.6 - Rôles ARIA invalides
            role = element_info['role']
            if role and role not in self._get_valid_aria_roles():
                self.issues.append({
                    'type': 'Rôle ARIA invalide',
                    'element': selector,
                    'severity': 'high',
                    'message': f'Rôle ARIA invalide: {role}',
                    'recommendation': f'Corriger ou supprimer le rôle ARIA invalide "{role}"'
                })
            
            # Critère 1.7 - Éléments interactifs sans focus
            if tag_name in ['a', 'button', 'input', 'textarea', 'select']:
                try:
                    if not element.is_displayed():
                        self.issues.append({
                            'type': 'Élément interactif non visible',
                            'element': selector,
                            'severity': 'medium',
                            'message': f'Élément {tag_name} non visible',
                            'recommendation': 'S\'assurer que l\'élément est visible ou le masquer complètement'
                        })
                except:
                    pass
                    
        except Exception as e:
            log_with_step(self.logger, logging.WARNING, "DOM", f"Erreur lors de la vérification d'accessibilité : {str(e)}")

    def _get_element_selector(self, element):
        """Génère un sélecteur CSS pour l'élément"""
        try:
            tag_name = element.tag_name.lower()
            id_attr = element.get_attribute('id')
            class_attr = element.get_attribute('class')
            
            if id_attr:
                return f"#{id_attr}"
            elif class_attr:
                classes = ' '.join(class_attr.split())
                return f"{tag_name}.{classes.replace(' ', '.')}"
            else:
                return tag_name
        except:
            return "unknown"

    def _get_element_xpath(self, element):
        """Génère le XPath de l'élément"""
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

    def _get_accessible_name(self, element, element_info):
        """
        Détermine le nom accessible selon l'ordre de priorité :
        1️⃣ aria-labelledby (priorité absolue)
        2️⃣ aria-label
        3️⃣ Contenu textuel (text node, inner text)
        4️⃣ Attribut alt (spécifique aux images)
        """
        try:
            tag_name = element_info['tag'].lower()
            
            # 1️⃣ aria-labelledby (priorité absolue)
            aria_labelledby = element_info.get('aria_labelledby', '')
            if aria_labelledby:
                try:
                    # Récupérer le texte des éléments référencés par aria-labelledby
                    labelledby_ids = aria_labelledby.split()
                    accessible_name = ""
                    for label_id in labelledby_ids:
                        label_element = self.driver.find_element(By.ID, label_id)
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
            aria_label = element_info.get('aria_label', '')
            if aria_label and aria_label.strip():
                return {
                    'name': aria_label.strip(),
                    'source': 'aria-label',
                    'priority': 2
                }
            
            # 3️⃣ Contenu textuel (text node, inner text)
            text_content = element_info.get('text', '')
            if text_content and text_content.strip():
                return {
                    'name': text_content.strip(),
                    'source': 'text_content',
                    'priority': 3
                }
            
            # 4️⃣ Attribut alt (spécifique aux images)
            if tag_name == 'img':
                alt_text = element_info.get('alt', '')
                if alt_text and alt_text.strip():
                    return {
                        'name': alt_text.strip(),
                        'source': 'alt',
                        'priority': 4
                    }
            
            # 4️⃣ Nom accessible hérité d'une image enfant (cas des liens avec logo)
            if tag_name == 'a':
                try:
                    img = element.find_element(By.TAG_NAME, 'img')
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
            log_with_step(self.logger, logging.WARNING, "DOM", f"Erreur lors de la détermination du nom accessible : {str(e)}")
            return {
                'name': '',
                'source': 'error',
                'priority': 0
            }

    def _get_valid_aria_roles(self):
        """Retourne la liste des rôles ARIA valides"""
        return [
            'alert', 'alertdialog', 'application', 'article', 'banner', 'button', 'cell', 'checkbox',
            'columnheader', 'combobox', 'complementary', 'contentinfo', 'definition', 'dialog',
            'directory', 'document', 'feed', 'figure', 'form', 'grid', 'gridcell', 'group', 'heading',
            'img', 'link', 'list', 'listbox', 'listitem', 'log', 'main', 'marquee', 'math', 'menu',
            'menubar', 'menuitem', 'menuitemcheckbox', 'menuitemradio', 'meter', 'navigation',
            'none', 'note', 'option', 'presentation', 'progressbar', 'radio', 'radiogroup', 'region',
            'row', 'rowgroup', 'rowheader', 'scrollbar', 'search', 'searchbox', 'separator', 'slider',
            'spinbutton', 'status', 'switch', 'tab', 'table', 'tablist', 'tabpanel', 'term', 'textbox',
            'timer', 'toolbar', 'tooltip', 'tree', 'treegrid', 'treeitem'
        ]

    def _display_detailed_summary(self, result):
        """Affiche un résumé détaillé de l'analyse DOM"""
        try:
            summary = result['summary']
            elements = result['elements']
            issues = result['issues']
            
            log_with_step(self.logger, logging.INFO, "DOM", "\n" + "="*60)
            log_with_step(self.logger, logging.INFO, "DOM", "RÉSUMÉ DÉTAILLÉ DE L'ANALYSE DOM")
            log_with_step(self.logger, logging.INFO, "DOM", "="*60)
            
            # Statistiques générales
            log_with_step(self.logger, logging.INFO, "DOM", f"Éléments totaux détectés : {summary['total_elements']}")
            log_with_step(self.logger, logging.INFO, "DOM", f"Éléments analysés avec succès : {summary['analyzed_elements']}")
            log_with_step(self.logger, logging.INFO, "DOM", f"Problèmes d'accessibilité détectés : {summary['issues_found']}")
            
            # Statistiques par type d'élément
            tag_counts = {}
            visible_count = 0
            focusable_count = 0
            aria_elements = 0
            accessible_names_count = 0
            accessible_names_by_source = {'aria-labelledby': 0, 'aria-label': 0, 'text_content': 0, 'alt': 0, 'none': 0}
            
            for element in elements:
                tag = element['tag'].lower()
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                if element.get('is_visible', False):
                    visible_count += 1
                if element.get('is_focusable', False):
                    focusable_count += 1
                if element.get('role') or element.get('aria_label') or element.get('aria_describedby'):
                    aria_elements += 1
                
                # Compter les noms accessibles
                accessible_name = element.get('accessible_name', {})
                if accessible_name.get('name'):
                    accessible_names_count += 1
                    source = accessible_name.get('source', 'none')
                    accessible_names_by_source[source] = accessible_names_by_source.get(source, 0) + 1
            
            log_with_step(self.logger, logging.INFO, "DOM", f"\nÉléments visibles : {visible_count}")
            log_with_step(self.logger, logging.INFO, "DOM", f"Éléments focusables : {focusable_count}")
            log_with_step(self.logger, logging.INFO, "DOM", f"Éléments avec attributs ARIA : {aria_elements}")
            log_with_step(self.logger, logging.INFO, "DOM", f"Éléments avec nom accessible : {accessible_names_count}")
            
            # Afficher la répartition des sources de noms accessibles
            log_with_step(self.logger, logging.INFO, "DOM", f"\nRépartition des noms accessibles :")
            for source, count in accessible_names_by_source.items():
                if count > 0:
                    log_with_step(self.logger, logging.INFO, "DOM", f"  {source}: {count}")
            
            # Top 10 des types d'éléments
            log_with_step(self.logger, logging.INFO, "DOM", f"\nTop 10 des types d'éléments :")
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            for tag, count in sorted_tags:
                log_with_step(self.logger, logging.INFO, "DOM", f"  {tag}: {count}")
            
            # Problèmes par sévérité
            if issues:
                severity_counts = {}
                for issue in issues:
                    severity = issue.get('severity', 'unknown')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                log_with_step(self.logger, logging.INFO, "DOM", f"\nProblèmes par sévérité :")
                for severity, count in severity_counts.items():
                    log_with_step(self.logger, logging.INFO, "DOM", f"  {severity}: {count}")
                
                # Afficher les 5 premiers problèmes critiques
                critical_issues = [i for i in issues if i.get('severity') == 'critical'][:5]
                if critical_issues:
                    log_with_step(self.logger, logging.INFO, "DOM", f"\nProblèmes critiques détectés :")
                    for i, issue in enumerate(critical_issues, 1):
                        log_with_step(self.logger, logging.INFO, "DOM", f"  {i}. {issue['type']} - {issue['element']}")
                        log_with_step(self.logger, logging.INFO, "DOM", f"     Message: {issue['message']}")
            
            # Afficher quelques exemples d'éléments analysés
            log_with_step(self.logger, logging.INFO, "DOM", f"\nEXEMPLES D'ÉLÉMENTS ANALYSÉS :")
            log_with_step(self.logger, logging.INFO, "DOM", "-" * 40)
            
            # Afficher les 5 premiers éléments avec des attributs ARIA
            aria_elements = [e for e in elements if e.get('role') or e.get('aria_label') or e.get('aria_describedby')][:5]
            if aria_elements:
                log_with_step(self.logger, logging.INFO, "DOM", "Éléments avec attributs ARIA :")
                for i, element in enumerate(aria_elements, 1):
                    log_with_step(self.logger, logging.INFO, "DOM", f"  {i}. {element['tag']} - ID: {element['id']} - Rôle: {element['role']} - Aria-label: {element['aria_label']}")
            
            # Afficher les 5 premiers éléments focusables
            focusable_elements = [e for e in elements if e.get('is_focusable', False)][:5]
            if focusable_elements:
                log_with_step(self.logger, logging.INFO, "DOM", "Éléments focusables :")
                for i, element in enumerate(focusable_elements, 1):
                    accessible_name = element.get('accessible_name', {})
                    name_info = accessible_name.get('name', 'Aucun nom accessible')
                    source = accessible_name.get('source', 'none')
                    priority = accessible_name.get('priority', 0)
                    
                    log_with_step(self.logger, logging.INFO, "DOM", f"  {i}. {element['tag']} - {element['css_selector']}")
                    log_with_step(self.logger, logging.INFO, "DOM", f"     Nom accessible: '{name_info}' (source: {source}, priorité: {priority})")
                    log_with_step(self.logger, logging.INFO, "DOM", f"     Texte: '{element['text'][:50]}...'")
            
            # Afficher les 5 premiers éléments avec des problèmes
            problematic_elements = [e for e in elements if any(i['element'] == e['css_selector'] for i in issues)][:5]
            if problematic_elements:
                log_with_step(self.logger, logging.INFO, "DOM", "Éléments avec problèmes :")
                for i, element in enumerate(problematic_elements, 1):
                    element_issues = [i for i in issues if i['element'] == element['css_selector']]
                    log_with_step(self.logger, logging.INFO, "DOM", f"  {i}. {element['tag']} - {element['css_selector']} - Problèmes: {len(element_issues)}")
                    for issue in element_issues[:2]:  # Afficher max 2 problèmes par élément
                        log_with_step(self.logger, logging.INFO, "DOM", f"     • {issue['type']}: {issue['message']}")
            
            log_with_step(self.logger, logging.INFO, "DOM", "="*60)
            
        except Exception as e:
            log_with_step(self.logger, logging.WARNING, "DOM", f"Erreur lors de l'affichage du résumé : {str(e)}")

    def _generate_detailed_csv_report(self, result):
        """Génère un rapport CSV détaillé avec tous les éléments analysés"""
        try:
            elements = result['elements']
            issues = result['issues']
            
            # Créer un fichier CSV
            filename = 'rapport_analyse_dom.csv'
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Écrire l'en-tête
                writer.writerow(['Élément', 'Tag', 'ID', 'Classe', 'Rôle', 'Aria-label', 'Aria-describedby', 'Aria-hidden', 'Aria-expanded', 'Aria-controls', 'Aria-labelledby', 'Texte', 'Alt', 'Title', 'Href', 'Src', 'Type', 'Value', 'Placeholder', 'Media Path', 'Media Type', 'XPath', 'CSS Selector', 'Is Visible', 'Is Displayed', 'Is Enabled', 'Is Focusable', 'Position', 'Computed Style', 'Problèmes'])
                
                # Écrire les lignes de données
                for element in elements:
                    tag = element['tag']
                    id_attr = element['id']
                    class_attr = element['class']
                    role = element['role']
                    aria_label = element['aria_label']
                    aria_describedby = element['aria_describedby']
                    aria_hidden = element['aria_hidden']
                    aria_expanded = element['aria_expanded']
                    aria_controls = element['aria_controls']
                    aria_labelledby = element['aria_labelledby']
                    text = element['text']
                    alt = element['alt']
                    title = element['title']
                    href = element['href']
                    src = element['src']
                    type = element['type']
                    value = element['value']
                    placeholder = element['placeholder']
                    media_path = element['media_path']
                    media_type = element['media_type']
                    xpath = element['xpath']
                    css_selector = element['css_selector']
                    is_visible = element['is_visible']
                    is_displayed = element['is_displayed']
                    is_enabled = element['is_enabled']
                    is_focusable = element['is_focusable']
                    position = element['position']
                    computed_style = element['computed_style']
                    issues_str = ', '.join([f"{i['type']} - {i['message']}" for i in issues if i['element'] == css_selector])
                    
                    writer.writerow([
                        tag, id_attr, class_attr, role, aria_label, aria_describedby, aria_hidden, aria_expanded, aria_controls, aria_labelledby, text, alt, title, href, src, type, value, placeholder, media_path, media_type, xpath, css_selector, is_visible, is_displayed, is_enabled, is_focusable, f"({position['x']}, {position['y']}, {position['width']}, {position['height']})", f"{computed_style.get('display', 'N/A')} {computed_style.get('visibility', 'N/A')} {computed_style.get('opacity', 'N/A')} {computed_style.get('position', 'N/A')} {computed_style.get('z_index', 'N/A')} {computed_style.get('background_color', 'N/A')} {computed_style.get('color', 'N/A')} {computed_style.get('font_size', 'N/A')} {computed_style.get('font_weight', 'N/A')}", issues_str
                    ])
            
            log_with_step(self.logger, logging.INFO, "DOM", f"Rapport CSV généré avec succès : {filename}")
            
        except Exception as e:
            log_with_step(self.logger, logging.WARNING, "DOM", f"Erreur lors de la génération du rapport CSV : {str(e)}")

    def _generate_detailed_json_report(self, result):
        """Génère un rapport JSON détaillé avec tous les éléments analysés"""
        try:
            elements = result['elements']
            issues = result['issues']
            
            # Créer un fichier JSON
            filename = 'rapport_analyse_dom.json'
            with open(filename, 'w') as jsonfile:
                json.dump({
                    'elements': elements,
                    'issues': issues,
                    'summary': result['summary']
                }, jsonfile)
            
            log_with_step(self.logger, logging.INFO, "DOM", f"Rapport JSON généré avec succès : {filename}")
            
        except Exception as e:
            log_with_step(self.logger, logging.WARNING, "DOM", f"Erreur lors de la génération du rapport JSON : {str(e)}")
    
    def _mark_element_with_css(self, element, element_info):
        """Marque un élément avec les classes CSS appropriées"""
        try:
            # Déterminer le type d'élément
            tag_name = element_info['tag'].lower()
            element_type = "analyzed"
            
            if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                element_type = "heading"
            elif tag_name == 'img':
                element_type = "image"
            elif tag_name == 'a':
                element_type = "link"
            elif tag_name == 'button' or (tag_name == 'input' and element_info.get('type') in ['button', 'submit', 'reset']):
                element_type = "button"
            elif tag_name in ['form', 'input', 'textarea', 'select']:
                element_type = "form"
            elif element_info.get('role') in ['banner', 'navigation', 'main', 'complementary', 'contentinfo', 'search', 'form']:
                element_type = "landmark"
            elif element_info.get('role') or any(attr.startswith('aria-') for attr in element_info.keys()):
                element_type = "aria"
            
            # Déterminer les problèmes d'accessibilité
            issues = []
            if not element_info.get('is_visible', False):
                issues.append("Élément non visible")
            if not element_info.get('is_enabled', False):
                issues.append("Élément désactivé")
            if tag_name == 'img' and not element_info.get('alt'):
                issues.append("Image sans attribut alt")
            if tag_name == 'a' and not element_info.get('text') and not element_info.get('aria_label'):
                issues.append("Lien sans texte visible")
            
            # Déterminer le statut de conformité
            compliant = len(issues) == 0
            
            # Créer les informations pour le tooltip
            tooltip_info = self._create_tooltip_info(element_info, issues, compliant)
            
            # Marquer l'élément
            self.css_marker.mark_element(
                element=element,
                element_type=element_type,
                issues=issues,
                compliant=compliant,
                info=tooltip_info
            )
            
        except Exception as e:
            log_with_step(self.logger, logging.WARNING, "CSS", f"Erreur lors du marquage CSS : {str(e)}")
    
    def _create_tooltip_info(self, element_info, issues, compliant):
        """Crée les informations pour le tooltip"""
        try:
            info_html = "<div style='text-align: left; font-size: 12px;'>"
            
            # Informations de base
            info_html += f"<strong>Élément:</strong> {element_info['tag']}<br>"
            
            if element_info.get('id'):
                info_html += f"<strong>ID:</strong> {element_info['id']}<br>"
            
            if element_info.get('class'):
                info_html += f"<strong>Classes:</strong> {element_info['class']}<br>"
            
            # Rôle ARIA
            if element_info.get('role'):
                info_html += f"<strong>Rôle:</strong> {element_info['role']}<br>"
            
            # Nom accessible
            accessible_name = element_info.get('accessible_name', {})
            if accessible_name.get('name'):
                info_html += f"<strong>Nom accessible:</strong> {accessible_name['name']}<br>"
            
            # Statut de visibilité
            if element_info.get('is_visible'):
                info_html += "<strong>Visibilité:</strong> ✅ Visible<br>"
            else:
                info_html += "<strong>Visibilité:</strong> ❌ Non visible<br>"
            
            # Problèmes détectés
            if issues:
                info_html += "<strong>Problèmes:</strong><ul style='margin: 4px 0; padding-left: 16px;'>"
                for issue in issues:
                    info_html += f"<li style='margin: 2px 0;'>{issue}</li>"
                info_html += "</ul>"
            
            # Statut de conformité
            if compliant:
                info_html += "<strong>Statut:</strong> ✅ Conforme"
            else:
                info_html += "<strong>Statut:</strong> ❌ Non conforme"
            
            info_html += "</div>"
            return info_html
            
        except Exception as e:
            log_with_step(self.logger, logging.WARNING, "CSS", f"Erreur lors de la création du tooltip : {str(e)}")
            return f"<div>Erreur: {str(e)}</div>" 