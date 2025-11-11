#!/usr/bin/env python3
"""
Script de test pour vérifier que TKSheet fonctionne correctement
"""

import tkinter as tk
from tksheet import Sheet

def test_tksheet():
    """Test simple de TKSheet"""
    root = tk.Tk()
    root.title("Test TKSheet")
    root.geometry("800x600")
    
    # Créer un tableau simple
    sheet = Sheet(root, 
                  headers=["Colonne 1", "Colonne 2", "Colonne 3"],
                  theme="light blue",
                  show_x_scrollbar=True,
                  show_y_scrollbar=True)
    
    # Ajouter quelques données de test
    test_data = [
        ["Ligne 1", "Donnée 1", "Valeur 1"],
        ["Ligne 2", "Donnée 2", "Valeur 2"],
        ["Ligne 3", "Donnée 3", "Valeur 3"],
    ]
    
    for i, row in enumerate(test_data):
        sheet.insert_row(i + 1, row)
    
    sheet.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    print("✅ TKSheet fonctionne correctement !")
    print("Fermez la fenêtre pour terminer le test.")
    
    root.mainloop()

if __name__ == "__main__":
    test_tksheet() 