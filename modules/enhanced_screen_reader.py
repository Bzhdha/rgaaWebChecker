# Copie du ScreenReader original avec ajout de méthodes pour exposer les données ARIA
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import math
import os

class EnhancedScreenReader:
    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger
        self.page_url = None
        self.csv_lines = []  # Pour stocker les lignes CSV
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
                mediaType: el.tagName.toLowerCase()
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
            "MediaType": attrs['mediaType'] or "non défini"
        }
        
        # Stocker les données ARIA pour partage
        element_id = self._get_element_identifier(element)
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
        # Réinitialiser le cache des XPath au début de chaque analyse
        self._xpath_cache.clear()
        
        # Afficher l'URL de la page analysée en haut de l'analyse
        try:
            url = self.driver.current_url
            self.logger.info(f"\n**URL analysée** : {url}\n")
        except Exception:
            pass

        # En-tête CSV
        csv_header = [
            "Type", "Sélecteur", "Extrait HTML", "Rôle", "Aria-label", "Text", "Alt", "Title", "Visible", "Focusable", "Id",
            # Nouvelles colonnes ARIA pour les outils de narration
            "Aria-describedby", "Aria-labelledby", "Aria-hidden", "Aria-expanded", "Aria-controls", "Aria-live", "Aria-atomic", "Aria-relevant", "Aria-busy", "Aria-current", "Aria-posinset", "Aria-setsize", "Aria-level", "Aria-sort", "Aria-valuemin", "Aria-valuemax", "Aria-valuenow", "Aria-valuetext", "Aria-haspopup", "Aria-invalid", "Aria-required", "Aria-readonly", "Aria-disabled", "Aria-selected", "Aria-checked", "Aria-pressed", "Aria-multiline", "Aria-multiselectable", "Aria-orientation", "Aria-placeholder", "Aria-roledescription", "Aria-keyshortcuts", "Aria-details", "Aria-errormessage", "Aria-flowto", "Aria-owns", "Tabindex",
            "X-path principal", "X-path secondaire 1", "X-path secondaire 2"
        ]
        self.csv_lines.append(';'.join(csv_header))
        
        # Log des sections en Markdown
        self.logger.info("## Analyse des éléments d'accessibilité")
        self.logger.info("Cette section analyse les éléments clés pour l'accessibilité selon les critères RGAA :")
        self.logger.info("- Titres : Structure hiérarchique du contenu")
        self.logger.info("- Images : Alternatives textuelles et rôles")
        self.logger.info("- Liens : Textes explicites et attributs ARIA")
        self.logger.info("- Boutons : Rôles et états")
        self.logger.info("- Formulaires : Labels et attributs d'accessibilité")
        self.logger.info("- Landmarks : Structure sémantique de la page")
        self.logger.info("- Attributs ARIA : Rôles et propriétés d'accessibilité\n")

        # Récupération du DOM en une seule fois
        try:
            # Récupérer tous les éléments en une seule fois
            all_elements = self.driver.find_elements(By.XPATH, "//*")
            total_elements = len(all_elements)
            self.logger.info(f"Nombre total d'éléments HTML à analyser : {total_elements}")
            self.logger.info("Phase 1 : Classification des éléments par type...")
            
            # Créer des dictionnaires pour stocker les éléments par type
            elements_by_type = {
                "headings": [],
                "images": [],
                "links": [],
                "buttons": [],
                "forms": [],
                "landmarks": [],
                "aria_roles": []
            }

            # Classification optimisée par lots
            batch_size = 50  # Traiter par lots de 50 éléments
            for batch_start in range(0, total_elements, batch_size):
                batch_end = min(batch_start + batch_size, total_elements)
                batch = all_elements[batch_start:batch_end]
                
                # Récupération groupée des informations de classification
                batch_info = self.driver.execute_script('''
                    var elements = arguments[0];
                    var results = [];
                    for (var i = 0; i < elements.length; i++) {
                        var el = elements[i];
                        results.push({
                            tagName: el.tagName.toLowerCase(),
                            role: el.getAttribute('role')
                        });
                    }
                    return results;
                ''', batch)
                
                # Classification des éléments du lot
                for j, info in enumerate(batch_info):
                    current_index = batch_start + j + 1
                    if current_index % 10 == 0:  # Mise à jour plus fréquente de la barre de progression
                        self._print_progress(current_index, total_elements, prefix="Classification :", suffix=f"{current_index}/{total_elements}")
                    
                    tag_name = info['tagName']
                    role = info['role']
                    
                    if tag_name.startswith('h') and tag_name[1:].isdigit():
                        elements_by_type["headings"].append(batch[j])
                    elif tag_name == 'img':
                        elements_by_type["images"].append(batch[j])
                    elif tag_name == 'a':
                        elements_by_type["links"].append(batch[j])
                    elif tag_name == 'button':
                        elements_by_type["buttons"].append(batch[j])
                    elif tag_name == 'form':
                        elements_by_type["forms"].append(batch[j])
                    elif tag_name in ['header', 'nav', 'main', 'aside', 'footer']:
                        elements_by_type["landmarks"].append(batch[j])
                    
                    # Vérifier les rôles ARIA
                    if role:
                        elements_by_type["aria_roles"].append(batch[j])

            print()  # Nouvelle ligne après la barre de progression
            self.logger.info("\nPhase 2 : Analyse détaillée des éléments par catégorie...")
            
            # Analyser les éléments par catégorie
            categories = [
                ("headings", "Titres", "Structure hiérarchique du contenu"),
                ("images", "Images", "Alternatives textuelles et rôles"),
                ("links", "Liens", "Textes explicites et attributs ARIA"),
                ("buttons", "Boutons", "Rôles et états"),
                ("forms", "Formulaires", "Labels et attributs d'accessibilité"),
                ("landmarks", "Landmarks", "Structure sémantique de la page"),
                ("aria_roles", "Éléments avec rôles ARIA", "Rôles et propriétés d'accessibilité")
            ]

            total_processed = 0
            category_times = {}
            
            for category_key, category_name, category_desc in categories:
                elements = elements_by_type[category_key]
                if elements:
                    category_start = time.time()
                    self.logger.info(f"\n### {category_name} ({len(elements)} éléments)")
                    self.logger.info(f"Description : {category_desc}")
                    
                    # Analyse optimisée pour toutes les catégories
                    self.logger.info(f"Analyse optimisée des {category_name.lower()} en cours...")
                    self._analyze_elements_integrated(elements, category_name)
                    total_processed += len(elements)
                    
                    # Calculer et afficher le temps d'analyse
                    category_time = time.time() - category_start
                    category_times[category_name] = category_time
                    speed = len(elements) / category_time if category_time > 0 else 0
                    self.logger.info(f"⏱️ {category_name}: {category_time:.2f}s ({len(elements)} éléments) - Vitesse: {speed:.1f} éléments/s")
                    
                    # Afficher les attributs ARIA après la progression
                    self._log_aria_attributes()

            # Vérification de l'unicité des id
            self.logger.info("\nPhase 3 : Vérification des identifiants uniques...")
            self._check_duplicate_ids()
            
            # Afficher le résumé des temps d'analyse
            if category_times:
                self.logger.info(f"\n📊 Résumé des temps d'analyse:")
                total_analysis_time = sum(category_times.values())
                for category_name, time_taken in category_times.items():
                    percentage = (time_taken / total_analysis_time * 100) if total_analysis_time > 0 else 0
                    self.logger.info(f"   - {category_name}: {time_taken:.2f}s ({percentage:.1f}%)")
                self.logger.info(f"   - Total: {total_analysis_time:.2f}s")

        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse du DOM : {str(e)}")

        # Créer le répertoire reports s'il n'existe pas
        os.makedirs('reports', exist_ok=True)
        
        # Écrire le fichier CSV dans le répertoire reports
        with open('reports/accessibility_analysis.csv', 'w', encoding='utf-8-sig') as f:
            f.write('\n'.join(self.csv_lines))

        # Générer le rapport après l'analyse
        self.generate_report()
        self.logger.info("\nProgression : Rapport généré avec succès.")
        
        # Afficher un résumé des données ARIA collectées
        self.logger.info(f"\nDonnées ARIA collectées pour {len(self.aria_data_by_element)} éléments")

    def _print_element_table(self, element, element_type):
        """Analyse un élément et ajoute ses informations au rapport"""
        try:
            info = self._get_element_info(element)
            main_xpath, secondary_xpaths = self._get_xpath(element)
            
            # Ajout des XPath dans le dictionnaire info
            info["main_xpath"] = main_xpath
            info["secondary_xpath1"] = secondary_xpaths[0] if len(secondary_xpaths) > 0 else ''
            info["secondary_xpath2"] = secondary_xpaths[1] if len(secondary_xpaths) > 1 else ''
            
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
                self._clean_csv_field(info["main_xpath"]),
                self._clean_csv_field(info["secondary_xpath1"]),
                self._clean_csv_field(info["secondary_xpath2"])
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

    def _get_xpath(self, element):
        """Génère le X-path de l'élément avec mise en cache"""
        try:
            # Générer une clé unique pour l'élément
            element_id = element.get_attribute('id')
            element_class = element.get_attribute('class')
            element_tag = element.tag_name
            element_text = element.text[:50] if element.text else ''
            
            cache_key = f"{element_tag}:{element_id}:{element_class}:{element_text}"
            
            # Vérifier si le XPath est déjà en cache
            if cache_key in self._xpath_cache:
                return self._xpath_cache[cache_key]
            
            def get_xpath(el):
                """Génère un XPath précis pour l'élément"""
                # Si l'élément a un ID unique, utiliser directement
                if element_id:
                    return f"//*[@id='{element_id}']"
                
                # Sinon, construire le chemin complet
                path = []
                current = el
                
                while current is not None and current.tag_name.lower() != 'html':
                    # Obtenir l'index parmi les frères du même type
                    siblings = current.find_elements(By.XPATH, f"preceding-sibling::{current.tag_name}")
                    index = len(siblings) + 1
                    
                    # Construire le sélecteur pour cet élément
                    selector = current.tag_name
                    
                    # Ajouter des attributs pour plus de précision
                    attrs = []
                    
                    # Ajouter les classes si présentes
                    classes = current.get_attribute('class')
                    if classes:
                        class_list = classes.split()
                        if len(class_list) == 1:
                            attrs.append(f"@class='{classes}'")
                        else:
                            attrs.append(f"contains(@class, '{class_list[0]}')")
                    
                    # Ajouter le texte si présent et unique
                    text = current.text.strip()
                    if text and len(text) < 50:  # Limiter la longueur du texte
                        attrs.append(f"contains(text(), '{text}')")
                    
                    # Ajouter l'index si nécessaire
                    if len(attrs) > 0:
                        selector = f"{selector}[{' and '.join(attrs)}]"
                    else:
                        selector = f"{selector}[{index}]"
                    
                    path.insert(0, selector)
                    current = current.find_element(By.XPATH, '..')
                
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
        if element_type == "Image":
            # Critère 1.3 - Images
            alt = info["Alt"]
            role = info["Rôle"]
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

        elif element_type == "Lien":
            # Utilisation de la nouvelle méthode optimisée pour les liens
            results = self._analyze_links_batch([element])
            self.non_conformites["liens"].extend(results)

        elif element_type.startswith("H"):
            # Critère 9.1 - Titres
            if "sr-only" in info["Sélecteur"]:
                self.non_conformites["titres"].append({
                    "type": "Titre masqué visuellement",
                    "element": info["Sélecteur"],
                    "xpath": info["main_xpath"],
                    "recommandation": "Vérifier que le titre est pertinent pour la structure du document"
                })

        elif element_type == "Nav":
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
        role = info["Rôle"]
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
        elif role == "non défini" and element_type in ["Button", "Link", "Image", "Form"]:
            self.non_conformites["roles_aria"].append({
                "type": f"Élément {element_type} sans rôle ARIA",
                "element": info["Sélecteur"],
                "xpath": info["main_xpath"],
                "recommandation": f"Ajouter un rôle ARIA approprié pour l'élément {element_type}"
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

    def _check_duplicate_ids(self):
        """Vérifie l'unicité des attributs id dans la page"""
        id_map = defaultdict(list)
        # Récupérer tous les éléments avec un id
        elements = self.driver.find_elements(By.XPATH, '//*[@id]')
        for el in elements:
            eid = el.get_attribute('id')
            if eid:
                id_map[eid].append(el)
        # Chercher les ids dupliqués
        for eid, els in id_map.items():
            if len(els) > 1:
                for el in els:
                    main_xpath, _ = self._get_xpath(el)
                    self.non_conformites["duplicate_id"].append({
                        "type": f"Attribut id dupliqué : '{eid}'",
                        "element": self._get_simple_selector(el),
                        "xpath": main_xpath,
                        "recommandation": f"L'attribut id '{eid}' doit être unique dans la page."
                    })

    def _print_progress(self, current, total, prefix="", suffix="", length=50, fill="="):
        """Affiche une barre de progression sur la même ligne"""
        percent = f"{100 * (current / float(total)):.1f}"
        filled_length = int(length * current // total)
        bar = fill * filled_length + '-' * (length - filled_length)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='', flush=True)
        if current == total:
            print()  # Nouvelle ligne seulement à la fin

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
                        outerHTML: el.outerHTML
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
                        "MediaType": attrs['mediaType'] or "non défini"
                    }
                    
                    # Génération de XPath simplifiés (éviter les appels coûteux)
                    main_xpath = f"//a[@id='{attrs['id']}']" if attrs['id'] else f"//a[contains(@class, '{attrs['className'].split()[0]}')]" if attrs['className'] else "//a"
                    secondary_xpath1 = f"//a[contains(text(), '{attrs['text'][:30]}')]" if attrs['text'] and len(attrs['text']) < 50 else ""
                    secondary_xpath2 = f"//a[@href='{attrs['href']}']" if attrs['href'] else ""
                    
                    info["main_xpath"] = main_xpath
                    info["secondary_xpath1"] = secondary_xpath1
                    info["secondary_xpath2"] = secondary_xpath2
                    
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
                        self._clean_csv_field(info["main_xpath"]),
                        self._clean_csv_field(info["secondary_xpath1"]),
                        self._clean_csv_field(info["secondary_xpath2"])
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
        
        print()  # Nouvelle ligne après la barre de progression

    def _get_simple_selector_from_attrs(self, attrs):
        """Génère un sélecteur simple à partir des attributs récupérés"""
        tag = attrs['tag'].lower()
        classes = attrs['className']
        if classes:
            return f"{tag}.{'.'.join(classes.split())}"
        return tag

    def _analyze_elements_integrated(self, elements, category_name):
        """Analyse intégrée pour toutes les catégories - combine analyse des non-conformités et génération CSV en une seule passe"""
        # Traitement par lots pour réduire les appels JavaScript
        batch_size = 20
        total_elements = len(elements)
        
        for batch_start in range(0, total_elements, batch_size):
            batch_end = min(batch_start + batch_size, total_elements)
            batch = elements[batch_start:batch_end]
            
            # Récupération groupée des attributs pour tout le lot
            batch_attrs = self.driver.execute_script('''
                var elements = arguments[0];
                var results = [];
                for (var i = 0; i < elements.length; i++) {
                    var el = elements[i];
                    var rect = el.getBoundingClientRect();
                    var style = window.getComputedStyle(el);
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
                        src: el.getAttribute('src'),
                        isVisible: !(style.display === 'none' || style.visibility === 'hidden' || rect.width === 0 || rect.height === 0),
                        isEnabled: !el.disabled,
                        isFocusable: el.tabIndex >= 0 || ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName),
                        mediaPath: el.getAttribute('src') || el.getAttribute('data') || '',
                        mediaType: el.tagName.toLowerCase(),
                        outerHTML: el.outerHTML
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
                        "MediaType": attrs['mediaType'] or "non défini"
                    }
                    
                    # Génération de XPath simplifiés (éviter les appels coûteux)
                    main_xpath = self._generate_simple_xpath(attrs)
                    secondary_xpath1 = self._generate_secondary_xpath1(attrs)
                    secondary_xpath2 = self._generate_secondary_xpath2(attrs)
                    
                    info["main_xpath"] = main_xpath
                    info["secondary_xpath1"] = secondary_xpath1
                    info["secondary_xpath2"] = secondary_xpath2
                    
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
                        self._clean_csv_field(info["main_xpath"]),
                        self._clean_csv_field(info["secondary_xpath1"]),
                        self._clean_csv_field(info["secondary_xpath2"])
                    ]
                    self.csv_lines.append(';'.join(row))
                    
                    # Analyse des non-conformités
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
        
        print()  # Nouvelle ligne après la barre de progression

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
        
        # Écrire le rapport dans un fichier
        with open('reports/accessibility_report.md', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
