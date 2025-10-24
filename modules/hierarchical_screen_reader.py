# Copie du ScreenReader avec algorithme hiérarchique optimisé
from selenium.webdriver.common.by import By
from selenium.common.exceptions import JavascriptException
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import math
import os
from utils.css_selector_generator import CSSSelectorGenerator

class HierarchicalScreenReader:
    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger
        self.page_url = None
        self.csv_lines = []  # Pour stocker les lignes CSV
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
        # Hiérarchie DOM optimisée
        self._dom_hierarchy = {}
        self._element_map = {}
        
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

    def set_page_url(self, url):
        self.page_url = url

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

    def _build_dom_hierarchy(self):
        """Construit une hiérarchie DOM optimisée pour la génération de XPath"""
        self.logger.info("🔧 Construction de la hiérarchie DOM optimisée...")
        start_time = time.time()
        
        # Récupérer tous les éléments en une seule requête
        all_elements = self.driver.find_elements(By.XPATH, "//*")
        total_elements = len(all_elements)
        
        # Construire la hiérarchie avec une seule requête JavaScript
        hierarchy_data = self.driver.execute_script('''
            var elements = arguments[0];
            var hierarchy = {};
            var elementMap = {};
            
            for (var i = 0; i < elements.length; i++) {
                var el = elements[i];
                var parent = el.parentElement;
                var siblings = parent ? Array.from(parent.children) : [];
                var index = siblings.indexOf(el);
                
                var elementInfo = {
                    tag: el.tagName,
                    id: el.id || null,
                    className: el.className || null,
                    text: el.textContent ? el.textContent.trim().substring(0, 50) : '',
                    parentTag: parent ? parent.tagName : null,
                    parentId: parent ? parent.id : null,
                    siblingIndex: index,
                    siblingCount: siblings.length,
                    siblingTags: siblings.map(s => s.tagName),
                    isVisible: el.offsetWidth > 0 && el.offsetHeight > 0,
                    isEnabled: !el.disabled,
                    isFocusable: el.tabIndex >= 0 || ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName)
                };
                
                // Créer un identifiant unique
                var identifier = el.id ? el.tagName + '#' + el.id : 
                                el.textContent ? el.tagName + '[text=\'' + el.textContent.trim().substring(0, 30) + '\']' :
                                el.className ? el.tagName + '.' + el.className.split(' ')[0] :
                                el.tagName + '[' + i + ']';
                
                hierarchy[identifier] = elementInfo;
                elementMap[identifier] = el;
            }
            
            return { hierarchy: hierarchy, elementMap: elementMap };
        ''', all_elements)
        
        self._dom_hierarchy = hierarchy_data['hierarchy']
        self._element_map = hierarchy_data['elementMap']
        
        build_time = time.time() - start_time
        self.logger.info(f"✅ Hiérarchie DOM construite: {build_time:.2f}s ({total_elements} éléments)")
        
        return self._dom_hierarchy, self._element_map

    def _get_xpath_hierarchical(self, element):
        """Génère XPath optimisé en utilisant la hiérarchie DOM"""
        try:
            element_id = self._get_element_identifier(element)
            element_info = self._dom_hierarchy.get(element_id)
            
            if not element_info:
                return self._get_simple_xpath(element)
            
            # Vérifier le cache d'abord
            cache_key = f"{element_info['tag']}:{element_info['id']}:{element_info['className']}"
            if cache_key in self._xpath_cache:
                return self._xpath_cache[cache_key]
            
            # XPath optimisé basé sur la hiérarchie
            if element_info['id']:
                xpath = f"//*[@id='{element_info['id']}']"
            else:
                # Construire le chemin hiérarchique optimisé
                path_parts = []
                current = element_info
                
                while current:
                    tag = current['tag']
                    sibling_index = current['siblingIndex']
                    sibling_count = current['siblingCount']
                    
                    # Optimisation : utiliser l'index seulement si nécessaire
                    if sibling_count > 1:
                        path_parts.insert(0, f"{tag}[{sibling_index + 1}]")
                    else:
                        path_parts.insert(0, tag)
                    
                    # Remonter vers le parent (simulé)
                    if current['parentTag']:
                        current = {
                            'tag': current['parentTag'],
                            'siblingIndex': 0,  # Simplifié pour la performance
                            'siblingCount': 1
                        }
                    else:
                        current = None
                
                xpath = '/html/' + '/'.join(path_parts)
            
            # Mettre en cache
            self._xpath_cache[cache_key] = (xpath, [])
            return (xpath, [])
            
        except Exception as e:
            self.logger.debug(f"Erreur lors de la génération du XPath hiérarchique : {str(e)}")
            return self._get_simple_xpath(element)

    def _get_simple_xpath(self, element):
        """XPath simple et rapide en fallback"""
        try:
            element_id = element.get_attribute('id')
            if element_id:
                return (f"//*[@id='{element_id}']", [])
            
            tag = element.tag_name
            classes = element.get_attribute('class')
            if classes:
                return (f"//{tag}[contains(@class, '{classes.split()[0]}')]", [])
            
            return (f"//{tag}[{hash(str(element))}]", [])
        except:
            return ('Non disponible', [])

    def _get_element_info(self, element):
        """Récupère toutes les informations d'accessibilité d'un élément (optimisé)"""
        # Script JavaScript allégé - récupère seulement les attributs essentiels
        attrs = self.driver.execute_script('''
            var el = arguments[0];
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
                ariaRequired: el.getAttribute('aria-required'),
                ariaDisabled: el.getAttribute('aria-disabled'),
                ariaSelected: el.getAttribute('aria-selected'),
                ariaChecked: el.getAttribute('aria-checked'),
                ariaPressed: el.getAttribute('aria-pressed'),
                tabindex: el.getAttribute('tabindex'),
                title: el.getAttribute('title'),
                alt: el.getAttribute('alt'),
                id: el.getAttribute('id'),
                className: el.getAttribute('class'),
                text: el.textContent ? el.textContent.trim() : '',
                isVisible: el.offsetWidth > 0 && el.offsetHeight > 0,
                isEnabled: !el.disabled,
                isFocusable: el.tabIndex >= 0 || ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName),
                mediaPath: el.getAttribute('src') || el.getAttribute('data') || '',
                mediaType: el.tagName.toLowerCase()
            };
        ''', element)

        # Construction du dictionnaire d'informations optimisé
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
            "Aria-required": attrs['ariaRequired'] or "non défini",
            "Aria-disabled": attrs['ariaDisabled'] or "non défini",
            "Aria-selected": attrs['ariaSelected'] or "non défini",
            "Aria-checked": attrs['ariaChecked'] or "non défini",
            "Aria-pressed": attrs['ariaPressed'] or "non défini",
            "Tabindex": attrs['tabindex'] or "non défini",
            "Title": attrs['title'] or "non défini",
            "Alt": attrs['alt'] or "non défini",
            "Text": attrs['text'] or "non défini",
            "Visible": "Oui" if attrs['isVisible'] else "Non",
            "Focusable": "Oui" if attrs['isFocusable'] else "Non",
            "Id": attrs['id'] or "non défini",
            "Sélecteur": self._get_simple_selector(element),
            "Extrait HTML": self._get_html_snippet(element),
            "MediaPath": attrs['mediaPath'] or "non défini",
            "MediaType": attrs['mediaType'] or "non défini"
        }
        return info

    def _get_simple_selector(self, element):
        tag = element.tag_name
        classes = element.get_attribute('class')
        if classes:
            return f"{tag}.{'.'.join(classes.split())}"
        return tag

    def _get_html_snippet(self, element):
        """Génère un extrait HTML léger sans outerHTML coûteux"""
        try:
            tag = element.tag_name
            id_attr = element.get_attribute('id')
            class_attr = element.get_attribute('class')
            text = element.text[:50] if element.text else ''
            
            # Construire un extrait simple
            snippet = f"<{tag.lower()}"
            if id_attr:
                snippet += f' id="{id_attr}"'
            if class_attr:
                snippet += f' class="{class_attr[:30]}"'
            if text:
                snippet += f">{text[:30]}...</{tag.lower()}>"
            else:
                snippet += " />"
            
            return snippet
        except:
            return f"<{element.tag_name.lower()} />"

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

    def _analyze_links_hierarchical(self, links):
        """Analyse optimisée des liens avec hiérarchie DOM"""
        self.logger.info("🔗 Analyse hiérarchique optimisée des liens...")
        start_time = time.time()
        
        # Récupérer tous les attributs des liens en une seule requête
        batch_attrs = self.driver.execute_script('''
            var links = arguments[0];
            return links.map(function(el) {
                return {
                    text: el.textContent ? el.textContent.trim() : '',
                    ariaLabel: el.getAttribute('aria-label'),
                    href: el.getAttribute('href'),
                    class: el.getAttribute('class'),
                    id: el.getAttribute('id'),
                    tag: el.tagName
                };
            });
        ''', links)
        
        # Traiter tous les liens avec XPath optimisés
        results = []
        for i, (link, attrs) in enumerate(zip(links, batch_attrs)):
            try:
                # XPath généré à partir de la hiérarchie (très rapide)
                main_xpath, secondary_xpaths = self._get_xpath_hierarchical(link)
                
                # Vérifications de non-conformité
                if not attrs['text'] or len(attrs['text'].strip()) < 3:
                    results.append({
                        "type": "Lien sans texte explicite",
                        "element": f"{attrs['tag']}#{attrs['id']}" if attrs['id'] else f"{attrs['tag']}.{attrs['class'].split()[0]}" if attrs['class'] else attrs['tag'],
                        "xpath": main_xpath,
                        "recommandation": "Ajouter un texte descriptif au lien ou un aria-label"
                    })
                
                if attrs['class'] and "btn--hide-txt" in attrs['class']:
                    results.append({
                        "type": "Lien avec texte masqué",
                        "element": f"{attrs['tag']}#{attrs['id']}" if attrs['id'] else f"{attrs['tag']}.{attrs['class'].split()[0]}" if attrs['class'] else attrs['tag'],
                        "xpath": main_xpath,
                        "recommandation": "S'assurer que le texte est accessible aux lecteurs d'écran via aria-label"
                    })
                    
            except Exception as e:
                self.logger.debug(f"Erreur lors de l'analyse du lien : {str(e)}")
                continue
        
        analysis_time = time.time() - start_time
        self.logger.info(f"⏱️ Analyse hiérarchique des liens: {analysis_time:.2f}s ({len(links)} liens)")
        
        return results

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

    def _print_element_table(self, element, element_type):
        """Analyse un élément et ajoute ses informations au rapport (version hiérarchique)"""
        try:
            info = self._get_element_info(element)
            main_xpath, secondary_xpaths = self._get_xpath_hierarchical(element)
            
            # Ajout des XPath dans le dictionnaire info
            info["main_xpath"] = main_xpath
            info["secondary_xpath1"] = secondary_xpaths[0] if len(secondary_xpaths) > 0 else ''
            info["secondary_xpath2"] = secondary_xpaths[1] if len(secondary_xpaths) > 1 else ''
            
            # Génération de sélecteurs CSS alternatifs
            css_selectors = self.css_generator.generate_css_selectors(element)
            info["main_css"] = css_selectors["main_css"]
            info["secondary_css1"] = css_selectors["secondary_css1"]
            info["secondary_css2"] = css_selectors["secondary_css2"]
            
            # Construction de la ligne CSV avec nettoyage des champs
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
                self._clean_csv_field(info["main_xpath"]),
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
            
            # Log des attributs ARIA en Markdown (uniquement si des attributs sont définis)
            aria_attrs = {k: v for k, v in info.items() if k.startswith("Aria-") and v != "non défini"}
            if aria_attrs:
                self.logger.info("### Attributs ARIA définis")
                for attr, value in aria_attrs.items():
                    self.logger.debug(f"✓ {attr}: {value}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse de l'élément {element_type}: {str(e)}")

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
                    main_xpath, _ = self._get_xpath_hierarchical(el)
                    self.non_conformites["duplicate_id"].append({
                        "type": f"Attribut id dupliqué : '{eid}'",
                        "element": self._get_simple_selector(el),
                        "xpath": main_xpath,
                        "recommandation": f"L'attribut id '{eid}' doit être unique dans la page."
                    })

    def _print_progress(self, current, total, prefix="", suffix="", length=50, fill="█"):
        """Affiche une barre de progression sur la même ligne"""
        percent = f"{100 * (current / float(total)):.1f}"
        filled_length = int(length * current // total)
        bar = fill * filled_length + '-' * (length - filled_length)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
        if current == total:
            print()

    def generate_report(self):
        """Génère un rapport détaillé des non-conformités"""
        report = []
        report.append("# Rapport d'accessibilité RGAA (Version Hiérarchique)\n")
        
        for category, issues in self.non_conformites.items():
            if issues:
                report.append(f"\n## {category.upper()}\n")
                for issue in issues:
                    report.append(f"### {issue['type']}")
                    report.append(f"- **Élément**: `{issue['element']}`")
                    report.append(f"- **XPath**: `{issue['xpath']}`")
                    report.append(f"- **Recommandation**: {issue['recommandation']}\n")
        
        # Écrire le rapport dans un fichier
        with open('reports/accessibility_report_hierarchical.md', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))

    def run(self):
        """Exécute l'analyse d'accessibilité avec algorithme hiérarchique optimisé"""
        import time
        start_time = time.time()
        
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
            "Type", "Sélecteur", "Extrait HTML", "Rôle", "Aria-label", "Text", "Alt", "Title", "Visible", "Focusable", "Id", "X-path principal", "X-path secondaire 1", "X-path secondaire 2"
        ]
        self.csv_lines.append(';'.join(csv_header))
        
        # Log des sections en Markdown
        self.logger.info("## Analyse des éléments d'accessibilité (Version Hiérarchique)")
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
            # ⏱️ ÉTAPE 1: Construction de la hiérarchie DOM
            step1_start = time.time()
            self._build_dom_hierarchy()
            step1_time = time.time() - step1_start
            self.logger.info(f"⏱️ ÉTAPE 1 - Construction hiérarchie: {step1_time:.2f}s")
            
            # ⏱️ ÉTAPE 2: Classification des éléments
            step2_start = time.time()
            self.logger.info("Phase 1 : Classification des éléments par type...")
            
            # Récupérer tous les éléments en une seule fois
            all_elements = self.driver.find_elements(By.XPATH, "//*")
            total_elements = len(all_elements)
            self.logger.info(f"Nombre total d'éléments HTML à analyser : {total_elements}")
            
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

            # Classer les éléments par type
            for i, element in enumerate(all_elements, 1):
                if i % 10 == 0:  # Mise à jour plus fréquente de la barre de progression
                    self._print_progress(i, total_elements, prefix="Classification :", suffix=f"{i}/{total_elements}")
                
                tag_name = element.tag_name.lower()
                
                if tag_name.startswith('h') and tag_name[1:].isdigit():
                    elements_by_type["headings"].append(element)
                elif tag_name == 'img':
                    elements_by_type["images"].append(element)
                elif tag_name == 'a':
                    elements_by_type["links"].append(element)
                elif tag_name == 'button':
                    elements_by_type["buttons"].append(element)
                elif tag_name == 'form':
                    elements_by_type["forms"].append(element)
                elif tag_name in ['header', 'nav', 'main', 'aside', 'footer']:
                    elements_by_type["landmarks"].append(element)
                
                # Vérifier les rôles ARIA
                role = element.get_attribute('role')
                if role:
                    elements_by_type["aria_roles"].append(element)

            step2_time = time.time() - step2_start
            print()  # Nouvelle ligne après la barre de progression
            self.logger.info(f"⏱️ ÉTAPE 2 - Classification: {step2_time:.2f}s")
            self.logger.info(f"📊 Résultats classification:")
            for category, elements in elements_by_type.items():
                self.logger.info(f"   - {category}: {len(elements)} éléments")
            
            # ⏱️ ÉTAPE 3: Analyse détaillée par catégorie
            step3_start = time.time()
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
                    
                    if category_key == "links":
                        # Analyse hiérarchique optimisée des liens
                        self.logger.info("Analyse hiérarchique optimisée des liens en cours...")
                        results = self._analyze_links_hierarchical(elements)
                        self.non_conformites["liens"].extend(results)
                        
                        # Traitement direct avec XPath optimisés
                        for i, element in enumerate(elements, 1):
                            self._print_progress(i, len(elements), prefix=f"Analyse {category_name}:", suffix=f"{i}/{len(elements)}")
                            self._print_element_table(element, category_name)
                            total_processed += 1
                    else:
                        # Analyse normale pour les autres catégories
                        for i, element in enumerate(elements, 1):
                            self._print_progress(i, len(elements), prefix=f"Analyse {category_name}:", suffix=f"{i}/{len(elements)}")
                            self._print_element_table(element, category_name)
                            total_processed += 1
                    
                    category_time = time.time() - category_start
                    category_times[category_name] = category_time
                    self.logger.info(f"⏱️ {category_name}: {category_time:.2f}s ({len(elements)} éléments)")
                    print()  # Nouvelle ligne après la barre de progression
            
            step3_time = time.time() - step3_start
            self.logger.info(f"⏱️ ÉTAPE 3 - Analyse détaillée: {step3_time:.2f}s")
            self.logger.info(f"📊 Temps par catégorie:")
            for category, time_taken in category_times.items():
                self.logger.info(f"   - {category}: {time_taken:.2f}s")

            # ⏱️ ÉTAPE 4: Vérification des identifiants uniques
            step4_start = time.time()
            self.logger.info("\nPhase 3 : Vérification des identifiants uniques...")
            self._check_duplicate_ids()
            step4_time = time.time() - step4_start
            self.logger.info(f"⏱️ ÉTAPE 4 - Vérification IDs: {step4_time:.2f}s")

        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse du DOM : {str(e)}")

        # ⏱️ ÉTAPE 5: Génération des rapports
        step5_start = time.time()
        self.logger.info("\n⏱️ ÉTAPE 5 - Génération des rapports...")
        
        # Créer le répertoire reports s'il n'existe pas
        os.makedirs('reports', exist_ok=True)
        
        # Écrire le fichier CSV dans le répertoire reports
        with open('reports/accessibility_analysis_hierarchical.csv', 'w', encoding='utf-8-sig') as f:
            f.write('\n'.join(self.csv_lines))

        # Générer le rapport après l'analyse
        self.generate_report()
        step5_time = time.time() - step5_start
        self.logger.info(f"⏱️ ÉTAPE 5 - Génération rapports: {step5_time:.2f}s")
        
        # 📊 RÉSUMÉ GLOBAL DES PERFORMANCES
        total_time = time.time() - start_time
        self.logger.info(f"\n🚀 RÉSUMÉ DES PERFORMANCES (VERSION HIÉRARCHIQUE):")
        self.logger.info(f"⏱️ Temps total d'analyse: {total_time:.2f}s")
        self.logger.info(f"📊 Éléments traités: {total_processed}")
        if total_processed > 0:
            self.logger.info(f"⚡ Vitesse moyenne: {total_processed/total_time:.1f} éléments/seconde")
        self.logger.info("\nProgression : Rapport généré avec succès (Version Hiérarchique).")
