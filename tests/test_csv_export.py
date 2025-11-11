#!/usr/bin/env python3
"""
Script de test pour l'export CSV des données d'accessibilité
"""

import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.csv_exporter import CSVExporter
from core.shared_data import SharedData

def test_csv_export():
    """Test de l'export CSV avec des données fictives"""
    
    print("🧪 Test de l'export CSV des données d'accessibilité")
    print("=" * 60)
    
    # Créer des données de test
    shared_data = SharedData()
    
    # Ajouter des données ARIA fictives
    test_aria_data = {
        "button#submit": {
            "Type": "BUTTON",
            "Rôle": "button",
            "Aria-label": "Soumettre le formulaire",
            "Aria-describedby": "help-text",
            "Aria-hidden": "false",
            "Aria-expanded": "false",
            "Aria-controls": "",
            "Aria-live": "",
            "Aria-atomic": "",
            "Aria-relevant": "",
            "Aria-busy": "",
            "Aria-current": "",
            "Aria-posinset": "",
            "Aria-setsize": "",
            "Aria-level": "",
            "Aria-sort": "",
            "Aria-valuemin": "",
            "Aria-valuemax": "",
            "Aria-valuenow": "",
            "Aria-valuetext": "",
            "Aria-haspopup": "",
            "Aria-invalid": "",
            "Aria-required": "",
            "Aria-readonly": "",
            "Aria-disabled": "",
            "Aria-selected": "",
            "Aria-checked": "",
            "Aria-pressed": "",
            "Aria-multiline": "",
            "Aria-multiselectable": "",
            "Aria-orientation": "",
            "Aria-placeholder": "",
            "Aria-roledescription": "",
            "Aria-keyshortcuts": "",
            "Aria-details": "",
            "Aria-errormessage": "",
            "Aria-flowto": "",
            "Aria-owns": "",
            "Tabindex": "0",
            "Title": "Bouton de soumission",
            "Alt": "",
            "Text": "Soumettre",
            "Visible": "Oui",
            "Focusable": "Oui",
            "Id": "submit",
            "Sélecteur": "button#submit",
            "Extrait HTML": "<button id='submit' aria-label='Soumettre le formulaire'>Soumettre</button>",
            "MediaPath": "",
            "MediaType": ""
        },
        "input#email": {
            "Type": "INPUT",
            "Rôle": "textbox",
            "Aria-label": "Adresse e-mail",
            "Aria-describedby": "email-help",
            "Aria-hidden": "false",
            "Aria-expanded": "",
            "Aria-controls": "",
            "Aria-live": "",
            "Aria-atomic": "",
            "Aria-relevant": "",
            "Aria-busy": "",
            "Aria-current": "",
            "Aria-posinset": "",
            "Aria-setsize": "",
            "Aria-level": "",
            "Aria-sort": "",
            "Aria-valuemin": "",
            "Aria-valuemax": "",
            "Aria-valuenow": "",
            "Aria-valuetext": "",
            "Aria-haspopup": "",
            "Aria-invalid": "",
            "Aria-required": "true",
            "Aria-readonly": "",
            "Aria-disabled": "",
            "Aria-selected": "",
            "Aria-checked": "",
            "Aria-pressed": "",
            "Aria-multiline": "",
            "Aria-multiselectable": "",
            "Aria-orientation": "",
            "Aria-placeholder": "Entrez votre e-mail",
            "Aria-roledescription": "",
            "Aria-keyshortcuts": "",
            "Aria-details": "",
            "Aria-errormessage": "",
            "Aria-flowto": "",
            "Aria-owns": "",
            "Tabindex": "0",
            "Title": "",
            "Alt": "",
            "Text": "",
            "Visible": "Oui",
            "Focusable": "Oui",
            "Id": "email",
            "Sélecteur": "input#email",
            "Extrait HTML": "<input id='email' type='email' aria-label='Adresse e-mail' aria-required='true' placeholder='Entrez votre e-mail'>",
            "MediaPath": "",
            "MediaType": ""
        }
    }
    
    # Ajouter des éléments focusables fictifs
    test_focusable_data = [
        {
            "identifier": "link#home",
            "info": {
                "Type": "A",
                "Rôle": "link",
                "Aria-label": "Accueil",
                "Aria-describedby": "",
                "Aria-labelledby": "",
                "Aria-hidden": "false",
                "Aria-expanded": "",
                "Aria-controls": "",
                "Aria-live": "",
                "Aria-atomic": "",
                "Aria-relevant": "",
                "Aria-busy": "",
                "Aria-current": "",
                "Aria-posinset": "",
                "Aria-setsize": "",
                "Aria-level": "",
                "Aria-sort": "",
                "Aria-valuemin": "",
                "Aria-valuemax": "",
                "Aria-valuenow": "",
                "Aria-valuetext": "",
                "Aria-haspopup": "",
                "Aria-invalid": "",
                "Aria-required": "",
                "Aria-readonly": "",
                "Aria-disabled": "",
                "Aria-selected": "",
                "Aria-checked": "",
                "Aria-pressed": "",
                "Aria-multiline": "",
                "Aria-multiselectable": "",
                "Aria-orientation": "",
                "Aria-placeholder": "",
                "Aria-roledescription": "",
                "Aria-keyshortcuts": "",
                "Aria-details": "",
                "Aria-errormessage": "",
                "Aria-flowto": "",
                "Aria-owns": "",
                "Tabindex": "0",
                "Title": "Retour à l'accueil",
                "Alt": "",
                "Text": "Accueil",
                "Visible": "Oui",
                "Focusable": "Oui",
                "Id": "home",
                "Sélecteur": "a#home",
                "Extrait HTML": "<a id='home' href='/' title='Retour à l'accueil'>Accueil</a>",
                "MediaPath": "",
                "MediaType": ""
            }
        }
    ]
    
    # Remplir les données partagées
    for element_id, data in test_aria_data.items():
        shared_data.add_aria_data(element_id, data)
    
    for element in test_focusable_data:
        shared_data.add_focusable_element(element["identifier"], element["info"])
    
    print(f"📊 Données de test créées:")
    print(f"   - Éléments ARIA: {len(shared_data.aria_data)}")
    print(f"   - Éléments focusables: {len(shared_data.focusable_elements)}")
    
    # Tester l'export CSV
    try:
        exporter = CSVExporter()
        
        print("\n🔄 Test de l'export CSV complet...")
        filepath = exporter.export_complete_data(shared_data, "test_accessibility_data.csv")
        print(f"✅ Export réussi: {filepath}")
        
        # Vérifier que le fichier existe
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"📄 Taille du fichier: {file_size} octets")
            
            # Afficher les premières lignes du fichier
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
                print(f"📝 Nombre de lignes: {len(lines)}")
                print("\n📋 Aperçu du fichier CSV:")
                for i, line in enumerate(lines[:5]):  # Afficher les 5 premières lignes
                    print(f"   Ligne {i+1}: {line.strip()[:100]}...")
        else:
            print("❌ Le fichier CSV n'a pas été créé")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False
    
    print("\n🎉 Test terminé avec succès!")
    return True

if __name__ == "__main__":
    success = test_csv_export()
    sys.exit(0 if success else 1)
