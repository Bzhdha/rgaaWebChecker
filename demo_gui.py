#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de démonstration pour l'interface graphique RGAA Web Checker
Ce script lance l'interface avec des données d'exemple pour tester les fonctionnalités
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

def show_demo_info():
    """Affiche les informations de démonstration"""
    info = """
    🎯 DÉMONSTRATION - RGAA Web Checker Interface Graphique
    
    Cette démonstration vous permet de tester l'interface graphique
    avec des données d'exemple sans effectuer de vraie analyse.
    
    📋 Fonctionnalités à tester :
    
    1. Configuration de l'analyse
       - Saisie d'URL
       - Sélection des modules
       - Options avancées
    
    2. Interface des résultats
       - Statistiques
       - Tableau détaillé
       - Export CSV/JSON
    
    3. Visualisation des images
       - Navigation entre images
       - Zoom et défilement
    
    4. Gestion des logs
       - Logs en temps réel
       - Sauvegarde
    
    🚀 Pour tester avec de vraies données :
    - Saisissez une URL réelle
    - Cliquez sur "Démarrer l'analyse"
    
    ⚠️  Note : Cette démonstration utilise des données fictives
    """
    
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Démonstration RGAA Web Checker", info)
    root.destroy()

def create_demo_data():
    """Crée des données de démonstration"""
    demo_results = {
        'contrast': [
            {
                'type': 'Contraste insuffisant',
                'message': 'Le texte "Bienvenue" a un ratio de contraste de 2.1 (minimum requis: 4.5)',
                'severity': 'high'
            },
            {
                'type': 'Contraste insuffisant',
                'message': 'Le lien "En savoir plus" a un ratio de contraste de 3.2 (minimum requis: 4.5)',
                'severity': 'medium'
            }
        ],
        'dom': [
            {
                'type': 'Attribut manquant',
                'message': 'L\'image "logo.png" n\'a pas d\'attribut alt',
                'severity': 'critical'
            },
            {
                'type': 'Rôle ARIA invalide',
                'message': 'L\'élément div a un rôle "button" mais n\'est pas focusable',
                'severity': 'medium'
            }
        ],
        'image': [
            {
                'type': 'Image sans alt',
                'message': 'Image "banner.jpg" sans texte alternatif',
                'severity': 'critical'
            },
            {
                'type': 'Image décorative',
                'message': 'Image "decoration.png" devrait avoir alt=""',
                'severity': 'low'
            }
        ],
        'screen': [
            {
                'type': 'Titre manquant',
                'message': 'La page n\'a pas de titre principal (h1)',
                'severity': 'high'
            },
            {
                'type': 'Landmark manquant',
                'message': 'Aucun landmark "main" trouvé sur la page',
                'severity': 'medium'
            }
        ],
        'tab': [
            {
                'type': 'Ordre de tabulation',
                'message': 'L\'ordre de tabulation n\'est pas logique',
                'severity': 'medium'
            }
        ]
    }
    
    return demo_results

def main():
    """Fonction principale de démonstration"""
    print("🎯 RGAA Web Checker - Démonstration Interface Graphique")
    print("=" * 60)
    
    # Afficher les informations de démonstration
    show_demo_info()
    
    # Vérifier que l'interface graphique existe
    if not os.path.exists('gui_app.py'):
        print("❌ Erreur: gui_app.py non trouvé")
        print("Assurez-vous d'être dans le répertoire racine de l'application")
        return 1
    
    # Vérifier les dépendances
    try:
        import tkinter
        print("✅ Tkinter disponible")
    except ImportError:
        print("❌ Tkinter non disponible")
        print("Installer: sudo apt install python3-tk (Ubuntu/Linux)")
        return 1
    
    try:
        from PIL import Image
        print("✅ Pillow (PIL) disponible")
    except ImportError:
        print("❌ Pillow (PIL) non disponible")
        print("Installer: pip install Pillow")
        return 1
    
    print("✅ Toutes les dépendances sont disponibles")
    print("🚀 Lancement de l'interface graphique...")
    
    try:
        # Importer et lancer l'interface graphique
        from gui_app import main as gui_main
        
        # Modifier temporairement la classe pour ajouter des données de démonstration
        import gui_app
        
        # Sauvegarder la méthode originale
        original_process_results = gui_app.RGAAWebCheckerGUI.process_results
        
        def demo_process_results(self, results):
            """Version de démonstration qui utilise des données fictives"""
            demo_data = create_demo_data()
            original_process_results(self, demo_data)
            
            # Ajouter un message de démonstration
            self.update_logs("🎯 MODE DÉMONSTRATION - Données fictives utilisées")
            self.update_logs("Pour une vraie analyse, saisissez une URL et cliquez sur 'Démarrer l'analyse'")
        
        # Remplacer temporairement la méthode
        gui_app.RGAAWebCheckerGUI.process_results = demo_process_results
        
        # Lancer l'interface
        gui_main()
        
        return 0
        
    except Exception as e:
        print(f"❌ Erreur lors du lancement: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 