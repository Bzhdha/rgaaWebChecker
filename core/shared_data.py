"""
Module de partage de données entre les modules d'analyse d'accessibilité
"""

class SharedData:
    """Classe pour partager des données entre les modules d'analyse"""
    
    def __init__(self):
        self.aria_data = {}  # Stockage des données ARIA par élément
        self.focusable_elements = []  # Liste des éléments focusables
        self.element_identifiers = {}  # Mapping des identifiants d'éléments
        
    def add_aria_data(self, element_identifier, aria_properties):
        """Ajoute les données ARIA d'un élément"""
        self.aria_data[element_identifier] = aria_properties
        
    def get_aria_data(self, element_identifier):
        """Récupère les données ARIA d'un élément"""
        return self.aria_data.get(element_identifier, {})
        
    def add_focusable_element(self, element_identifier, element_info):
        """Ajoute un élément focusable à la liste"""
        self.focusable_elements.append({
            'identifier': element_identifier,
            'info': element_info
        })
        
    def get_focusable_elements(self):
        """Récupère la liste des éléments focusables"""
        return self.focusable_elements
        
    def clear(self):
        """Vide toutes les données partagées"""
        self.aria_data.clear()
        self.focusable_elements.clear()
        self.element_identifiers.clear()
