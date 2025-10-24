"""
Module d'export CSV pour les données d'accessibilité collectées
"""

import csv
import os
from datetime import datetime
from typing import Dict, List, Any


class CSVExporter:
    """Classe pour exporter les données d'accessibilité en CSV"""
    
    def __init__(self, output_dir='reports'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def export_aria_data(self, aria_data: Dict[str, Any], filename=None):
        """
        Exporte les données ARIA collectées en CSV
        
        Args:
            aria_data: Dictionnaire des données ARIA par élément
            filename: Nom du fichier CSV (optionnel)
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"aria_data_export_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # En-têtes CSV pour les données ARIA
        headers = [
            "Element_ID",
            "Type",
            "Rôle",
            "Aria-label",
            "Aria-describedby", 
            "Aria-labelledby",
            "Aria-hidden",
            "Aria-expanded",
            "Aria-controls",
            "Aria-live",
            "Aria-atomic",
            "Aria-relevant",
            "Aria-busy",
            "Aria-current",
            "Aria-posinset",
            "Aria-setsize",
            "Aria-level",
            "Aria-sort",
            "Aria-valuemin",
            "Aria-valuemax",
            "Aria-valuenow",
            "Aria-valuetext",
            "Aria-haspopup",
            "Aria-invalid",
            "Aria-required",
            "Aria-readonly",
            "Aria-disabled",
            "Aria-selected",
            "Aria-checked",
            "Aria-pressed",
            "Aria-multiline",
            "Aria-multiselectable",
            "Aria-orientation",
            "Aria-placeholder",
            "Aria-roledescription",
            "Aria-keyshortcuts",
            "Aria-details",
            "Aria-errormessage",
            "Aria-flowto",
            "Aria-owns",
            "Tabindex",
            "Title",
            "Alt",
            "Text",
            "Visible",
            "Focusable",
            "Id",
            "Sélecteur",
            "Extrait_HTML",
            "MediaPath",
            "MediaType"
        ]
        
        try:
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                
                # Écrire les en-têtes
                writer.writerow(headers)
                
                # Écrire les données pour chaque élément
                for element_id, data in aria_data.items():
                    row = [
                        element_id,
                        data.get("Type", ""),
                        data.get("Rôle", ""),
                        data.get("Aria-label", ""),
                        data.get("Aria-describedby", ""),
                        data.get("Aria-labelledby", ""),
                        data.get("Aria-hidden", ""),
                        data.get("Aria-expanded", ""),
                        data.get("Aria-controls", ""),
                        data.get("Aria-live", ""),
                        data.get("Aria-atomic", ""),
                        data.get("Aria-relevant", ""),
                        data.get("Aria-busy", ""),
                        data.get("Aria-current", ""),
                        data.get("Aria-posinset", ""),
                        data.get("Aria-setsize", ""),
                        data.get("Aria-level", ""),
                        data.get("Aria-sort", ""),
                        data.get("Aria-valuemin", ""),
                        data.get("Aria-valuemax", ""),
                        data.get("Aria-valuenow", ""),
                        data.get("Aria-valuetext", ""),
                        data.get("Aria-haspopup", ""),
                        data.get("Aria-invalid", ""),
                        data.get("Aria-required", ""),
                        data.get("Aria-readonly", ""),
                        data.get("Aria-disabled", ""),
                        data.get("Aria-selected", ""),
                        data.get("Aria-checked", ""),
                        data.get("Aria-pressed", ""),
                        data.get("Aria-multiline", ""),
                        data.get("Aria-multiselectable", ""),
                        data.get("Aria-orientation", ""),
                        data.get("Aria-placeholder", ""),
                        data.get("Aria-roledescription", ""),
                        data.get("Aria-keyshortcuts", ""),
                        data.get("Aria-details", ""),
                        data.get("Aria-errormessage", ""),
                        data.get("Aria-flowto", ""),
                        data.get("Aria-owns", ""),
                        data.get("Tabindex", ""),
                        data.get("Title", ""),
                        data.get("Alt", ""),
                        data.get("Text", ""),
                        data.get("Visible", ""),
                        data.get("Focusable", ""),
                        data.get("Id", ""),
                        data.get("Sélecteur", ""),
                        data.get("Extrait HTML", ""),
                        data.get("MediaPath", ""),
                        data.get("MediaType", "")
                    ]
                    writer.writerow(row)
            
            return filepath
            
        except Exception as e:
            raise Exception(f"Erreur lors de l'export CSV: {e}")
    
    def export_focusable_elements(self, focusable_elements: List[Dict], filename=None):
        """
        Exporte les éléments focusables en CSV
        
        Args:
            focusable_elements: Liste des éléments focusables
            filename: Nom du fichier CSV (optionnel)
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"focusable_elements_export_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        headers = [
            "Element_ID",
            "Type",
            "Text",
            "Title",
            "Alt",
            "Role",
            "Tabindex",
            "Visible",
            "Focusable",
            "Selector",
            "HTML_Extract"
        ]
        
        try:
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                
                # Écrire les en-têtes
                writer.writerow(headers)
                
                # Écrire les données pour chaque élément focusable
                for element in focusable_elements:
                    info = element.get('info', {})
                    row = [
                        element.get('identifier', ''),
                        info.get("Type", ""),
                        info.get("Text", ""),
                        info.get("Title", ""),
                        info.get("Alt", ""),
                        info.get("Rôle", ""),
                        info.get("Tabindex", ""),
                        info.get("Visible", ""),
                        info.get("Focusable", ""),
                        info.get("Sélecteur", ""),
                        info.get("Extrait HTML", "")
                    ]
                    writer.writerow(row)
            
            return filepath
            
        except Exception as e:
            raise Exception(f"Erreur lors de l'export CSV des éléments focusables: {e}")
    
    def export_complete_data(self, shared_data, filename=None):
        """
        Exporte toutes les données collectées en CSV
        
        Args:
            shared_data: Objet SharedData contenant toutes les données
            filename: Nom du fichier CSV (optionnel)
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"complete_accessibility_data_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # En-têtes pour toutes les données
        headers = [
            "Element_ID",
            "Data_Type",  # ARIA ou FOCUSABLE
            "Type",
            "Rôle",
            "Aria-label",
            "Aria-describedby",
            "Aria-labelledby", 
            "Aria-hidden",
            "Aria-expanded",
            "Aria-controls",
            "Aria-live",
            "Aria-atomic",
            "Aria-relevant",
            "Aria-busy",
            "Aria-current",
            "Aria-posinset",
            "Aria-setsize",
            "Aria-level",
            "Aria-sort",
            "Aria-valuemin",
            "Aria-valuemax",
            "Aria-valuenow",
            "Aria-valuetext",
            "Aria-haspopup",
            "Aria-invalid",
            "Aria-required",
            "Aria-readonly",
            "Aria-disabled",
            "Aria-selected",
            "Aria-checked",
            "Aria-pressed",
            "Aria-multiline",
            "Aria-multiselectable",
            "Aria-orientation",
            "Aria-placeholder",
            "Aria-roledescription",
            "Aria-keyshortcuts",
            "Aria-details",
            "Aria-errormessage",
            "Aria-flowto",
            "Aria-owns",
            "Tabindex",
            "Title",
            "Alt",
            "Text",
            "Visible",
            "Focusable",
            "Id",
            "Sélecteur",
            "Extrait_HTML",
            "MediaPath",
            "MediaType"
        ]
        
        try:
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                
                # Écrire les en-têtes
                writer.writerow(headers)
                
                # Écrire les données ARIA
                for element_id, data in shared_data.aria_data.items():
                    row = [
                        element_id,
                        "ARIA",
                        data.get("Type", ""),
                        data.get("Rôle", ""),
                        data.get("Aria-label", ""),
                        data.get("Aria-describedby", ""),
                        data.get("Aria-labelledby", ""),
                        data.get("Aria-hidden", ""),
                        data.get("Aria-expanded", ""),
                        data.get("Aria-controls", ""),
                        data.get("Aria-live", ""),
                        data.get("Aria-atomic", ""),
                        data.get("Aria-relevant", ""),
                        data.get("Aria-busy", ""),
                        data.get("Aria-current", ""),
                        data.get("Aria-posinset", ""),
                        data.get("Aria-setsize", ""),
                        data.get("Aria-level", ""),
                        data.get("Aria-sort", ""),
                        data.get("Aria-valuemin", ""),
                        data.get("Aria-valuemax", ""),
                        data.get("Aria-valuenow", ""),
                        data.get("Aria-valuetext", ""),
                        data.get("Aria-haspopup", ""),
                        data.get("Aria-invalid", ""),
                        data.get("Aria-required", ""),
                        data.get("Aria-readonly", ""),
                        data.get("Aria-disabled", ""),
                        data.get("Aria-selected", ""),
                        data.get("Aria-checked", ""),
                        data.get("Aria-pressed", ""),
                        data.get("Aria-multiline", ""),
                        data.get("Aria-multiselectable", ""),
                        data.get("Aria-orientation", ""),
                        data.get("Aria-placeholder", ""),
                        data.get("Aria-roledescription", ""),
                        data.get("Aria-keyshortcuts", ""),
                        data.get("Aria-details", ""),
                        data.get("Aria-errormessage", ""),
                        data.get("Aria-flowto", ""),
                        data.get("Aria-owns", ""),
                        data.get("Tabindex", ""),
                        data.get("Title", ""),
                        data.get("Alt", ""),
                        data.get("Text", ""),
                        data.get("Visible", ""),
                        data.get("Focusable", ""),
                        data.get("Id", ""),
                        data.get("Sélecteur", ""),
                        data.get("Extrait HTML", ""),
                        data.get("MediaPath", ""),
                        data.get("MediaType", "")
                    ]
                    writer.writerow(row)
                
                # Écrire les données des éléments focusables
                for element in shared_data.focusable_elements:
                    info = element.get('info', {})
                    row = [
                        element.get('identifier', ''),
                        "FOCUSABLE",
                        info.get("Type", ""),
                        info.get("Rôle", ""),
                        info.get("Aria-label", ""),
                        info.get("Aria-describedby", ""),
                        info.get("Aria-labelledby", ""),
                        info.get("Aria-hidden", ""),
                        info.get("Aria-expanded", ""),
                        info.get("Aria-controls", ""),
                        info.get("Aria-live", ""),
                        info.get("Aria-atomic", ""),
                        info.get("Aria-relevant", ""),
                        info.get("Aria-busy", ""),
                        info.get("Aria-current", ""),
                        info.get("Aria-posinset", ""),
                        info.get("Aria-setsize", ""),
                        info.get("Aria-level", ""),
                        info.get("Aria-sort", ""),
                        info.get("Aria-valuemin", ""),
                        info.get("Aria-valuemax", ""),
                        info.get("Aria-valuenow", ""),
                        info.get("Aria-valuetext", ""),
                        info.get("Aria-haspopup", ""),
                        info.get("Aria-invalid", ""),
                        info.get("Aria-required", ""),
                        info.get("Aria-readonly", ""),
                        info.get("Aria-disabled", ""),
                        info.get("Aria-selected", ""),
                        info.get("Aria-checked", ""),
                        info.get("Aria-pressed", ""),
                        info.get("Aria-multiline", ""),
                        info.get("Aria-multiselectable", ""),
                        info.get("Aria-orientation", ""),
                        info.get("Aria-placeholder", ""),
                        info.get("Aria-roledescription", ""),
                        info.get("Aria-keyshortcuts", ""),
                        info.get("Aria-details", ""),
                        info.get("Aria-errormessage", ""),
                        info.get("Aria-flowto", ""),
                        info.get("Aria-owns", ""),
                        info.get("Tabindex", ""),
                        info.get("Title", ""),
                        info.get("Alt", ""),
                        info.get("Text", ""),
                        info.get("Visible", ""),
                        info.get("Focusable", ""),
                        info.get("Id", ""),
                        info.get("Sélecteur", ""),
                        info.get("Extrait HTML", ""),
                        info.get("MediaPath", ""),
                        info.get("MediaType", "")
                    ]
                    writer.writerow(row)
            
            return filepath
            
        except Exception as e:
            raise Exception(f"Erreur lors de l'export CSV complet: {e}")
