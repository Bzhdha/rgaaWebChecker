"""
Module unifié pour la génération d'identifiants d'éléments
Assure la cohérence entre tous les modules d'analyse
"""

class ElementIdentifier:
    """Générateur d'identifiants unifié pour les éléments DOM"""
    
    @staticmethod
    def generate_identifier(element, driver=None, include_position=True):
        """
        Génère un identifiant unique et cohérent pour un élément
        
        Args:
            element: L'élément Selenium
            driver: Le driver Selenium (optionnel, pour la position)
            include_position: Inclure la position dans l'identifiant (défaut: True)
            
        Returns:
            str: Identifiant unique de l'élément
        """
        try:
            # Propriétés de base de l'élément
            tag = element.tag_name.lower()
            element_id = element.get_attribute('id')
            element_class = element.get_attribute('class')
            element_text = element.text.strip() if element.text else ''
            element_href = element.get_attribute('href')
            element_type = element.get_attribute('type')
            
            # Priorité 1: ID unique (le plus fiable)
            if element_id:
                identifier = f"{tag}#{element_id}"
                if include_position and driver:
                    position = ElementIdentifier._get_element_position(element, driver)
                    if position:
                        identifier += f"|pos={position}"
                return identifier
            
            # Priorité 2: Texte unique (pour les boutons, liens)
            if element_text and len(element_text) <= 50:
                # Nettoyer le texte pour éviter les caractères problématiques
                clean_text = element_text.replace('\n', ' ').replace('\r', ' ').strip()
                clean_text = ' '.join(clean_text.split())  # Supprimer les espaces multiples
                identifier = f"{tag}[text='{clean_text[:30]}']"
                if include_position and driver:
                    position = ElementIdentifier._get_element_position(element, driver)
                    if position:
                        identifier += f"|pos={position}"
                return identifier
            
            # Priorité 3: Href unique (pour les liens)
            if element_href and tag == 'a':
                clean_href = element_href[:50]
                identifier = f"{tag}[href='{clean_href}']"
                if include_position and driver:
                    position = ElementIdentifier._get_element_position(element, driver)
                    if position:
                        identifier += f"|pos={position}"
                return identifier
            
            # Priorité 4: Classe unique
            if element_class:
                # Prendre la première classe (la plus spécifique)
                first_class = element_class.split()[0]
                identifier = f"{tag}.{first_class}"
                if include_position and driver:
                    position = ElementIdentifier._get_element_position(element, driver)
                    if position:
                        identifier += f"|pos={position}"
                return identifier
            
            # Priorité 5: Type d'élément
            if element_type and tag in ['input', 'button']:
                identifier = f"{tag}[type='{element_type}']"
                if include_position and driver:
                    position = ElementIdentifier._get_element_position(element, driver)
                    if position:
                        identifier += f"|pos={position}"
                return identifier
            
            # Fallback: Hash de l'élément avec position
            element_hash = hash(str(element))
            identifier = f"{tag}[{element_hash}]"
            if include_position and driver:
                position = ElementIdentifier._get_element_position(element, driver)
                if position:
                    identifier += f"|pos={position}"
            return identifier
            
        except Exception as e:
            # En cas d'erreur, utiliser un hash simple
            return f"unknown_{hash(str(element))}"
    
    @staticmethod
    def _get_element_position(element, driver):
        """Récupère la position de l'élément dans le viewport"""
        try:
            rect = driver.execute_script("""
                var element = arguments[0];
                var rect = element.getBoundingClientRect();
                return {
                    x: Math.round(rect.left),
                    y: Math.round(rect.top),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                };
            """, element)
            
            # Retourner une position simplifiée
            return f"{rect['x']},{rect['y']}"
        except:
            return None
    
    @staticmethod
    def normalize_identifier(identifier):
        """
        Normalise un identifiant pour la comparaison
        
        Args:
            identifier: L'identifiant à normaliser
            
        Returns:
            str: Identifiant normalisé
        """
        if not identifier:
            return ""
        
        # Supprimer la position pour la comparaison
        if '|pos=' in identifier:
            identifier = identifier.split('|pos=')[0]
        
        # Normaliser la casse
        return identifier.lower()
    
    @staticmethod
    def find_matching_identifier(target_identifier, available_identifiers):
        """
        Trouve un identifiant correspondant dans une liste
        
        Args:
            target_identifier: L'identifiant à rechercher
            available_identifiers: Liste des identifiants disponibles
            
        Returns:
            str or None: L'identifiant correspondant ou None
        """
        if not target_identifier or not available_identifiers:
            return None
        
        # Normaliser l'identifiant cible
        normalized_target = ElementIdentifier.normalize_identifier(target_identifier)
        
        # Recherche exacte d'abord
        for identifier in available_identifiers:
            if ElementIdentifier.normalize_identifier(identifier) == normalized_target:
                return identifier
        
        # Recherche par similarité (pour les cas où la position diffère)
        for identifier in available_identifiers:
            normalized_available = ElementIdentifier.normalize_identifier(identifier)
            
            # Vérifier si les parties principales correspondent
            if (normalized_target.startswith(normalized_available.split('|')[0]) or
                normalized_available.startswith(normalized_target.split('|')[0])):
                return identifier
        
        return None
    
    @staticmethod
    def extract_element_info(identifier):
        """
        Extrait les informations d'un identifiant
        
        Args:
            identifier: L'identifiant à analyser
            
        Returns:
            dict: Informations extraites
        """
        info = {
            'tag': None,
            'id': None,
            'text': None,
            'href': None,
            'class': None,
            'type': None,
            'position': None
        }
        
        if not identifier:
            return info
        
        # Extraire le tag
        if '#' in identifier:
            parts = identifier.split('#')
            info['tag'] = parts[0]
            info['id'] = parts[1].split('|')[0]
        elif '[' in identifier and ']' in identifier:
            # Format: tag[attribute='value']
            tag_part = identifier.split('[')[0]
            info['tag'] = tag_part
            
            attr_part = identifier.split('[')[1].split(']')[0]
            if '=' in attr_part:
                attr_name, attr_value = attr_part.split('=', 1)
                attr_value = attr_value.strip("'\"")
                
                if attr_name == 'text':
                    info['text'] = attr_value
                elif attr_name == 'href':
                    info['href'] = attr_value
                elif attr_name == 'type':
                    info['type'] = attr_value
        elif '.' in identifier:
            # Format: tag.class
            parts = identifier.split('.')
            info['tag'] = parts[0]
            info['class'] = parts[1].split('|')[0]
        else:
            info['tag'] = identifier.split('|')[0]
        
        # Extraire la position si présente
        if '|pos=' in identifier:
            position_part = identifier.split('|pos=')[1]
            if ',' in position_part:
                x, y = position_part.split(',')
                info['position'] = {'x': int(x), 'y': int(y)}
        
        return info
