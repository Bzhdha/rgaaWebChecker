"""
Générateur de sélecteurs CSS pour l'analyse d'accessibilité
Génère 1 à 3 sélecteurs CSS alternatifs pour chaque élément analysé
"""

class CSSSelectorGenerator:
    """Générateur de sélecteurs CSS multiples pour les éléments web"""
    
    def __init__(self):
        pass
    
    def generate_css_selectors(self, element):
        """
        Génère 1 à 3 sélecteurs CSS pour un élément donné
        
        Args:
            element: Élément Selenium WebElement
            
        Returns:
            dict: Dictionnaire contenant main_css, secondary_css1, secondary_css2
        """
        try:
            selectors = {
                'main_css': '',
                'secondary_css1': '',
                'secondary_css2': ''
            }
            
            # Récupération des attributs de base
            tag_name = element.tag_name.lower()
            element_id = element.get_attribute('id')
            class_attr = element.get_attribute('class')
            name_attr = element.get_attribute('name')
            type_attr = element.get_attribute('type')
            href_attr = element.get_attribute('href')
            text_content = element.text.strip() if element.text else ''
            
            # Sélecteur principal (priorité : ID > classe > tag)
            if element_id:
                selectors['main_css'] = f"#{element_id}"
            elif class_attr:
                # Prendre la première classe
                first_class = class_attr.split()[0]
                selectors['main_css'] = f"{tag_name}.{first_class}"
            else:
                selectors['main_css'] = tag_name
            
            # Sélecteur secondaire 1 (combinaison d'attributs)
            if element_id and class_attr:
                # ID + classe
                first_class = class_attr.split()[0]
                selectors['secondary_css1'] = f"#{element_id}.{first_class}"
            elif class_attr and len(class_attr.split()) > 1:
                # Plusieurs classes
                classes = '.'.join(class_attr.split()[:2])  # Prendre les 2 premières classes
                selectors['secondary_css1'] = f"{tag_name}.{classes}"
            elif name_attr:
                # Attribut name
                selectors['secondary_css1'] = f"{tag_name}[name='{name_attr}']"
            elif type_attr and tag_name in ['input', 'button']:
                # Type d'input
                selectors['secondary_css1'] = f"{tag_name}[type='{type_attr}']"
            elif href_attr and tag_name == 'a':
                # Lien avec href
                selectors['secondary_css1'] = f"{tag_name}[href*='{href_attr[:20]}']"  # Partie du href
            else:
                # Sélecteur par position (nth-child)
                try:
                    parent = element.find_element_by_xpath('..')
                    siblings = parent.find_elements_by_xpath(f'./{tag_name}')
                    if len(siblings) > 1:
                        index = siblings.index(element) + 1
                        selectors['secondary_css1'] = f"{tag_name}:nth-child({index})"
                except:
                    pass
            
            # Sélecteur secondaire 2 (attributs ARIA ou texte)
            aria_label = element.get_attribute('aria-label')
            aria_labelledby = element.get_attribute('aria-labelledby')
            title_attr = element.get_attribute('title')
            
            if aria_label:
                selectors['secondary_css2'] = f"{tag_name}[aria-label='{aria_label}']"
            elif aria_labelledby:
                selectors['secondary_css2'] = f"{tag_name}[aria-labelledby='{aria_labelledby}']"
            elif title_attr:
                selectors['secondary_css2'] = f"{tag_name}[title='{title_attr}']"
            elif text_content and len(text_content) < 50:
                # Sélecteur par texte (si le texte est court)
                clean_text = text_content.replace('"', '\\"').replace("'", "\\'")
                selectors['secondary_css2'] = f"{tag_name}:contains('{clean_text[:30]}')"
            elif class_attr and len(class_attr.split()) > 2:
                # Toutes les classes
                all_classes = '.'.join(class_attr.split())
                selectors['secondary_css2'] = f"{tag_name}.{all_classes}"
            else:
                # Sélecteur par attribut data- ou role
                role_attr = element.get_attribute('role')
                if role_attr:
                    selectors['secondary_css2'] = f"{tag_name}[role='{role_attr}']"
                else:
                    # Dernier recours : sélecteur par position dans le parent
                    try:
                        parent_tag = element.find_element_by_xpath('..').tag_name.lower()
                        selectors['secondary_css2'] = f"{parent_tag} > {tag_name}"
                    except:
                        selectors['secondary_css2'] = tag_name
            
            # Nettoyage des sélecteurs vides
            for key in selectors:
                if not selectors[key]:
                    selectors[key] = tag_name
            
            return selectors
            
        except Exception as e:
            # En cas d'erreur, retourner des sélecteurs de base
            tag_name = getattr(element, 'tag_name', 'div').lower()
            return {
                'main_css': tag_name,
                'secondary_css1': tag_name,
                'secondary_css2': tag_name
            }
    
    def generate_css_selectors_from_attrs(self, attrs):
        """
        Génère des sélecteurs CSS à partir d'un dictionnaire d'attributs
        
        Args:
            attrs: Dictionnaire contenant les attributs de l'élément
            
        Returns:
            dict: Dictionnaire contenant main_css, secondary_css1, secondary_css2
        """
        try:
            selectors = {
                'main_css': '',
                'secondary_css1': '',
                'secondary_css2': ''
            }
            
            tag_name = attrs.get('tag', 'div').lower()
            element_id = attrs.get('id', '')
            class_attr = attrs.get('className', '')
            name_attr = attrs.get('name', '')
            type_attr = attrs.get('type', '')
            href_attr = attrs.get('href', '')
            text_content = attrs.get('text', '').strip()
            
            # Sélecteur principal
            if element_id:
                selectors['main_css'] = f"#{element_id}"
            elif class_attr:
                first_class = class_attr.split()[0]
                selectors['main_css'] = f"{tag_name}.{first_class}"
            else:
                selectors['main_css'] = tag_name
            
            # Sélecteur secondaire 1
            if element_id and class_attr:
                first_class = class_attr.split()[0]
                selectors['secondary_css1'] = f"#{element_id}.{first_class}"
            elif class_attr and len(class_attr.split()) > 1:
                classes = '.'.join(class_attr.split()[:2])
                selectors['secondary_css1'] = f"{tag_name}.{classes}"
            elif name_attr:
                selectors['secondary_css1'] = f"{tag_name}[name='{name_attr}']"
            elif type_attr and tag_name in ['input', 'button']:
                selectors['secondary_css1'] = f"{tag_name}[type='{type_attr}']"
            elif href_attr and tag_name == 'a':
                selectors['secondary_css1'] = f"{tag_name}[href*='{href_attr[:20]}']"
            else:
                selectors['secondary_css1'] = tag_name
            
            # Sélecteur secondaire 2
            aria_label = attrs.get('ariaLabel', '')
            aria_labelledby = attrs.get('ariaLabelledby', '')
            title_attr = attrs.get('title', '')
            
            if aria_label:
                selectors['secondary_css2'] = f"{tag_name}[aria-label='{aria_label}']"
            elif aria_labelledby:
                selectors['secondary_css2'] = f"{tag_name}[aria-labelledby='{aria_labelledby}']"
            elif title_attr:
                selectors['secondary_css2'] = f"{tag_name}[title='{title_attr}']"
            elif text_content and len(text_content) < 50:
                clean_text = text_content.replace('"', '\\"').replace("'", "\\'")
                selectors['secondary_css2'] = f"{tag_name}:contains('{clean_text[:30]}')"
            elif class_attr and len(class_attr.split()) > 2:
                all_classes = '.'.join(class_attr.split())
                selectors['secondary_css2'] = f"{tag_name}.{all_classes}"
            else:
                role_attr = attrs.get('role', '')
                if role_attr:
                    selectors['secondary_css2'] = f"{tag_name}[role='{role_attr}']"
                else:
                    selectors['secondary_css2'] = tag_name
            
            # Nettoyage des sélecteurs vides
            for key in selectors:
                if not selectors[key]:
                    selectors[key] = tag_name
            
            return selectors
            
        except Exception as e:
            tag_name = attrs.get('tag', 'div').lower()
            return {
                'main_css': tag_name,
                'secondary_css1': tag_name,
                'secondary_css2': tag_name
            }
