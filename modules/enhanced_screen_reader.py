# Copie du ScreenReader original avec ajout de méthodes pour exposer les données ARIA
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import time
import tempfile
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import math
import os
from utils.css_selector_generator import CSSSelectorGenerator
from modules.dom_accessibility_from_batch import (
    DOM_BATCH_EXTRACT_SCRIPT,
    build_dom_element_record,
    check_accessibility_issues_from_dict,
    stable_css_selector_from_attrs,
    write_dom_analysis_reports,
)
import logging
from utils.log_utils import log_with_step

class EnhancedScreenReader:
    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger
        self.page_url = None
        self.csv_lines = []  # Pour stocker les lignes CSV
        # Rapport DOM aligné DOMAnalyzer (batch) — activé par OrderedAccessibilityCrawler si module dom sans legacy
        self.emit_dom_rapport = False
        self._dom_report_elements = []
        self._dom_report_issues = []
        self.css_generator = CSSSelectorGenerator()  # Générateur de sélecteurs CSS
        self.non_conformites = {
            "images": [],
            "liens": [],
            "titres": [],
            "navigation": [],
            "roles_aria": [],
            "landmarks": [],
            "duplicate_id": []
        }
        # Cache pour les XPath
        self._xpath_cache = {}
        # Liste des rôles ARIA valides (extrait de la spec WAI-ARIA)
        self.ARIA_ROLES_VALIDES = set([
            'alert', 'alertdialog', 'application', 'article', 'banner', 'button', 'cell', 'checkbox', 'columnheader',
            'combobox', 'complementary', 'contentinfo', 'definition', 'dialog', 'directory', 'document', 'feed',
            'figure', 'form', 'grid', 'gridcell', 'group', 'heading', 'img', 'link', 'list', 'listbox', 'listitem',
            'log', 'main', 'marquee', 'math', 'menu', 'menubar', 'menuitem', 'menuitemcheckbox', 'menuitemradio',
            'navigation', 'none', 'note', 'option', 'presentation', 'progressbar', 'radio', 'radiogroup', 'region',
            'row', 'rowgroup', 'rowheader', 'scrollbar', 'search', 'searchbox', 'separator', 'slider', 'spinbutton',
            'status', 'switch', 'tab', 'table', 'tablist', 'tabpanel', 'term', 'textbox', 'timer', 'toolbar', 'tooltip', 'tree', 'treegrid', 'treeitem'
        ])
        # Liste des rôles dépréciés (exemple)
        self.ARIA_ROLES_DEPRECIES = set(['directory', 'marquee', 'note'])
        
        # Nouveau: Stockage des données ARIA pour partage
        self.aria_data_by_element = {}
        self.element_identifiers = {}

    def get_aria_data_for_element(self, element):
        """Retourne les données ARIA pour un élément spécifique"""
        try:
            element_id = self._get_element_identifier(element)
            return self.aria_data_by_element.get(element_id, {})
        except Exception as e:
            self.logger.warning(f"Erreur lors de la récupération des données ARIA: {e}")
            return {}

    def get_all_aria_data(self):
        """Retourne toutes les données ARIA collectées"""
        return self.aria_data_by_element

    def _get_element_identifier(self, element):
        """Génère un identifiant unique pour un élément"""
        try:
            tag = element.tag_name
            element_id = element.get_attribute('id')
            element_class = element.get_attribute('class')
            element_text = element.text[:50] if element.text else ''
            
            # Créer un identifiant basé sur les propriétés les plus stables
            if element_id:
                return f"{tag}#{element_id}"
            elif element_text:
                return f"{tag}[text='{element_text[:30]}']"
            elif element_class:
                return f"{tag}.{element_class.split()[0]}"
            else:
                return f"{tag}[{hash(str(element))}]"
        except Exception as e:
            self.logger.warning(f"Erreur lors de la génération de l'identifiant: {e}")
            return f"unknown_{hash(str(element))}"

    def _get_element_info(self, element):
        """Récupère toutes les informations d'accessibilité d'un élément (optimisé)"""
        # Récupération groupée des attributs via JS en une seule fois
        attrs = self.driver.execute_script('''
            var el = arguments[0];
            var rect = el.getBoundingClientRect();
            var style = window.getComputedStyle(el);
            // Calculer la position parmi les frères dans le DOM (1-based)
            var domIndex = (function(){
                try {
                    var parent = el.parentNode;
                    if (!parent) return -1;
                    var children = Array.prototype.filter.call(parent.children, function(c){ return c.nodeType === 1; });
                    for (var i=0; i<children.length; i++){ if (children[i] === el) return i+1; }
                    return -1;
                } catch (e) { return -1; }
            })();
            // Calculer la position du parent parmi ses frères (1-based)
            var parentIndex = (function(){
                try {
                    var parent = el.parentNode;
                    if (!parent || !parent.parentNode) return -1;
                    var siblings = Array.prototype.filter.call(parent.parentNode.children, function(c){ return c.nodeType === 1; });
                    for (var i=0; i<siblings.length; i++){ if (siblings[i] === parent) return i+1; }
                    return -1;
                } catch (e) { return -1; }
            })();
            return {
                tag: el.tagName,
                role: el.getAttribute('role'),
                ariaLabel: el.getAttribute('aria-label'),
                ariaDescribedby: el.getAttribute('aria-describedby'),
                ariaLabelledby: el.getAttribute('aria-labelledby'),
                ariaHidden: el.getAttribute('aria-hidden'),
                ariaExpanded: el.getAttribute('aria-expanded'),
                ariaControls: el.getAttribute('aria-controls'),
                ariaLive: el.getAttribute('aria-live'),
                ariaAtomic: el.getAttribute('aria-atomic'),
                ariaRelevant: el.getAttribute('aria-relevant'),
                ariaBusy: el.getAttribute('aria-busy'),
                ariaCurrent: el.getAttribute('aria-current'),
                ariaPosinset: el.getAttribute('aria-posinset'),
                ariaSetsize: el.getAttribute('aria-setsize'),
                ariaLevel: el.getAttribute('aria-level'),
                ariaSort: el.getAttribute('aria-sort'),
                ariaValuemin: el.getAttribute('aria-valuemin'),
                ariaValuemax: el.getAttribute('aria-valuemax'),
                ariaValuenow: el.getAttribute('aria-valuenow'),
                ariaValuetext: el.getAttribute('aria-valuetext'),
                ariaHaspopup: el.getAttribute('aria-haspopup'),
                ariaInvalid: el.getAttribute('aria-invalid'),
                ariaRequired: el.getAttribute('aria-required'),
                ariaReadonly: el.getAttribute('aria-readonly'),
                ariaDisabled: el.getAttribute('aria-disabled'),
                ariaSelected: el.getAttribute('aria-selected'),
                ariaChecked: el.getAttribute('aria-checked'),
                ariaPressed: el.getAttribute('aria-pressed'),
                ariaMultiline: el.getAttribute('aria-multiline'),
                ariaMultiselectable: el.getAttribute('aria-multiselectable'),
                ariaOrientation: el.getAttribute('aria-orientation'),
                ariaPlaceholder: el.getAttribute('aria-placeholder'),
                ariaRoledescription: el.getAttribute('aria-roledescription'),
                ariaKeyshortcuts: el.getAttribute('aria-keyshortcuts'),
                ariaDetails: el.getAttribute('aria-details'),
                ariaErrormessage: el.getAttribute('aria-errormessage'),
                ariaFlowto: el.getAttribute('aria-flowto'),
                ariaOwns: el.getAttribute('aria-owns'),
                tabindex: el.getAttribute('tabindex'),
                title: el.getAttribute('title'),
                alt: el.getAttribute('alt'),
                id: el.getAttribute('id'),
                className: el.getAttribute('class'),
                outerHTML: el.outerHTML,
                text: el.textContent,
                isVisible: !(style.display === 'none' || style.visibility === 'hidden' || rect.width === 0 || rect.height === 0),
                isEnabled: !el.disabled,
                isFocusable: el.tabIndex >= 0 || el.tagName === 'A' || el.tagName === 'BUTTON' || el.tagName === 'INPUT' || el.tagName === 'SELECT' || el.tagName === 'TEXTAREA',
                mediaPath: el.getAttribute('src') || el.getAttribute('data') || '',
                mediaType: el.tagName.toLowerCase(),
                domIndex: domIndex,
                parentIndex: parentIndex,
                // position absolue dans le document (1-based, même document que l'élément)
                absIndex: (function(){
                    try {
                        var doc = el.ownerDocument || document;
                        var all = doc.querySelectorAll('*');
                        for (var k=0;k<all.length;k++){ if (all[k]===el) return k+1; }
                        return -1;
                    } catch (e) { return -1; }
                })()
            ,
            // position absolue du parent (élément) dans le document (1-based)
            parentAbsIndex: (function(){
                try {
                    var parent = el.parentNode;
                    if (!parent || parent.nodeType !== 1) return -1;
                    var doc = el.ownerDocument || document;
                    var all = doc.querySelectorAll('*');
                    for (var k=0;k<all.length;k++){ if (all[k]===parent) return k+1; }
                    return -1;
                } catch (e) { return -1; }
            })()
            };
        ''', element)

        # Construction du dictionnaire d'informations en une seule fois
        info = {
            "Type": attrs['tag'],
            "Rôle": attrs['role'] or "non défini",
            "Aria-label": attrs['ariaLabel'] or "non défini",
            "Aria-describedby": attrs['ariaDescribedby'] or "non défini",
            "Aria-labelledby": attrs['ariaLabelledby'] or "non défini",
            "Aria-hidden": attrs['ariaHidden'] or "non défini",
            "Aria-expanded": attrs['ariaExpanded'] or "non défini",
            "Aria-controls": attrs['ariaControls'] or "non défini",
            "Aria-live": attrs['ariaLive'] or "non défini",
            "Aria-atomic": attrs['ariaAtomic'] or "non défini",
            "Aria-relevant": attrs['ariaRelevant'] or "non défini",
            "Aria-busy": attrs['ariaBusy'] or "non défini",
            "Aria-current": attrs['ariaCurrent'] or "non défini",
            "Aria-posinset": attrs['ariaPosinset'] or "non défini",
            "Aria-setsize": attrs['ariaSetsize'] or "non défini",
            "Aria-level": attrs['ariaLevel'] or "non défini",
            "Aria-sort": attrs['ariaSort'] or "non défini",
            "Aria-valuemin": attrs['ariaValuemin'] or "non défini",
            "Aria-valuemax": attrs['ariaValuemax'] or "non défini",
            "Aria-valuenow": attrs['ariaValuenow'] or "non défini",
            "Aria-valuetext": attrs['ariaValuetext'] or "non défini",
            "Aria-haspopup": attrs['ariaHaspopup'] or "non défini",
            "Aria-invalid": attrs['ariaInvalid'] or "non défini",
            "Aria-required": attrs['ariaRequired'] or "non défini",
            "Aria-readonly": attrs['ariaReadonly'] or "non défini",
            "Aria-disabled": attrs['ariaDisabled'] or "non défini",
            "Aria-selected": attrs['ariaSelected'] or "non défini",
            "Aria-checked": attrs['ariaChecked'] or "non défini",
            "Aria-pressed": attrs['ariaPressed'] or "non défini",
            "Aria-multiline": attrs['ariaMultiline'] or "non défini",
            "Aria-multiselectable": attrs['ariaMultiselectable'] or "non défini",
            "Aria-orientation": attrs['ariaOrientation'] or "non défini",
            "Aria-placeholder": attrs['ariaPlaceholder'] or "non défini",
            "Aria-roledescription": attrs['ariaRoledescription'] or "non défini",
            "Aria-keyshortcuts": attrs['ariaKeyshortcuts'] or "non défini",
            "Aria-details": attrs['ariaDetails'] or "non défini",
            "Aria-errormessage": attrs['ariaErrormessage'] or "non défini",
            "Aria-flowto": attrs['ariaFlowto'] or "non défini",
            "Aria-owns": attrs['ariaOwns'] or "non défini",
            "Tabindex": attrs['tabindex'] or "non défini",
            "Title": attrs['title'] or "non défini",
            "Alt": attrs['alt'] or "non défini",
            "Text": attrs['text'].strip() if attrs['text'] else "non défini",
            "Visible": "Oui" if attrs['isVisible'] else "Non",
            "Focusable": "Oui" if attrs['isFocusable'] else "Non",
            "Id": attrs['id'] or "non défini",
            "Sélecteur": self._get_simple_selector(element),
            "Extrait HTML": (attrs['outerHTML'] or '')[:200] + '...',
            "MediaPath": attrs['mediaPath'] or "non défini",
            "MediaType": attrs['mediaType'] or "non défini",
            # Positions DOM si fournies
            "Dom-absolute-position": attrs.get('absIndex') if isinstance(attrs, dict) and 'absIndex' in attrs else ("non défini"),
            "Parent-absolute-position": attrs.get('parentAbsIndex') if isinstance(attrs, dict) and 'parentAbsIndex' in attrs else ("non défini"),
            "Dom-position": attrs.get('domIndex') if isinstance(attrs, dict) and 'domIndex' in attrs else ("non défini"),
            "Parent-position": attrs.get('parentIndex') if isinstance(attrs, dict) and 'parentIndex' in attrs else ("non défini")
        }
        
        # Stocker les données ARIA pour partage (clé alignée sur EnhancedTabNavigator)
        element_id = self._get_shared_element_key(element)
        self.aria_data_by_element[element_id] = info
        
        return info

    def _get_simple_selector(self, element):
        tag = element.tag_name
        classes = element.get_attribute('class')
        if classes:
            return f"{tag}.{'.'.join(classes.split())}"
        return tag

    # ... (reste du code identique au ScreenReader original)
    # Pour simplifier, on garde les méthodes essentielles
    
    def run(self):
        """Exécute l'analyse d'accessibilité avec stockage des données ARIA"""
        # Réinitialiser les lignes CSV et le cache XPath pour une analyse fraîche
        self.csv_lines = []
        self._xpath_cache.clear()
        self._dom_report_elements = []
        self._dom_report_issues = []
        self._last_dom_total_elements = 0
        self.aria_data_by_element = {}

        # Afficher l'URL de la page analysée en haut de l'analyse
        try:
            url = self.driver.current_url
            log_with_step(self.logger, logging.INFO, "SCREEN", f"URL analysée : {url}")
        except Exception:
            pass

        # En-tête CSV (ajout du contexte d'iframe et positions DOM)
        csv_header = [
            "Type", "Sélecteur", "Extrait HTML", "Rôle", "Aria-label", "Text", "Alt", "Title", "Visible", "Focusable", "Id",
            # Nouvelles colonnes ARIA pour les outils de narration
            "Aria-describedby", "Aria-labelledby", "Aria-hidden", "Aria-expanded", "Aria-controls", "Aria-live", "Aria-atomic", "Aria-relevant", "Aria-busy", "Aria-current", "Aria-posinset", "Aria-setsize", "Aria-level", "Aria-sort", "Aria-valuemin", "Aria-valuemax", "Aria-valuenow", "Aria-valuetext", "Aria-haspopup", "Aria-invalid", "Aria-required", "Aria-readonly", "Aria-disabled", "Aria-selected", "Aria-checked", "Aria-pressed", "Aria-multiline", "Aria-multiselectable", "Aria-orientation", "Aria-placeholder", "Aria-roledescription", "Aria-keyshortcuts", "Aria-details", "Aria-errormessage", "Aria-flowto", "Aria-owns", "Tabindex",
            # Positions dans le DOM
            "Dom-absolute-position", "Parent-absolute-position", "Dom-position", "Parent-position",
            # Contexte iframe
            "Frame-src", "Frame-index",
            "X-path simplifié", "X-path complet", "X-path secondaire 1", "X-path secondaire 2"
            , "Sélecteur CSS principal", "Sélecteur CSS secondaire 1", "Sélecteur CSS secondaire 2",
            "InnerText", "Name-attr", "Type-attr", "Value-attr", "Placeholder-attr", "HasLabelFor",
            "Accessible-name", "AccName-source", "Is-displayed-DOM", "Rect-page", "ComputedStyle-short",
        ]
        self.csv_lines.append(';'.join(csv_header))

        # En-tête (fichier + console structurée)
        self.logger.info("## Analyse des éléments d'accessibilité")
        log_with_step(
            self.logger,
            logging.INFO,
            "SCREEN",
            "Périmètre RGAA : titres, images, liens, boutons, formulaires, landmarks, attributs ARIA",
        )

        # Initialiser le contexte de frame par défaut
        self._current_frame_src = ""
        self._current_frame_index = -1

        # Analyser le document principal (default content) puis chaque iframe détectée
        try:
            # Analyse du document racine
            self.driver.switch_to.default_content()
            self._current_frame_src = ""
            self._current_frame_index = -1
            self._analyze_document()

            # Rechercher les iframes/frames dans le document principal
            frames = self.driver.find_elements(By.CSS_SELECTOR, "iframe, frame")
            for idx, frame in enumerate(frames):
                try:
                    frame_src = frame.get_attribute('src') or frame.get_attribute('name') or ''
                    # Passer dans le contexte de la frame
                    self.driver.switch_to.frame(frame)
                    self._current_frame_src = frame_src
                    self._current_frame_index = idx
                    log_with_step(
                        self.logger,
                        logging.INFO,
                        "SCREEN",
                        f"Analyse iframe #{idx} src={frame_src!r}",
                    )
                    self._analyze_document()
                except Exception as e:
                    # Impossible d'accéder au contenu de la frame (ex: cross-origin)
                    self.logger.warning(f"Impossible d'inspecter iframe #{idx} (src='{frame_src}'): {e}")
                finally:
                    # Revenir au contexte principal pour passer à la frame suivante
                    try:
                        self.driver.switch_to.default_content()
                    except Exception:
                        pass

            # Après avoir parcouru toutes les frames, vérifier les ids dupliqués (dans chaque contexte on a ajouté les éléments au CSV)
            log_with_step(self.logger, logging.INFO, "SCREEN", "Phase finale : vérification des identifiants uniques")
            self._check_duplicate_ids()

        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse multi-frame du DOM : {str(e)}")

        self._write_accessibility_csv()

        if self.emit_dom_rapport and self._dom_report_elements:
            summary = {
                "total_elements": self._last_dom_total_elements or len(self._dom_report_elements),
                "analyzed_elements": len(self._dom_report_elements),
                "issues_found": len(self._dom_report_issues),
            }
            write_dom_analysis_reports(
                self._dom_report_elements,
                self._dom_report_issues,
                summary,
                csv_filename="rapport_analyse_dom.csv",
                json_filename="rapport_analyse_dom.json",
                logger=self.logger,
            )

        # Générer le rapport après l'analyse
        self.generate_report()
        log_with_step(self.logger, logging.INFO, "SCREEN", "Rapport lecteur d'écran généré avec succès.")
        log_with_step(
            self.logger,
            logging.INFO,
            "SCREEN",
            f"Données ARIA collectées : {len(self.aria_data_by_element)} éléments",
        )

    def _print_element_table(self, element, element_type):
        """Analyse un élément et ajoute ses informations au rapport"""
        try:
            info = self._get_element_info(element)
            main_xpath, secondary_xpaths = self._get_xpath(element)
            
            # Ajout des XPath dans le dictionnaire info
            info["main_xpath"] = main_xpath
            info["secondary_xpath1"] = secondary_xpaths[0] if len(secondary_xpaths) > 0 else ''
            info["secondary_xpath2"] = secondary_xpaths[1] if len(secondary_xpaths) > 1 else ''
            
            # Génération de sélecteurs CSS alternatifs
            css_selectors = self.css_generator.generate_css_selectors(element)
            info["main_css"] = css_selectors["main_css"]
            info["secondary_css1"] = css_selectors["secondary_css1"]
            info["secondary_css2"] = css_selectors["secondary_css2"]
            
            # Construction de la ligne CSV avec toutes les données ARIA
            # Ajouter le contexte de frame dans les infos
            info["Frame-src"] = getattr(self, '_current_frame_src', "")
            info["Frame-index"] = getattr(self, '_current_frame_index', -1)

            row = [
                self._clean_csv_field(info["Type"]),
                self._clean_csv_field(info["Sélecteur"]),
                self._clean_csv_field(info["Extrait HTML"]),
                self._clean_csv_field(info["Rôle"]),
                self._clean_csv_field(info["Aria-label"]),
                self._clean_csv_field(info["Text"]),
                self._clean_csv_field(info["Alt"]),
                self._clean_csv_field(info["Title"]),
                self._clean_csv_field(info["Visible"]),
                self._clean_csv_field(info["Focusable"]),
                self._clean_csv_field(info["Id"]),
                # Nouvelles colonnes ARIA pour les outils de narration
                self._clean_csv_field(info["Aria-describedby"]),
                self._clean_csv_field(info["Aria-labelledby"]),
                self._clean_csv_field(info["Aria-hidden"]),
                self._clean_csv_field(info["Aria-expanded"]),
                self._clean_csv_field(info["Aria-controls"]),
                self._clean_csv_field(info["Aria-live"]),
                self._clean_csv_field(info["Aria-atomic"]),
                self._clean_csv_field(info["Aria-relevant"]),
                self._clean_csv_field(info["Aria-busy"]),
                self._clean_csv_field(info["Aria-current"]),
                self._clean_csv_field(info["Aria-posinset"]),
                self._clean_csv_field(info["Aria-setsize"]),
                self._clean_csv_field(info["Aria-level"]),
                self._clean_csv_field(info["Aria-sort"]),
                self._clean_csv_field(info["Aria-valuemin"]),
                self._clean_csv_field(info["Aria-valuemax"]),
                self._clean_csv_field(info["Aria-valuenow"]),
                self._clean_csv_field(info["Aria-valuetext"]),
                self._clean_csv_field(info["Aria-haspopup"]),
                self._clean_csv_field(info["Aria-invalid"]),
                self._clean_csv_field(info["Aria-required"]),
                self._clean_csv_field(info["Aria-readonly"]),
                self._clean_csv_field(info["Aria-disabled"]),
                self._clean_csv_field(info["Aria-selected"]),
                self._clean_csv_field(info["Aria-checked"]),
                self._clean_csv_field(info["Aria-pressed"]),
                self._clean_csv_field(info["Aria-multiline"]),
                self._clean_csv_field(info["Aria-multiselectable"]),
                self._clean_csv_field(info["Aria-orientation"]),
                self._clean_csv_field(info["Aria-placeholder"]),
                self._clean_csv_field(info["Aria-roledescription"]),
                self._clean_csv_field(info["Aria-keyshortcuts"]),
                self._clean_csv_field(info["Aria-details"]),
                self._clean_csv_field(info["Aria-errormessage"]),
                self._clean_csv_field(info["Aria-flowto"]),
                self._clean_csv_field(info["Aria-owns"]),
                self._clean_csv_field(info["Tabindex"]),
                # Positions DOM
                self._clean_csv_field(info.get("Dom-position", "")),
                self._clean_csv_field(info.get("Parent-position", "")),
                # Contexte iframe
                self._clean_csv_field(info.get("Frame-src", "")),
                self._clean_csv_field(info.get("Frame-index", "")),
                self._clean_csv_field(info["main_xpath"]),
                self._clean_csv_field(info.get("xpath_complet", "")),
                self._clean_csv_field(info["secondary_xpath1"]),
                self._clean_csv_field(info["secondary_xpath2"]),
                # Sélecteurs CSS alternatifs
                self._clean_csv_field(info["main_css"]),
                self._clean_csv_field(info["secondary_css1"]),
                self._clean_csv_field(info["secondary_css2"])
            ]
            self.csv_lines.append(';'.join(row))
            
            # Analyse des non-conformités
            self._analyze_non_conformites(info, element_type, element)
            
            # Stocker les attributs ARIA pour affichage après la progression
            aria_attrs = {k: v for k, v in info.items() if k.startswith("Aria-") and v != "non défini"}
            if aria_attrs:
                # Stocker pour affichage après la barre de progression
                if not hasattr(self, '_aria_attrs_to_log'):
                    self._aria_attrs_to_log = []
                self._aria_attrs_to_log.append((element_type, aria_attrs))
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse de l'élément {element_type}: {str(e)}")

    def _analyze_document(self):
        """Analyse le document courant (contexte principal ou iframe)"""
        try:
            # Récupérer tous les éléments en une seule fois (document order)
            all_elements = self.driver.find_elements(By.XPATH, "//*")
            total_elements = len(all_elements)
            self._last_dom_total_elements += total_elements
            frame_ctx = getattr(self, "_current_frame_src", "") or "(principal)"
            log_with_step(
                self.logger,
                logging.INFO,
                "SCREEN",
                f"DOM frame={frame_ctx!r} : {total_elements} éléments — export complet…",
            )

            # Important: on exporte tous les éléments du DOM (dans le contexte courant
            # principal ou iframe) afin d'avoir la totalité des lignes dans
            # `reports/accessibility_analysis.csv`.
            start = time.time()
            self._analyze_elements_integrated(all_elements, "DOM_COMPLET")
            self._log_aria_attributes()
            elapsed = time.time() - start
            log_with_step(
                self.logger,
                logging.INFO,
                "SCREEN",
                f"Analyse DOM terminée en {elapsed:.2f}s ({total_elements} éléments)",
            )

        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse du DOM : {str(e)}")

    def _get_xpath(self, element):
        """Génère le X-path absolu complet de l'élément (chemin depuis /html avec indices), avec mise en cache par élément."""
        try:
            # Clé incluant l'identité de l'élément pour éviter des collisions (ex. deux divs même classe)
            element_id = element.get_attribute('id')
            element_class = element.get_attribute('class')
            element_tag = element.tag_name
            element_text = element.text[:50] if element.text else ''
            cache_key = f"{id(element)}:{element_tag}:{element_id}:{element_class}:{element_text}"
            
            if cache_key in self._xpath_cache:
                return self._xpath_cache[cache_key]
            
            def get_xpath(el):
                """Génère un XPath absolu complet (chemin depuis /html avec indices)."""
                # Si l'élément a un ID unique, on peut retourner le court chemin ;
                # on génère aussi le chemin complet pour cohérence avec les attentes.
                path = []
                current = el
                try:
                    while current is not None:
                        tag_lower = current.tag_name.lower()
                        if tag_lower == 'html':
                            break
                        # Index 1-based parmi les frères du même nom de balise
                        siblings = current.find_elements(By.XPATH, f"preceding-sibling::{current.tag_name}")
                        index = len(siblings) + 1
                        segment = f"{tag_lower}[{index}]"
                        path.insert(0, segment)
                        current = current.find_element(By.XPATH, '..')
                except Exception:
                    pass
                if not path:
                    return f"//*[@id='{element_id}']" if element_id else "//*"
                return '/html/' + '/'.join(path)
            
            # Générer le XPath principal
            main_xpath = get_xpath(element)
            
            # Générer des XPath alternatifs
            secondary = []
            
            # XPath par ID (si disponible)
            if element_id:
                secondary.append(f"//*[@id='{element_id}']")
            
            # XPath par classe (si disponible)
            if element_class:
                class_list = element_class.split()
                for c in class_list:
                    secondary.append(f"//{element_tag}[contains(@class, '{c}')]")
            
            # XPath par texte (si disponible et court)
            if element_text and len(element_text) < 50:
                secondary.append(f"//{element_tag}[contains(text(), '{element_text}')]")
            
            result = (main_xpath, secondary[:2])
            
            # Mettre en cache le résultat
            self._xpath_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            self.logger.debug(f"Erreur lors de la génération du XPath : {str(e)}")
            return ('Non disponible', [])

    def _clean_csv_field(self, value):
        """Nettoie une valeur pour l'insertion dans un CSV"""
        if value is None:
            return "non défini"
        # Convertir en string si ce n'est pas déjà le cas
        value = str(value)
        # Remplacer les retours à la ligne par des espaces
        value = value.replace('\n', ' ').replace('\r', ' ')
        # Supprimer les espaces multiples
        value = ' '.join(value.split())
        # Échapper les points-virgules
        value = value.replace(';', ',')
        return value

    def _analyze_non_conformites(self, info, element_type, element):
        """Analyse les non-conformités RGAA pour un élément"""
        # On détermine la logique d'analyse à partir du tag courant (et pas du
        # nom de la catégorie), afin de rester cohérent quand on analyse le DOM
        # complet (au lieu de catégories).
        tag = (info.get("Type") or "").lower()
        role = info.get("Rôle", "non défini")

        if tag == "img":
            # Critère 1.3 - Images
            alt = info["Alt"]
            if alt == "non défini" and role != "presentation":
                self.non_conformites["images"].append({
                    "type": "Image sans alternative textuelle",
                    "element": info["Sélecteur"],
                    "xpath": info["main_xpath"],
                    "recommandation": "Ajouter un attribut alt descriptif ou role='presentation' si l'image est décorative"
                })
            elif alt.endswith(('.jpg', '.png', '.svg')) and role != "presentation":
                self.non_conformites["images"].append({
                    "type": "Image avec nom de fichier comme alternative",
                    "element": info["Sélecteur"],
                    "xpath": info["main_xpath"],
                    "recommandation": "Remplacer le nom de fichier par une description pertinente de l'image"
                })

        elif tag == "a":
            # Critère liens
            results = self._analyze_links_batch([element])
            self.non_conformites["liens"].extend(results)

        elif tag.startswith("h") and tag[1:].isdigit():
            # Critère 9.1 - Titres
            if "sr-only" in info["Sélecteur"]:
                self.non_conformites["titres"].append({
                    "type": "Titre masqué visuellement",
                    "element": info["Sélecteur"],
                    "xpath": info["main_xpath"],
                    "recommandation": "Vérifier que le titre est pertinent pour la structure du document"
                })

        elif tag == "nav":
            # Critère 12.1 - Navigation
            aria_label = info["Aria-label"]
            if aria_label == "non défini":
                self.non_conformites["navigation"].append({
                    "type": "Navigation sans label",
                    "element": info["Sélecteur"],
                    "xpath": info["main_xpath"],
                    "recommandation": "Ajouter un aria-label descriptif à la navigation"
                })

        # Analyse des rôles ARIA
        if role != "non défini":
            if role not in self.ARIA_ROLES_VALIDES:
                self.non_conformites["roles_aria"].append({
                    "type": f"Rôle ARIA non valide : '{role}'",
                    "element": info["Sélecteur"],
                    "xpath": info["main_xpath"],
                    "recommandation": f"Le rôle ARIA '{role}' n'est pas reconnu par la spécification WAI-ARIA. Corrigez ou supprimez ce rôle."
                })
            elif role in self.ARIA_ROLES_DEPRECIES:
                self.non_conformites["roles_aria"].append({
                    "type": f"Rôle ARIA déprécié : '{role}'",
                    "element": info["Sélecteur"],
                    "xpath": info["main_xpath"],
                    "recommandation": f"Le rôle ARIA '{role}' est déprécié et ne doit plus être utilisé."
                })
        elif role == "non défini" and tag in ["button", "a", "img", "form"]:
            # On ne signale que les cas principaux (bouton, lien, image, formulaire)
            # pour éviter trop de bruit sur le DOM complet.
            tag_to_label = {
                "button": "Button",
                "a": "Link",
                "img": "Image",
                "form": "Form",
            }
            element_label = tag_to_label.get(tag, tag)
            self.non_conformites["roles_aria"].append({
                "type": f"Élément {element_label} sans rôle ARIA",
                "element": info["Sélecteur"],
                "xpath": info["main_xpath"],
                "recommandation": f"Ajouter un rôle ARIA approprié pour l'élément {element_label}"
            })

    def _analyze_links_batch(self, links):
        """Analyse un lot de liens de manière optimisée"""
        results = []
        for link in links:
            try:
                # Récupération groupée des attributs via JS en une seule fois
                attrs = self.driver.execute_script('''
                    var el = arguments[0];
                    return {
                        text: el.textContent.trim(),
                        ariaLabel: el.getAttribute('aria-label'),
                        href: el.getAttribute('href'),
                        class: el.getAttribute('class'),
                        id: el.getAttribute('id')
                    };
                ''', link)
                
                text = attrs['text']
                aria_label = attrs['ariaLabel']
                href = attrs['href']
                class_name = attrs['class']
                
                # Vérification des non-conformités
                if not text or len(text.strip()) < 3:
                    main_xpath, _ = self._get_xpath(link)
                    results.append({
                        "type": "Lien sans texte explicite",
                        "element": self._get_simple_selector(link),
                        "xpath": main_xpath,
                        "recommandation": "Ajouter un texte descriptif au lien ou un aria-label"
                    })
                
                if class_name and "btn--hide-txt" in class_name:
                    main_xpath, _ = self._get_xpath(link)
                    results.append({
                        "type": "Lien avec texte masqué",
                        "element": self._get_simple_selector(link),
                        "xpath": main_xpath,
                        "recommandation": "S'assurer que le texte est accessible aux lecteurs d'écran via aria-label"
                    })
            except Exception as e:
                self.logger.debug(f"Erreur lors de l'analyse du lien : {str(e)}")
                continue
                
        return results

    def _analyze_duplicate_id_impact(self, duplicate_id, elements_with_id):
        """
        Analyse l'impact spécifique d'un ID dupliqué selon les catégories RGAA
        
        Retourne une liste d'impacts détectés avec leurs descriptions
        """
        impacts = []
        
        # Vérifier si l'ID est référencé par d'autres éléments (aria-labelledby, aria-describedby, etc.)
        referenced_attributes = ['aria-labelledby', 'aria-describedby', 'aria-controls', 
                                'aria-owns', 'aria-flowto', 'aria-errormessage', 'aria-details']
        
        # Vérifier si l'ID est utilisé dans des labels
        labels_using_id = self.driver.find_elements(By.XPATH, f'//label[@for="{duplicate_id}"]')
        
        # Analyser chaque élément avec l'ID dupliqué
        for el in elements_with_id:
            tag_name = el.tag_name.lower()
            role = el.get_attribute('role')
            aria_live = el.get_attribute('aria-live')
            aria_labelledby = el.get_attribute('aria-labelledby')
            aria_describedby = el.get_attribute('aria-describedby')
            
            # Catégorie 1: ID dupliqué pour un label, titre ou bloc ARIA
            is_label = tag_name == 'label'
            is_title = tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
            is_aria_block = role is not None or any([
                el.get_attribute('aria-label'),
                el.get_attribute('aria-labelledby'),
                el.get_attribute('aria-describedby'),
                el.get_attribute('aria-controls'),
                el.get_attribute('aria-owns')
            ])
            
            if is_label or is_title or is_aria_block or len(labels_using_id) > 0:
                impacts.append({
                    "categorie": "Label, titre ou bloc ARIA",
                    "impact": "Le lecteur d'écran ne lit pas le bon texte",
                    "severity": "critical"
                })
            
            # Catégorie 2: ID dupliqué pour un lien interne ou bouton
            is_link = tag_name == 'a' or role == 'link'
            is_button = tag_name == 'button' or role == 'button' or role == 'menuitem'
            href = el.get_attribute('href')
            # Lien interne = ancre (#) ou lien relatif (sans http/https)
            is_internal_link = is_link and href and (href.startswith('#') or (not href.startswith('http://') and not href.startswith('https://')))
            
            if (is_link and is_internal_link) or is_button:
                impacts.append({
                    "categorie": "Lien interne ou bouton",
                    "impact": "Mauvais focus / zone non atteinte",
                    "severity": "critical"
                })
            
            # Catégorie 3: ID dupliqué dans une zone dynamique
            if aria_live and aria_live in ['polite', 'assertive', 'off']:
                impacts.append({
                    "categorie": "Zone dynamique (aria-live)",
                    "impact": "Annonces incohérentes ou non lues",
                    "severity": "critical"
                })
            
            # Vérifier si l'ID est référencé par d'autres attributs ARIA
            for attr in referenced_attributes:
                elements_referencing = self.driver.find_elements(
                    By.XPATH, f'//*[contains(@{attr}, "{duplicate_id}")]'
                )
                if elements_referencing:
                    impacts.append({
                        "categorie": "Référence ARIA",
                        "impact": "Arborescence d'accessibilité corrompue",
                        "severity": "critical",
                        "details": f"ID référencé par l'attribut {attr}"
                    })
        
        # Si l'ID est référencé par plusieurs éléments, c'est un problème d'arborescence
        total_references = len(labels_using_id)
        for attr in referenced_attributes:
            total_references += len(self.driver.find_elements(
                By.XPATH, f'//*[contains(@{attr}, "{duplicate_id}")]'
            ))
        
        if total_references > 0 and len(elements_with_id) > 1:
            impacts.append({
                "categorie": "Référence multiple dans le DOM",
                "impact": "Arborescence d'accessibilité corrompue",
                "severity": "critical"
            })
        
        # Dédupliquer les impacts
        seen = set()
        unique_impacts = []
        for impact in impacts:
            key = (impact["categorie"], impact["impact"])
            if key not in seen:
                seen.add(key)
                unique_impacts.append(impact)
        
        return unique_impacts if unique_impacts else [{
            "categorie": "ID dupliqué général",
            "impact": "Violation de l'unicité des IDs dans le DOM",
            "severity": "high"
        }]

    def _check_duplicate_ids(self):
        """Vérifie l'unicité des attributs id dans la page et analyse l'impact sur l'accessibilité"""
        id_map = defaultdict(list)
        # Récupérer tous les éléments avec un id
        elements = self.driver.find_elements(By.XPATH, '//*[@id]')
        for el in elements:
            eid = el.get_attribute('id')
            if eid:
                id_map[eid].append(el)
        # Chercher les ids dupliqués et analyser leur impact
        for eid, els in id_map.items():
            if len(els) > 1:
                # Analyser l'impact spécifique de cet ID dupliqué
                impacts = self._analyze_duplicate_id_impact(eid, els)
                
                for el in els:
                    main_xpath, _ = self._get_xpath(el)
                    
                    # Construire la description des impacts
                    impact_descriptions = []
                    for impact in impacts:
                        impact_descriptions.append(
                            f"{impact['categorie']}: {impact['impact']}"
                        )
                    
                    impact_text = " | ".join(impact_descriptions) if impact_descriptions else "Impact non spécifique"
                    
                    # Déterminer la sévérité la plus élevée
                    max_severity = max([imp.get('severity', 'medium') for imp in impacts], 
                                      key=lambda x: {'critical': 3, 'high': 2, 'medium': 1}.get(x, 0))
                    
                    self.non_conformites["duplicate_id"].append({
                        "type": f"Attribut id dupliqué : '{eid}'",
                        "element": self._get_simple_selector(el),
                        "xpath": main_xpath,
                        "impact": impact_text,
                        "severity": max_severity,
                        "recommandation": f"L'attribut id '{eid}' doit être unique dans la page. {impact_text}"
                    })

    def _print_progress(self, current, total, prefix="", suffix="", length=50, fill="="):
        """Barre de progression : uniquement en --debug (évite le mélange avec les logs structurés)."""
        if not self.logger.isEnabledFor(logging.DEBUG):
            return
        percent = f"{100 * (current / float(total)):.1f}"
        filled_length = int(length * current // total)
        bar = fill * filled_length + '-' * (length - filled_length)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='', flush=True)
        if current == total:
            print()

    def _write_accessibility_csv(self):
        """Écriture atomique ; repli si le fichier cible est verrouillé (ex. ouvert dans Excel)."""
        path = "reports/accessibility_analysis.csv"
        os.makedirs("reports", exist_ok=True)
        body = "\n".join(self.csv_lines)
        try:
            fd, tmp_path = tempfile.mkstemp(prefix="acc_", suffix=".csv", dir="reports")
            try:
                with os.fdopen(fd, "w", encoding="utf-8-sig", newline="") as f:
                    f.write(body)
                os.replace(tmp_path, path)
            except Exception:
                if os.path.isfile(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
                raise
        except (PermissionError, OSError) as e:
            if not isinstance(e, PermissionError) and getattr(e, "errno", None) != 13:
                raise
            alt = os.path.join(
                "reports",
                f"accessibility_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            )
            with open(alt, "w", encoding="utf-8-sig", newline="") as f:
                f.write(body)
            log_with_step(
                self.logger,
                logging.WARNING,
                "SCREEN",
                f"Fichier verrouillé, impossible d'écrire {path}. Données enregistrées dans : {alt}",
            )

    def _log_aria_attributes(self):
        """Affiche les attributs ARIA stockés pendant l'analyse"""
        if hasattr(self, '_aria_attrs_to_log') and self._aria_attrs_to_log:
            self.logger.info("### Attributs ARIA définis")
            for element_type, aria_attrs in self._aria_attrs_to_log:
                for attr, value in aria_attrs.items():
                    self.logger.debug(f"✓ {attr}: {value}")
            # Nettoyer la liste après affichage
            self._aria_attrs_to_log = []

    def _analyze_links_integrated(self, links):
        """Analyse intégrée des liens - combine analyse des non-conformités et génération CSV en une seule passe"""
        # Traitement par lots pour réduire les appels JavaScript
        batch_size = 20
        total_links = len(links)
        
        for batch_start in range(0, total_links, batch_size):
            batch_end = min(batch_start + batch_size, total_links)
            batch = links[batch_start:batch_end]
            
            # Récupération groupée des attributs pour tout le lot
            batch_attrs = self.driver.execute_script('''
                var links = arguments[0];
                var results = [];
                for (var i = 0; i < links.length; i++) {
                    var el = links[i];
                    var rect = el.getBoundingClientRect();
                    var style = window.getComputedStyle(el);
                    // positions
                    var domIndex = (function(){
                        try {
                            var parent = el.parentNode;
                            if (!parent) return -1;
                            var children = Array.prototype.filter.call(parent.children, function(c){ return c.nodeType === 1; });
                            for (var k=0;k<children.length;k++){ if (children[k]===el) return k+1; }
                            return -1;
                        } catch (e){ return -1; }
                    })();
                    var parentIndex = (function(){
                        try {
                            var parent = el.parentNode;
                            if (!parent || !parent.parentNode) return -1;
                            var siblings = Array.prototype.filter.call(parent.parentNode.children, function(c){ return c.nodeType === 1; });
                            for (var k=0;k<siblings.length;k++){ if (siblings[k]===parent) return k+1; }
                            return -1;
                        } catch (e){ return -1; }
                    })();
                    var doc = el.ownerDocument || document;
                    var absIndex = (function(){
                        try {
                            var all = doc.querySelectorAll('*');
                            for (var k=0;k<all.length;k++){ if (all[k]===el) return k+1; }
                            return -1;
                        } catch (e){ return -1; }
                    })();
                    var parentAbsIndex = (function(){
                        try {
                            var parent = el.parentNode;
                            if (!parent || parent.nodeType !== 1) return -1;
                            var all = doc.querySelectorAll('*');
                            for (var k=0;k<all.length;k++){ if (all[k]===parent) return k+1; }
                            return -1;
                        } catch (e){ return -1; }
                    })();
                    results.push({
                        tag: el.tagName,
                        role: el.getAttribute('role'),
                        ariaLabel: el.getAttribute('aria-label'),
                        ariaDescribedby: el.getAttribute('aria-describedby'),
                        ariaLabelledby: el.getAttribute('aria-labelledby'),
                        ariaHidden: el.getAttribute('aria-hidden'),
                        ariaExpanded: el.getAttribute('aria-expanded'),
                        ariaControls: el.getAttribute('aria-controls'),
                        ariaLive: el.getAttribute('aria-live'),
                        ariaAtomic: el.getAttribute('aria-atomic'),
                        ariaRelevant: el.getAttribute('aria-relevant'),
                        ariaBusy: el.getAttribute('aria-busy'),
                        ariaCurrent: el.getAttribute('aria-current'),
                        ariaPosinset: el.getAttribute('aria-posinset'),
                        ariaSetsize: el.getAttribute('aria-setsize'),
                        ariaLevel: el.getAttribute('aria-level'),
                        ariaSort: el.getAttribute('aria-sort'),
                        ariaValuemin: el.getAttribute('aria-valuemin'),
                        ariaValuemax: el.getAttribute('aria-valuemax'),
                        ariaValuenow: el.getAttribute('aria-valuenow'),
                        ariaValuetext: el.getAttribute('aria-valuetext'),
                        ariaHaspopup: el.getAttribute('aria-haspopup'),
                        ariaInvalid: el.getAttribute('aria-invalid'),
                        ariaRequired: el.getAttribute('aria-required'),
                        ariaReadonly: el.getAttribute('aria-readonly'),
                        ariaDisabled: el.getAttribute('aria-disabled'),
                        ariaSelected: el.getAttribute('aria-selected'),
                        ariaChecked: el.getAttribute('aria-checked'),
                        ariaPressed: el.getAttribute('aria-pressed'),
                        ariaMultiline: el.getAttribute('aria-multiline'),
                        ariaMultiselectable: el.getAttribute('aria-multiselectable'),
                        ariaOrientation: el.getAttribute('aria-orientation'),
                        ariaPlaceholder: el.getAttribute('aria-placeholder'),
                        ariaRoledescription: el.getAttribute('aria-roledescription'),
                        ariaKeyshortcuts: el.getAttribute('aria-keyshortcuts'),
                        ariaDetails: el.getAttribute('aria-details'),
                        ariaErrormessage: el.getAttribute('aria-errormessage'),
                        ariaFlowto: el.getAttribute('aria-flowto'),
                        ariaOwns: el.getAttribute('aria-owns'),
                        tabindex: el.getAttribute('tabindex'),
                        title: el.getAttribute('title'),
                        alt: el.getAttribute('alt'),
                        id: el.getAttribute('id'),
                        className: el.getAttribute('class'),
                        text: el.textContent ? el.textContent.trim() : '',
                        href: el.getAttribute('href'),
                        isVisible: !(style.display === 'none' || style.visibility === 'hidden' || rect.width === 0 || rect.height === 0),
                        isEnabled: !el.disabled,
                        isFocusable: el.tabIndex >= 0 || el.tagName === 'A' || el.tagName === 'BUTTON' || el.tagName === 'INPUT' || el.tagName === 'SELECT' || el.tagName === 'TEXTAREA',
                        mediaPath: el.getAttribute('src') || el.getAttribute('data') || '',
                        mediaType: el.tagName.toLowerCase(),
                        outerHTML: el.outerHTML,
                        domIndex: domIndex,
                        parentIndex: parentIndex,
                        absIndex: (typeof absIndex !== 'undefined' ? absIndex : -1),
                        parentAbsIndex: (typeof parentAbsIndex !== 'undefined' ? parentAbsIndex : -1)
                    });
                }
                return results;
            ''', batch)
            
            # Traitement des résultats du lot
            for j, attrs in enumerate(batch_attrs):
                try:
                    # Construction du dictionnaire d'informations
                    info = {
                        "Type": attrs['tag'],
                        "Rôle": attrs['role'] or "non défini",
                        "Aria-label": attrs['ariaLabel'] or "non défini",
                        "Aria-describedby": attrs['ariaDescribedby'] or "non défini",
                        "Aria-labelledby": attrs['ariaLabelledby'] or "non défini",
                        "Aria-hidden": attrs['ariaHidden'] or "non défini",
                        "Aria-expanded": attrs['ariaExpanded'] or "non défini",
                        "Aria-controls": attrs['ariaControls'] or "non défini",
                        "Aria-live": attrs['ariaLive'] or "non défini",
                        "Aria-atomic": attrs['ariaAtomic'] or "non défini",
                        "Aria-relevant": attrs['ariaRelevant'] or "non défini",
                        "Aria-busy": attrs['ariaBusy'] or "non défini",
                        "Aria-current": attrs['ariaCurrent'] or "non défini",
                        "Aria-posinset": attrs['ariaPosinset'] or "non défini",
                        "Aria-setsize": attrs['ariaSetsize'] or "non défini",
                        "Aria-level": attrs['ariaLevel'] or "non défini",
                        "Aria-sort": attrs['ariaSort'] or "non défini",
                        "Aria-valuemin": attrs['ariaValuemin'] or "non défini",
                        "Aria-valuemax": attrs['ariaValuemax'] or "non défini",
                        "Aria-valuenow": attrs['ariaValuenow'] or "non défini",
                        "Aria-valuetext": attrs['ariaValuetext'] or "non défini",
                        "Aria-haspopup": attrs['ariaHaspopup'] or "non défini",
                        "Aria-invalid": attrs['ariaInvalid'] or "non défini",
                        "Aria-required": attrs['ariaRequired'] or "non défini",
                        "Aria-readonly": attrs['ariaReadonly'] or "non défini",
                        "Aria-disabled": attrs['ariaDisabled'] or "non défini",
                        "Aria-selected": attrs['ariaSelected'] or "non défini",
                        "Aria-checked": attrs['ariaChecked'] or "non défini",
                        "Aria-pressed": attrs['ariaPressed'] or "non défini",
                        "Aria-multiline": attrs['ariaMultiline'] or "non défini",
                        "Aria-multiselectable": attrs['ariaMultiselectable'] or "non défini",
                        "Aria-orientation": attrs['ariaOrientation'] or "non défini",
                        "Aria-placeholder": attrs['ariaPlaceholder'] or "non défini",
                        "Aria-roledescription": attrs['ariaRoledescription'] or "non défini",
                        "Aria-keyshortcuts": attrs['ariaKeyshortcuts'] or "non défini",
                        "Aria-details": attrs['ariaDetails'] or "non défini",
                        "Aria-errormessage": attrs['ariaErrormessage'] or "non défini",
                        "Aria-flowto": attrs['ariaFlowto'] or "non défini",
                        "Aria-owns": attrs['ariaOwns'] or "non défini",
                        "Tabindex": attrs['tabindex'] or "non défini",
                        "Title": attrs['title'] or "non défini",
                        "Alt": attrs['alt'] or "non défini",
                        "Text": attrs['text'] or "non défini",
                        "Visible": "Oui" if attrs['isVisible'] else "Non",
                        "Focusable": "Oui" if attrs['isFocusable'] else "Non",
                        "Id": attrs['id'] or "non défini",
                        "Sélecteur": self._get_simple_selector_from_attrs(attrs),
                        "Extrait HTML": (attrs['outerHTML'] or '')[:200] + '...',
                        "MediaPath": attrs['mediaPath'] or "non défini",
                        "MediaType": attrs['mediaType'] or "non défini",
                        # Positions DOM si fournies
                        "Dom-absolute-position": attrs.get('absIndex') if isinstance(attrs, dict) and 'absIndex' in attrs else ("non défini"),
                        "Parent-absolute-position": attrs.get('parentAbsIndex') if isinstance(attrs, dict) and 'parentAbsIndex' in attrs else ("non défini"),
                        "Dom-position": attrs.get('domIndex') if isinstance(attrs, dict) and 'domIndex' in attrs else ("non défini"),
                        "Parent-position": attrs.get('parentIndex') if isinstance(attrs, dict) and 'parentIndex' in attrs else ("non défini")
                    }
                    
                    # Génération de XPath simplifiés (éviter les appels coûteux)
                    main_xpath = f"//a[@id='{attrs['id']}']" if attrs['id'] else f"//a[contains(@class, '{attrs['className'].split()[0]}')]" if attrs['className'] else "//a"
                    secondary_xpath1 = f"//a[contains(text(), '{attrs['text'][:30]}')]" if attrs['text'] and len(attrs['text']) < 50 else ""
                    secondary_xpath2 = f"//a[@href='{attrs['href']}']" if attrs['href'] else ""
                    
                    info["main_xpath"] = main_xpath
                    info["secondary_xpath1"] = secondary_xpath1
                    info["secondary_xpath2"] = secondary_xpath2
                    
                    # Génération de sélecteurs CSS alternatifs
                    css_selectors = self.css_generator.generate_css_selectors_from_attrs(attrs)
                    info["main_css"] = css_selectors["main_css"]
                    info["secondary_css1"] = css_selectors["secondary_css1"]
                    info["secondary_css2"] = css_selectors["secondary_css2"]
                    
                    # Ajouter le contexte de frame
                    info["Frame-src"] = getattr(self, '_current_frame_src', "")
                    info["Frame-index"] = getattr(self, '_current_frame_index', -1)

                    # Construction de la ligne CSV avec toutes les données ARIA
                    row = [
                        self._clean_csv_field(info["Type"]),
                        self._clean_csv_field(info["Sélecteur"]),
                        self._clean_csv_field(info["Extrait HTML"]),
                        self._clean_csv_field(info["Rôle"]),
                        self._clean_csv_field(info["Aria-label"]),
                        self._clean_csv_field(info["Text"]),
                        self._clean_csv_field(info["Alt"]),
                        self._clean_csv_field(info["Title"]),
                        self._clean_csv_field(info["Visible"]),
                        self._clean_csv_field(info["Focusable"]),
                        self._clean_csv_field(info["Id"]),
                        # Nouvelles colonnes ARIA pour les outils de narration
                        self._clean_csv_field(info["Aria-describedby"]),
                        self._clean_csv_field(info["Aria-labelledby"]),
                        self._clean_csv_field(info["Aria-hidden"]),
                        self._clean_csv_field(info["Aria-expanded"]),
                        self._clean_csv_field(info["Aria-controls"]),
                        self._clean_csv_field(info["Aria-live"]),
                        self._clean_csv_field(info["Aria-atomic"]),
                        self._clean_csv_field(info["Aria-relevant"]),
                        self._clean_csv_field(info["Aria-busy"]),
                        self._clean_csv_field(info["Aria-current"]),
                        self._clean_csv_field(info["Aria-posinset"]),
                        self._clean_csv_field(info["Aria-setsize"]),
                        self._clean_csv_field(info["Aria-level"]),
                        self._clean_csv_field(info["Aria-sort"]),
                        self._clean_csv_field(info["Aria-valuemin"]),
                        self._clean_csv_field(info["Aria-valuemax"]),
                        self._clean_csv_field(info["Aria-valuenow"]),
                        self._clean_csv_field(info["Aria-valuetext"]),
                        self._clean_csv_field(info["Aria-haspopup"]),
                        self._clean_csv_field(info["Aria-invalid"]),
                        self._clean_csv_field(info["Aria-required"]),
                        self._clean_csv_field(info["Aria-readonly"]),
                        self._clean_csv_field(info["Aria-disabled"]),
                        self._clean_csv_field(info["Aria-selected"]),
                        self._clean_csv_field(info["Aria-checked"]),
                        self._clean_csv_field(info["Aria-pressed"]),
                        self._clean_csv_field(info["Aria-multiline"]),
                        self._clean_csv_field(info["Aria-multiselectable"]),
                        self._clean_csv_field(info["Aria-orientation"]),
                        self._clean_csv_field(info["Aria-placeholder"]),
                        self._clean_csv_field(info["Aria-roledescription"]),
                        self._clean_csv_field(info["Aria-keyshortcuts"]),
                        self._clean_csv_field(info["Aria-details"]),
                        self._clean_csv_field(info["Aria-errormessage"]),
                        self._clean_csv_field(info["Aria-flowto"]),
                        self._clean_csv_field(info["Aria-owns"]),
                    self._clean_csv_field(info["Tabindex"]),
                    # Positions DOM
                    self._clean_csv_field(info.get("Dom-absolute-position", "")),
                    self._clean_csv_field(info.get("Parent-absolute-position", "")),
                    self._clean_csv_field(info.get("Dom-position", "")),
                    self._clean_csv_field(info.get("Parent-position", "")),
                    # Contexte iframe
                    self._clean_csv_field(info.get("Frame-src", "")),
                    self._clean_csv_field(info.get("Frame-index", "")),
                    self._clean_csv_field(info["main_xpath"]),
                    self._clean_csv_field(info.get("xpath_complet", "")),
                    self._clean_csv_field(info["secondary_xpath1"]),
                    self._clean_csv_field(info["secondary_xpath2"]),
                    # Sélecteurs CSS alternatifs
                    self._clean_csv_field(info["main_css"]),
                    self._clean_csv_field(info["secondary_css1"]),
                    self._clean_csv_field(info["secondary_css2"])
                    ]
                    self.csv_lines.append(';'.join(row))
                    
                    # Analyse des non-conformités
                    self._analyze_non_conformites(info, "Lien", batch[j])
                    
                    # Stocker les attributs ARIA pour affichage après la progression
                    aria_attrs = {k: v for k, v in info.items() if k.startswith("Aria-") and v != "non défini"}
                    if aria_attrs:
                        if not hasattr(self, '_aria_attrs_to_log'):
                            self._aria_attrs_to_log = []
                        self._aria_attrs_to_log.append(("Lien", aria_attrs))
                    
                    # Affichage de la progression
                    current_index = batch_start + j + 1
                    self._print_progress(current_index, total_links, prefix=f"Analyse Liens:", suffix=f"{current_index}/{total_links}")
                        
                except Exception as e:
                    self.logger.debug(f"Erreur lors de l'analyse du lien : {str(e)}")
                    continue

    def _get_simple_selector_from_attrs(self, attrs):
        """Génère un sélecteur simple à partir des attributs récupérés"""
        tag = attrs['tag'].lower()
        classes = attrs['className']
        if classes:
            return f"{tag}.{'.'.join(classes.split())}"
        return tag

    def _analyze_elements_integrated(self, elements, category_name):
        """Analyse intégrée pour toutes les catégories - combine analyse des non-conformités et génération CSV.
        Les XPath complets sont calculés après tous les lots à partir des positions absolues (performances)."""
        batch_size = 20
        total_elements = len(elements)
        rows_data = []  # (info, row_list, attrs) pour XPath complet + rapport DOM batch

        for batch_start in range(0, total_elements, batch_size):
            batch_end = min(batch_start + batch_size, total_elements)
            batch = elements[batch_start:batch_end]

            # Récupération groupée (script partagé avec DOMAnalyzer — voir dom_accessibility_from_batch)
            batch_attrs = self.driver.execute_script(DOM_BATCH_EXTRACT_SCRIPT, batch) or []
            
            # Traitement des résultats du lot
            for j, attrs in enumerate(batch_attrs):
                try:
                    # Construction du dictionnaire d'informations
                    info = {
                        "Type": attrs['tag'],
                        "Rôle": attrs['role'] or "non défini",
                        "Aria-label": attrs['ariaLabel'] or "non défini",
                        "Aria-describedby": attrs['ariaDescribedby'] or "non défini",
                        "Aria-labelledby": attrs['ariaLabelledby'] or "non défini",
                        "Aria-hidden": attrs['ariaHidden'] or "non défini",
                        "Aria-expanded": attrs['ariaExpanded'] or "non défini",
                        "Aria-controls": attrs['ariaControls'] or "non défini",
                        "Aria-live": attrs['ariaLive'] or "non défini",
                        "Aria-atomic": attrs['ariaAtomic'] or "non défini",
                        "Aria-relevant": attrs['ariaRelevant'] or "non défini",
                        "Aria-busy": attrs['ariaBusy'] or "non défini",
                        "Aria-current": attrs['ariaCurrent'] or "non défini",
                        "Aria-posinset": attrs['ariaPosinset'] or "non défini",
                        "Aria-setsize": attrs['ariaSetsize'] or "non défini",
                        "Aria-level": attrs['ariaLevel'] or "non défini",
                        "Aria-sort": attrs['ariaSort'] or "non défini",
                        "Aria-valuemin": attrs['ariaValuemin'] or "non défini",
                        "Aria-valuemax": attrs['ariaValuemax'] or "non défini",
                        "Aria-valuenow": attrs['ariaValuenow'] or "non défini",
                        "Aria-valuetext": attrs['ariaValuetext'] or "non défini",
                        "Aria-haspopup": attrs['ariaHaspopup'] or "non défini",
                        "Aria-invalid": attrs['ariaInvalid'] or "non défini",
                        "Aria-required": attrs['ariaRequired'] or "non défini",
                        "Aria-readonly": attrs['ariaReadonly'] or "non défini",
                        "Aria-disabled": attrs['ariaDisabled'] or "non défini",
                        "Aria-selected": attrs['ariaSelected'] or "non défini",
                        "Aria-checked": attrs['ariaChecked'] or "non défini",
                        "Aria-pressed": attrs['ariaPressed'] or "non défini",
                        "Aria-multiline": attrs['ariaMultiline'] or "non défini",
                        "Aria-multiselectable": attrs['ariaMultiselectable'] or "non défini",
                        "Aria-orientation": attrs['ariaOrientation'] or "non défini",
                        "Aria-placeholder": attrs['ariaPlaceholder'] or "non défini",
                        "Aria-roledescription": attrs['ariaRoledescription'] or "non défini",
                        "Aria-keyshortcuts": attrs['ariaKeyshortcuts'] or "non défini",
                        "Aria-details": attrs['ariaDetails'] or "non défini",
                        "Aria-errormessage": attrs['ariaErrormessage'] or "non défini",
                        "Aria-flowto": attrs['ariaFlowto'] or "non défini",
                        "Aria-owns": attrs['ariaOwns'] or "non défini",
                        "Tabindex": attrs['tabindex'] or "non défini",
                        "Title": attrs['title'] or "non défini",
                        "Alt": attrs['alt'] or "non défini",
                        "Text": attrs['text'] or "non défini",
                        "Visible": "Oui" if attrs['isVisible'] else "Non",
                        "Focusable": "Oui" if attrs['isFocusable'] else "Non",
                        "Id": attrs['id'] or "non défini",
                        "Sélecteur": self._get_simple_selector_from_attrs(attrs),
                        "Extrait HTML": (attrs['outerHTML'] or '')[:200] + '...',
                        "MediaPath": attrs['mediaPath'] or "non défini",
                        "MediaType": attrs['mediaType'] or "non défini",
                        # Positions DOM si fournies
                        "Dom-absolute-position": attrs.get('absIndex') if isinstance(attrs, dict) and 'absIndex' in attrs else ("non défini"),
                        "Parent-absolute-position": attrs.get('parentAbsIndex') if isinstance(attrs, dict) and 'parentAbsIndex' in attrs else ("non défini"),
                        "Dom-position": attrs.get('domIndex') if isinstance(attrs, dict) and 'domIndex' in attrs else ("non défini"),
                        "Parent-position": attrs.get('parentIndex') if isinstance(attrs, dict) and 'parentIndex' in attrs else ("non défini")
                    }
                    
                    # XPath pendant les lots : simple (chemin complet calculé après tous les lots)
                    info["main_xpath"] = self._generate_simple_xpath(attrs)
                    info["secondary_xpath1"] = self._generate_secondary_xpath1(attrs)
                    info["secondary_xpath2"] = self._generate_secondary_xpath2(attrs)
                    
                    # Génération de sélecteurs CSS alternatifs
                    css_selectors = self.css_generator.generate_css_selectors_from_attrs(attrs)
                    info["main_css"] = css_selectors["main_css"]
                    info["secondary_css1"] = css_selectors["secondary_css1"]
                    info["secondary_css2"] = css_selectors["secondary_css2"]
                    
                    # Ajouter le contexte de frame
                    info["Frame-src"] = getattr(self, '_current_frame_src', "")
                    info["Frame-index"] = getattr(self, '_current_frame_index', -1)

                    # Construction de la ligne CSV avec toutes les données ARIA
                    row = [
                        self._clean_csv_field(info["Type"]),
                        self._clean_csv_field(info["Sélecteur"]),
                        self._clean_csv_field(info["Extrait HTML"]),
                        self._clean_csv_field(info["Rôle"]),
                        self._clean_csv_field(info["Aria-label"]),
                        self._clean_csv_field(info["Text"]),
                        self._clean_csv_field(info["Alt"]),
                        self._clean_csv_field(info["Title"]),
                        self._clean_csv_field(info["Visible"]),
                        self._clean_csv_field(info["Focusable"]),
                        self._clean_csv_field(info["Id"]),
                        # Nouvelles colonnes ARIA pour les outils de narration
                        self._clean_csv_field(info["Aria-describedby"]),
                        self._clean_csv_field(info["Aria-labelledby"]),
                        self._clean_csv_field(info["Aria-hidden"]),
                        self._clean_csv_field(info["Aria-expanded"]),
                        self._clean_csv_field(info["Aria-controls"]),
                        self._clean_csv_field(info["Aria-live"]),
                        self._clean_csv_field(info["Aria-atomic"]),
                        self._clean_csv_field(info["Aria-relevant"]),
                        self._clean_csv_field(info["Aria-busy"]),
                        self._clean_csv_field(info["Aria-current"]),
                        self._clean_csv_field(info["Aria-posinset"]),
                        self._clean_csv_field(info["Aria-setsize"]),
                        self._clean_csv_field(info["Aria-level"]),
                        self._clean_csv_field(info["Aria-sort"]),
                        self._clean_csv_field(info["Aria-valuemin"]),
                        self._clean_csv_field(info["Aria-valuemax"]),
                        self._clean_csv_field(info["Aria-valuenow"]),
                        self._clean_csv_field(info["Aria-valuetext"]),
                        self._clean_csv_field(info["Aria-haspopup"]),
                        self._clean_csv_field(info["Aria-invalid"]),
                        self._clean_csv_field(info["Aria-required"]),
                        self._clean_csv_field(info["Aria-readonly"]),
                        self._clean_csv_field(info["Aria-disabled"]),
                        self._clean_csv_field(info["Aria-selected"]),
                        self._clean_csv_field(info["Aria-checked"]),
                        self._clean_csv_field(info["Aria-pressed"]),
                        self._clean_csv_field(info["Aria-multiline"]),
                        self._clean_csv_field(info["Aria-multiselectable"]),
                        self._clean_csv_field(info["Aria-orientation"]),
                        self._clean_csv_field(info["Aria-placeholder"]),
                        self._clean_csv_field(info["Aria-roledescription"]),
                        self._clean_csv_field(info["Aria-keyshortcuts"]),
                        self._clean_csv_field(info["Aria-details"]),
                        self._clean_csv_field(info["Aria-errormessage"]),
                        self._clean_csv_field(info["Aria-flowto"]),
                        self._clean_csv_field(info["Aria-owns"]),
                        self._clean_csv_field(info["Tabindex"]),
                        # Positions DOM
                        self._clean_csv_field(info.get("Dom-absolute-position", "")),
                        self._clean_csv_field(info.get("Parent-absolute-position", "")),
                        self._clean_csv_field(info.get("Dom-position", "")),
                        self._clean_csv_field(info.get("Parent-position", "")),
                        # Contexte iframe
                        self._clean_csv_field(info.get("Frame-src", "")),
                        self._clean_csv_field(info.get("Frame-index", "")),
                        self._clean_csv_field(info["main_xpath"]),
                        self._clean_csv_field(info.get("xpath_complet", "")),
                        self._clean_csv_field(info["secondary_xpath1"]),
                        self._clean_csv_field(info["secondary_xpath2"]),
                        # Sélecteurs CSS alternatifs
                        self._clean_csv_field(info["main_css"]),
                        self._clean_csv_field(info["secondary_css1"]),
                        self._clean_csv_field(info["secondary_css2"])
                    ]
                    an = attrs.get("accessibleName") or {}
                    rpg = attrs.get("rectPage") or {}
                    cs = attrs.get("computedStyle") or {}
                    style_short = " ".join(
                        x for x in (cs.get("display"), cs.get("visibility"), cs.get("opacity")) if x
                    ).strip()
                    rect_s = ""
                    if isinstance(rpg, dict) and rpg:
                        rect_s = f"{rpg.get('x', '')},{rpg.get('y', '')},{rpg.get('width', '')},{rpg.get('height', '')}"
                    row.extend([
                        self._clean_csv_field((attrs.get("innerText") or "").strip()),
                        self._clean_csv_field(attrs.get("nameAttr") or ""),
                        self._clean_csv_field(attrs.get("inputType") or ""),
                        self._clean_csv_field(attrs.get("value") or ""),
                        self._clean_csv_field(attrs.get("placeholder") or ""),
                        self._clean_csv_field("Oui" if attrs.get("hasLabelFor") else "Non"),
                        self._clean_csv_field(an.get("name", "")),
                        self._clean_csv_field(an.get("source", "")),
                        self._clean_csv_field("Oui" if attrs.get("isDisplayed") else "Non"),
                        self._clean_csv_field(rect_s or "non défini"),
                        self._clean_csv_field(style_short or "non défini"),
                    ])
                    rows_data.append((info, row, attrs))
                    try:
                        sk = self._get_shared_element_key(batch[j])
                        self.aria_data_by_element[sk] = info
                    except Exception:
                        pass

                    # Analyse des non-conformités (avec XPath simple ; le CSV aura le XPath complet)
                    self._analyze_non_conformites(info, category_name, batch[j])
                    
                    # Stocker les attributs ARIA pour affichage après la progression
                    aria_attrs = {k: v for k, v in info.items() if k.startswith("Aria-") and v != "non défini"}
                    if aria_attrs:
                        if not hasattr(self, '_aria_attrs_to_log'):
                            self._aria_attrs_to_log = []
                        self._aria_attrs_to_log.append((category_name, aria_attrs))
                    
                    # Affichage de la progression
                    current_index = batch_start + j + 1
                    self._print_progress(current_index, total_elements, prefix=f"Analyse {category_name}:", suffix=f"{current_index}/{total_elements}")
                        
                except Exception as e:
                    self.logger.debug(f"Erreur lors de l'analyse de l'élément {category_name}: {str(e)}")
                    continue

        # Après tous les lots : calcul des XPath complets à partir des positions absolues (un seul appel JS)
        if rows_data:
            abs_indices = [info.get("Dom-absolute-position") for info, _, _ in rows_data]
            full_xpaths = self._compute_full_xpaths_from_abs_indices(abs_indices)
            header_parts = self.csv_lines[0].split(";")
            try:
                ix_xpath_simple = header_parts.index("X-path simplifié")
                ix_xpath_full = header_parts.index("X-path complet")
            except ValueError:
                ix_xpath_simple = ix_xpath_full = None
            for i, (info, row_list, attrs) in enumerate(rows_data):
                xp = ""
                if i < len(full_xpaths) and full_xpaths[i]:
                    xp = full_xpaths[i]
                if xp:
                    info["main_xpath"] = xp
                    if ix_xpath_simple is not None and ix_xpath_simple < len(row_list):
                        row_list[ix_xpath_simple] = self._clean_csv_field(xp)
                    if ix_xpath_full is not None and ix_xpath_full < len(row_list):
                        row_list[ix_xpath_full] = self._clean_csv_field(xp)
                if self.emit_dom_rapport:
                    rec = build_dom_element_record(
                        attrs, info["main_xpath"], stable_css_selector_from_attrs(attrs)
                    )
                    check_accessibility_issues_from_dict(rec, self._dom_report_issues)
                    self._dom_report_elements.append(rec)
                self.csv_lines.append(";".join(row_list))

    def _compute_full_xpaths_from_abs_indices(self, abs_indices):
        """Calcule les XPath absolus complets à partir des positions absolues (un seul appel JS)."""
        if not abs_indices:
            return []
        try:
            # Nettoyer : ne garder que les indices numériques valides (1-based)
            indices = []
            for v in abs_indices:
                if v is None or v == "non défini":
                    indices.append(-1)
                else:
                    try:
                        n = int(v)
                        indices.append(n if n >= 1 else -1)
                    except (TypeError, ValueError):
                        indices.append(-1)
            xpaths = self.driver.execute_script('''
                var indices = arguments[0];
                var all = document.querySelectorAll("*");
                var result = [];
                function getPathForElement(el) {
                    var path = [];
                    var current = el;
                    while (current && current.nodeType === 1) {
                        var tag = current.tagName.toLowerCase();
                        if (tag === "html") break;
                        var parent = current.parentNode;
                        if (!parent) break;
                        var sameTag = 0;
                        for (var i = 0; i < parent.children.length; i++) {
                            var c = parent.children[i];
                            if (c.tagName && c.tagName.toLowerCase() === tag) {
                                sameTag++;
                                if (c === current) break;
                            }
                        }
                        path.unshift(tag + "[" + sameTag + "]");
                        current = parent;
                    }
                    return path.length ? "/html/" + path.join("/") : "";
                }
                for (var k = 0; k < indices.length; k++) {
                    var idx = indices[k];
                    if (typeof idx !== "number" || idx < 1 || idx > all.length) {
                        result.push("");
                        continue;
                    }
                    var el = all[idx - 1];
                    result.push(getPathForElement(el));
                }
                return result;
            ''', indices)
            return xpaths if isinstance(xpaths, list) else []
        except Exception as e:
            self.logger.debug(f"Calcul XPath par positions absolues : {e}")
            return []

    def _generate_simple_xpath(self, attrs):
        """Génère un XPath simple basé sur les attributs"""
        tag = attrs['tag'].lower()
        element_id = attrs['id']
        class_name = attrs['className']
        
        if element_id:
            return f"//{tag}[@id='{element_id}']"
        elif class_name:
            first_class = class_name.split()[0]
            return f"//{tag}[contains(@class, '{first_class}')]"
        else:
            return f"//{tag}"

    def _generate_secondary_xpath1(self, attrs):
        """Génère un XPath secondaire basé sur le texte"""
        tag = attrs['tag'].lower()
        text = attrs['text']
        
        if text and len(text) < 50:
            return f"//{tag}[contains(text(), '{text[:30]}')]"
        return ""

    def _generate_secondary_xpath2(self, attrs):
        """Génère un XPath secondaire basé sur les attributs spécifiques"""
        tag = attrs['tag'].lower()
        href = attrs['href']
        src = attrs['src']
        
        if href:
            return f"//{tag}[@href='{href}']"
        elif src:
            return f"//{tag}[@src='{src}']"
        return ""

    def generate_report(self):
        """Génère un rapport détaillé des non-conformités"""
        report = []
        report.append("# Rapport d'accessibilité RGAA\n")
        
        for category, issues in self.non_conformites.items():
            if issues:
                report.append(f"\n## {category.upper()}\n")
                for issue in issues:
                    report.append(f"### {issue['type']}")
                    report.append(f"- **Élément**: `{issue['element']}`")
                    report.append(f"- **XPath**: `{issue['xpath']}`")
                    report.append(f"- **Recommandation**: {issue['recommandation']}\n")

        # Mini résumé Titles (si disponible)
        titles_report_path = "reports/titles_report.md"
        if os.path.exists(titles_report_path):
            try:
                with open(titles_report_path, "r", encoding="utf-8") as tf:
                    lines = tf.read().splitlines()
                wanted_keys = {
                    "note_9_1_1",
                    "note_9_1_2",
                    "note_9_1_3",
                    "sections traitées via API",
                    "sections fallback (clé/API manquante ou erreur)",
                    "segments capturés",
                    "segments avec détections IA",
                }
                extracted = {}
                for line in lines:
                    if not line.startswith("- "):
                        continue
                    content = line[2:]
                    if ":" not in content:
                        continue
                    key, value = content.split(":", 1)
                    key = key.strip()
                    if key in wanted_keys:
                        extracted[key] = value.strip()

                if extracted:
                    report.append("\n## TITLES - Mini résumé")
                    report.append(f"- **9.1.1**: {extracted.get('note_9_1_1', '-')}")
                    report.append(f"- **9.1.2**: {extracted.get('note_9_1_2', '-')}")
                    report.append(f"- **9.1.3**: {extracted.get('note_9_1_3', '-')}")
                    report.append(
                        "- **Couverture IA sections (API/fallback)**: "
                        f"{extracted.get('sections traitées via API', '-')}/"
                        f"{extracted.get('sections fallback (clé/API manquante ou erreur)', '-')}"
                    )
                    report.append(
                        "- **Couverture IA segments (avec détections / capturés)**: "
                        f"{extracted.get('segments avec détections IA', '-')}/"
                        f"{extracted.get('segments capturés', '-')}\n"
                    )
            except Exception as e:
                self.logger.debug(f"Impossible d'ajouter le mini résumé Titles: {e}")
        
        # Écrire le rapport dans un fichier
        with open('reports/accessibility_report.md', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
