import os
from selenium.webdriver.common.by import By
from selenium.common.exceptions import JavascriptException
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import math
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.log_utils import log_with_step
import logging

class ScreenReader:
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

    def set_page_url(self, url):
        self.page_url = url

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

    def _analyze_links_optimized(self, links):
        """Analyse optimisée des liens - évite le double traitement et les XPath coûteux"""
        results = []
        
        # Traitement par lots pour réduire les appels JavaScript
        batch_size = 20
        for i in range(0, len(links), batch_size):
            batch = links[i:i + batch_size]
            
            # Récupération groupée des attributs pour tout le lot
            batch_attrs = self.driver.execute_script('''
                var links = arguments[0];
                var results = [];
                for (var i = 0; i < links.length; i++) {
                    var el = links[i];
                    results.push({
                        text: el.textContent ? el.textContent.trim() : '',
                        ariaLabel: el.getAttribute('aria-label'),
                        href: el.getAttribute('href'),
                        class: el.getAttribute('class'),
                        id: el.getAttribute('id'),
                        tag: el.tagName
                    });
                }
                return results;
            ''', batch)
            
            # Traitement des résultats du lot
            for j, attrs in enumerate(batch_attrs):
                try:
                    text = attrs['text']
                    aria_label = attrs['ariaLabel']
                    href = attrs['href']
                    class_name = attrs['class']
                    element_id = attrs['id']
                    
                    # Vérifications de non-conformité simplifiées
                    if not text or len(text.strip()) < 3:
                        # Utiliser un sélecteur simple au lieu de XPath coûteux
                        selector = f"a#{element_id}" if element_id else f"a.{class_name.split()[0]}" if class_name else "a"
                        results.append({
                            "type": "Lien sans texte explicite",
                            "element": selector,
                            "xpath": "N/A (optimisé)",
                            "recommandation": "Ajouter un texte descriptif au lien ou un aria-label"
                        })
                    
                    if class_name and "btn--hide-txt" in class_name:
                        selector = f"a#{element_id}" if element_id else f"a.{class_name.split()[0]}" if class_name else "a"
                        results.append({
                            "type": "Lien avec texte masqué",
                            "element": selector,
                            "xpath": "N/A (optimisé)",
                            "recommandation": "S'assurer que le texte est accessible aux lecteurs d'écran via aria-label"
                        })
                        
                except Exception as e:
                    self.logger.debug(f"Erreur lors de l'analyse du lien : {str(e)}")
                    continue
                    
        return results

    def _analyze_links_batch(self, links):
        """Analyse un lot de liens de manière optimisée (méthode legacy - conservée pour compatibilité)"""
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

    def _analyze_links_parallel(self, links, batch_size=10):
        """Analyse les liens en parallèle par lots"""
        # Diviser les liens en lots plus petits pour un meilleur équilibrage
        total_links = len(links)
        num_batches = math.ceil(total_links / batch_size)
        batches = [links[i:i + batch_size] for i in range(0, total_links, batch_size)]
        
        results = []
        # Utiliser un nombre fixe de workers pour maintenir la parallélisation
        max_workers = min(8, num_batches)  # Augmenter le nombre de workers
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Soumettre tous les lots en même temps
            future_to_batch = {
                executor.submit(self._analyze_links_batch, batch): i 
                for i, batch in enumerate(batches)
            }
            
            # Traiter les résultats au fur et à mesure qu'ils arrivent
            for future in as_completed(future_to_batch):
                try:
                    batch_results = future.result()
                    results.extend(batch_results)
                    # Afficher la progression
                    batch_index = future_to_batch[future]
                    self.logger.debug(f"Lot {batch_index + 1}/{num_batches} traité")
                except Exception as e:
                    self.logger.error(f"Erreur lors de l'analyse d'un lot de liens : {str(e)}")
        
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

    def _print_element_table(self, element, element_type):
        """Analyse un élément et ajoute ses informations au rapport"""
        try:
            info = self._get_element_info(element)
            main_xpath, secondary_xpaths = self._get_xpath(element)
            
            # Ajout des XPath dans le dictionnaire info
            info["main_xpath"] = main_xpath
            info["secondary_xpath1"] = secondary_xpaths[0] if len(secondary_xpaths) > 0 else ''
            info["secondary_xpath2"] = secondary_xpaths[1] if len(secondary_xpaths) > 1 else ''
            
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
                self._clean_csv_field(info["secondary_xpath2"])
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

    def _handle_cookie_popup(self):
        """Gère la popin de cookies comme une fenêtre complémentaire et clique sur le bon bouton"""
        try:
            time.sleep(2)  # Attente pour le chargement de la page
            # 1. Chercher une popin de type dialog ou contenant 'cookie' dans la classe ou l'id
            popup_selectors = [
                "[role='dialog']",
                "[role='alertdialog']",
                "div[class*='cookie']",
                "div[id*='cookie']",
                "section[class*='cookie']",
                "section[id*='cookie']",
                "div[class*='consent']",
                "div[id*='consent']"
            ]
            popup = None
            for selector in popup_selectors:
                try:
                    candidate = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if candidate.is_displayed():
                        popup = candidate
                        break
                except Exception:
                    continue
            if popup:
                # 2. Chercher les boutons dans la popin
                boutons = popup.find_elements(By.TAG_NAME, "button")
                # Textes possibles pour refuser ou fermer
                textes_cibles = [
                    "Continuer sans accepter", "Refuser", "Tout refuser", "Refuser tout", "Ne pas accepter", "Do not accept", "Continue without accepting", "Reject all", "Decline", "Fermer", "Close"
                ]
                textes_accept = [
                    "Accepter et fermer", "Accepter", "Tout accepter", "OK", "Accept and close", "Accept all", "Accept"
                ]
                # 3. Essayer de cliquer sur un bouton de refus d'abord
                for btn in boutons:
                    txt = btn.text.strip()
                    if any(tgt.lower() in txt.lower() for tgt in textes_cibles):
                        if btn.is_displayed():
                            btn.click()
                            self.logger.info(f"Popin de cookies fermée avec succès (bouton: {txt})")
                            time.sleep(1)
                            return True
                # 4. Sinon, cliquer sur un bouton d'acceptation si besoin
                for btn in boutons:
                    txt = btn.text.strip()
                    if any(tgt.lower() in txt.lower() for tgt in textes_accept):
                        if btn.is_displayed():
                            btn.click()
                            self.logger.info(f"Popin de cookies fermée avec succès (bouton: {txt})")
                            time.sleep(1)
                            return True
                self.logger.warning("Popin détectée mais aucun bouton pertinent trouvé.")
                return False
            # 5. Si aucune popin détectée, fallback sur les anciens sélecteurs
            # (pour compatibilité)
            try:
                refuse_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Continuer sans accepter')]")
                if refuse_btn.is_displayed():
                    refuse_btn.click()
                    self.logger.info("Popin de cookies fermée avec succès (Continuer sans accepter)")
                    time.sleep(1)
                    return True
            except Exception:
                pass
            try:
                accept_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Accepter et fermer')]")
                if accept_btn.is_displayed():
                    accept_btn.click()
                    self.logger.info("Popin de cookies fermée avec succès (Accepter et fermer)")
                    time.sleep(1)
                    return True
            except Exception:
                pass
            cookie_selectors = [
                "button[aria-label*='cookie']",
                "button[aria-label*='Cookie']",
                "button[aria-label*='COOKIE']",
                "button[id*='cookie']",
                "button[id*='Cookie']",
                "button[class*='cookie']",
                "button[class*='Cookie']"
            ]
            for selector in cookie_selectors:
                try:
                    accept_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if accept_button.is_displayed():
                        accept_button.click()
                        self.logger.info("Popin de cookies fermée avec succès (autre bouton)")
                        time.sleep(1)
                        return True
                except:
                    continue
            return False
        except Exception as e:
            self.logger.warning(f"Erreur lors de la gestion de la popin de cookies: {str(e)}")
            return False

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

    def _print_progress(self, current, total, prefix="", suffix="", length=50, fill="█"):
        """Affiche une barre de progression sur la même ligne"""
        percent = f"{100 * (current / float(total)):.1f}"
        filled_length = int(length * current // total)
        bar = fill * filled_length + '-' * (length - filled_length)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
        if current == total:
            print()

    def run(self):
        log_with_step(self.logger, logging.INFO, "LECTEUR_ECRAN", "\nSimulation de lecteur d'écran...")
        
        try:
            # Attendre que la page soit complètement chargée
            WebDriverWait(self.driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            # Analyser la structure de la page
            self._analyze_page_structure()
            
            # Analyser les éléments d'accessibilité
            self._analyze_accessibility_elements()
            
            # Analyser la navigation
            self._analyze_navigation()
            
            # Générer le rapport après l'analyse
            self.generate_report()
            log_with_step(self.logger, logging.INFO, "LECTEUR_ECRAN", "\nRapport généré avec succès.")
            
            # Retourner une liste vide pour éviter les erreurs d'itération
            return []
            
        except Exception as e:
            log_with_step(self.logger, logging.ERROR, "LECTEUR_ECRAN", f"Erreur lors de la simulation de lecteur d'écran : {str(e)}")
            return []

    def _analyze_page_structure(self):
        """Analyse la structure générale de la page"""
        try:
            # Vérifier la présence d'éléments de structure
            headings = self.driver.find_elements(By.XPATH, "//h1 | //h2 | //h3 | //h4 | //h5 | //h6")
            main_content = self.driver.find_elements(By.TAG_NAME, "main")
            nav_elements = self.driver.find_elements(By.TAG_NAME, "nav")
            
            log_with_step(self.logger, logging.INFO, "LECTEUR_ECRAN", f"Structure de la page :")
            log_with_step(self.logger, logging.INFO, "LECTEUR_ECRAN", f"- Titres trouvés : {len(headings)}")
            log_with_step(self.logger, logging.INFO, "LECTEUR_ECRAN", f"- Contenu principal : {len(main_content)}")
            log_with_step(self.logger, logging.INFO, "LECTEUR_ECRAN", f"- Navigation : {len(nav_elements)}")
            
        except Exception as e:
            log_with_step(self.logger, logging.WARNING, "LECTEUR_ECRAN", f"Erreur lors de l'analyse de la structure : {str(e)}")

    def _analyze_accessibility_elements(self):
        """Analyse les éléments d'accessibilité"""
        try:
            # Rechercher les éléments avec des attributs d'accessibilité
            aria_labeledby = self.driver.find_elements(By.XPATH, "//*[@aria-labelledby]")
            aria_describedby = self.driver.find_elements(By.XPATH, "//*[@aria-describedby]")
            aria_hidden = self.driver.find_elements(By.XPATH, "//*[@aria-hidden='true']")
            role_elements = self.driver.find_elements(By.XPATH, "//*[@role]")
            
            log_with_step(self.logger, logging.INFO, "LECTEUR_ECRAN", f"Éléments d'accessibilité :")
            log_with_step(self.logger, logging.INFO, "LECTEUR_ECRAN", f"- aria-labelledby : {len(aria_labeledby)}")
            log_with_step(self.logger, logging.INFO, "LECTEUR_ECRAN", f"- aria-describedby : {len(aria_describedby)}")
            log_with_step(self.logger, logging.INFO, "LECTEUR_ECRAN", f"- aria-hidden : {len(aria_hidden)}")
            log_with_step(self.logger, logging.INFO, "LECTEUR_ECRAN", f"- role : {len(role_elements)}")
            
        except Exception as e:
            log_with_step(self.logger, logging.WARNING, "LECTEUR_ECRAN", f"Erreur lors de l'analyse des éléments d'accessibilité : {str(e)}")

    def _analyze_navigation(self):
        """Analyse la navigation au clavier"""
        try:
            # Rechercher les éléments de navigation
            links = self.driver.find_elements(By.TAG_NAME, "a")
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            
            log_with_step(self.logger, logging.INFO, "LECTEUR_ECRAN", f"Éléments de navigation :")
            log_with_step(self.logger, logging.INFO, "LECTEUR_ECRAN", f"- Liens : {len(links)}")
            log_with_step(self.logger, logging.INFO, "LECTEUR_ECRAN", f"- Boutons : {len(buttons)}")
            log_with_step(self.logger, logging.INFO, "LECTEUR_ECRAN", f"- Champs de saisie : {len(inputs)}")
            
        except Exception as e:
            log_with_step(self.logger, logging.WARNING, "LECTEUR_ECRAN", f"Erreur lors de l'analyse de la navigation : {str(e)}")

    def generate_report(self):
        """Génère un rapport d'analyse pour le lecteur d'écran"""
        try:
            # Créer le dossier reports s'il n'existe pas
            os.makedirs('reports', exist_ok=True)
            
            # Générer un rapport simple
            report_path = 'reports/screen_reader_analysis.txt'
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("=== Analyse Lecteur d'Écran ===\n\n")
                f.write("Ce rapport contient les informations d'accessibilité\n")
                f.write("pour les utilisateurs de lecteurs d'écran.\n\n")
                
                # Ajouter les résultats de l'analyse
                f.write("Structure de la page :\n")
                f.write("- Vérifiez la hiérarchie des titres\n")
                f.write("- Assurez-vous de la présence d'un contenu principal\n")
                f.write("- Vérifiez la navigation\n\n")
                
                f.write("Éléments d'accessibilité :\n")
                f.write("- Vérifiez les attributs ARIA\n")
                f.write("- Assurez-vous que les éléments cachés sont bien masqués\n")
                f.write("- Vérifiez les rôles des éléments\n\n")
                
                f.write("Navigation :\n")
                f.write("- Testez la navigation au clavier\n")
                f.write("- Vérifiez l'ordre de tabulation\n")
                f.write("- Assurez-vous que tous les éléments sont accessibles\n")
            
            log_with_step(self.logger, logging.INFO, "LECTEUR_ECRAN", f"Rapport généré : {report_path}")
            
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
            # ⏱️ ÉTAPE 1: Récupération des éléments DOM
            step1_start = time.time()
            all_elements = self.driver.find_elements(By.XPATH, "//*")
            total_elements = len(all_elements)
            step1_time = time.time() - step1_start
            self.logger.info(f"⏱️ ÉTAPE 1 - Récupération DOM: {step1_time:.2f}s ({total_elements} éléments)")
            
            # ⏱️ ÉTAPE 2: Classification des éléments
            step2_start = time.time()
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
                        # Analyse optimisée des liens - traitement unique
                        self.logger.info("Analyse optimisée des liens en cours...")
                        results = self._analyze_links_optimized(elements)
                        self.non_conformites["liens"].extend(results)
                        
                        # Traitement direct sans ThreadPoolExecutor pour éviter la surcharge
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
            log_with_step(self.logger, logging.ERROR, "LECTEUR_ECRAN", f"Erreur lors de la génération du rapport : {str(e)}") 
            self.logger.error(f"Erreur lors de l'analyse du DOM : {str(e)}")

        # ⏱️ ÉTAPE 5: Génération des rapports
        step5_start = time.time()
        self.logger.info("\n⏱️ ÉTAPE 5 - Génération des rapports...")
        
        # Créer le répertoire reports s'il n'existe pas
        os.makedirs('reports', exist_ok=True)
        
        # Écrire le fichier CSV dans le répertoire reports
        with open('reports/accessibility_analysis.csv', 'w', encoding='utf-8-sig') as f:
            f.write('\n'.join(self.csv_lines))

        # Générer le rapport après l'analyse
        self.generate_report()
        step5_time = time.time() - step5_start
        self.logger.info(f"⏱️ ÉTAPE 5 - Génération rapports: {step5_time:.2f}s")
        
        # 📊 RÉSUMÉ GLOBAL DES PERFORMANCES
        total_time = time.time() - start_time
        self.logger.info(f"\n🚀 RÉSUMÉ DES PERFORMANCES:")
        self.logger.info(f"⏱️ Temps total d'analyse: {total_time:.2f}s")
        self.logger.info(f"📊 Éléments traités: {total_processed}")
        if total_processed > 0:
            self.logger.info(f"⚡ Vitesse moyenne: {total_processed/total_time:.1f} éléments/seconde")
        self.logger.info("\nProgression : Rapport généré avec succès.") 