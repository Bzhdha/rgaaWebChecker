#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de lancement pour l'interface graphique RGAA Web Checker
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

def check_dependencies():
    """Vérifie que toutes les dépendances sont installées"""
    missing_deps = []
    
    try:
        import PIL
    except ImportError:
        missing_deps.append("Pillow (PIL)")
    
    try:
        import selenium
    except ImportError:
        missing_deps.append("selenium")
    
    try:
        import webdriver_manager
    except ImportError:
        missing_deps.append("webdriver-manager")
    
    return missing_deps

def main():
    """Fonction principale"""
    print("RGAA Web Checker - Interface Graphique")
    print("=" * 40)
    
    # Vérifier les dépendances
    missing_deps = check_dependencies()
    if missing_deps:
        print("❌ Dépendances manquantes:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\nPour installer les dépendances manquantes:")
        print("pip install -r requirements.txt")
        return 1
    
    # Vérifier que les modules de l'application existent
    required_modules = [
        'core.config',
        'core.crawler', 
        'utils.log_utils',
        'modules.contrast_checker',
        'modules.dom_analyzer',
        'modules.color_simulator',
        'modules.tab_navigator',
        'modules.screen_reader',
        'modules.image_analyzer'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("❌ Modules de l'application manquants:")
        for module in missing_modules:
            print(f"   - {module}")
        print("\nAssurez-vous d'être dans le répertoire racine de l'application.")
        return 1
    
    print("✅ Toutes les dépendances sont installées")
    print("🚀 Lancement de l'interface graphique...")
    
    try:
        # Importer et lancer l'interface graphique
        from gui_app import main as gui_main
        gui_main()
        return 0
        
    except Exception as e:
        print(f"❌ Erreur lors du lancement: {str(e)}")
        
        # Afficher une boîte de dialogue d'erreur si possible
        try:
            root = tk.Tk()
            root.withdraw()  # Cacher la fenêtre principale
            messagebox.showerror(
                "Erreur de lancement",
                f"Impossible de lancer l'interface graphique:\n\n{str(e)}\n\n"
                "Vérifiez que toutes les dépendances sont installées:\n"
                "pip install -r requirements.txt"
            )
            root.destroy()
        except:
            pass
        
        return 1

if __name__ == "__main__":
    sys.exit(main()) 