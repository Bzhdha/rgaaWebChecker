#!/usr/bin/env python3
"""
Démonstration du CSSMarker avec main_ordered.py
Montre comment utiliser le marquage CSS avec votre ligne de commande habituelle
"""

import subprocess
import sys
import time
import os

def run_demo():
    """Lance une démonstration du CSSMarker avec main_ordered.py"""
    
    print("🎨 Démonstration du CSSMarker avec main_ordered.py")
    print("=" * 60)
    print()
    
    # URL de test (vous pouvez la changer)
    test_url = "https://www.ouest-france.fr"
    
    print("📋 Votre ligne de commande habituelle :")
    print("python main_ordered.py https://www.ouest-france.fr --modules screen --cookies \"OptanonAlertBoxClosed=2025-10-23T07:06:37.754Z\" --max-screenshots 200 --export-csv")
    print()
    
    print("🎯 Avec le CSSMarker activé :")
    print("python main_ordered.py https://www.ouest-france.fr --modules screen --cookies \"OptanonAlertBoxClosed=2025-10-23T07:06:37.754Z\" --max-screenshots 200 --export-csv --css-marker --css-marker-delay 10")
    print()
    
    print("✨ Nouvelles options disponibles :")
    print("   --css-marker              : Active le marquage CSS des éléments analysés")
    print("   --css-marker-delay N      : Délai en secondes pour observer les marquages (défaut: 5)")
    print()
    
    # Demander si l'utilisateur veut lancer la démonstration
    response = input("Voulez-vous lancer la démonstration avec le CSSMarker ? (o/n): ")
    
    if response.lower() in ['o', 'oui', 'y', 'yes']:
        print("\n🚀 Lancement de la démonstration...")
        print("⏳ Cela peut prendre quelques minutes...")
        print()
        
        # Commande avec CSSMarker
        cmd = [
            "python", "main_ordered.py",
            test_url,
            "--modules", "screen",
            "--cookies", "OptanonAlertBoxClosed=2025-10-23T07:06:37.754Z",
            "--max-screenshots", "50",  # Réduit pour la démo
            "--export-csv",
            "--css-marker",
            "--css-marker-delay", "15"  # Plus de temps pour observer
        ]
        
        try:
            # Lancer la commande
            result = subprocess.run(cmd, capture_output=False, text=True)
            
            if result.returncode == 0:
                print("\n✅ Démonstration terminée avec succès !")
                print("\n🎨 Pendant l'analyse, vous avez pu observer :")
                print("   • Les éléments analysés marqués visuellement")
                print("   • Les éléments conformes avec bordure verte et badge ✅")
                print("   • Les éléments non conformes avec bordure rouge et badge ⚠️")
                print("   • Les tooltips informatifs au survol des éléments")
                print("   • Les styles spécifiques par type d'élément")
            else:
                print(f"\n❌ Erreur lors de l'exécution (code: {result.returncode})")
                
        except KeyboardInterrupt:
            print("\n⏹️  Démonstration interrompue par l'utilisateur")
        except Exception as e:
            print(f"\n❌ Erreur lors de la démonstration : {e}")
    else:
        print("\n📚 Pour utiliser le CSSMarker avec votre ligne de commande :")
        print()
        print("1. Ajoutez --css-marker à votre commande")
        print("2. Optionnellement, ajoutez --css-marker-delay N pour le délai d'observation")
        print()
        print("Exemple complet :")
        print("python main_ordered.py https://www.ouest-france.fr --modules screen --cookies \"OptanonAlertBoxClosed=2025-10-23T07:06:37.754Z\" --max-screenshots 200 --export-csv --css-marker --css-marker-delay 10")
        print()
        print("🎯 Avantages du CSSMarker :")
        print("   • Identification visuelle immédiate des éléments analysés")
        print("   • Distinction claire entre éléments conformes et non conformes")
        print("   • Tooltips informatifs pour le débogage")
        print("   • Styles spécifiques par type d'élément")
        print("   • Mode production pour masquer les marquages")

def show_help():
    """Affiche l'aide pour le CSSMarker"""
    print("\n📖 Aide du CSSMarker")
    print("=" * 30)
    print()
    print("🎨 Fonctionnalités :")
    print("   • Marquage visuel des éléments analysés")
    print("   • Indication de la conformité (vert/rouge)")
    print("   • Tooltips informatifs au survol")
    print("   • Styles spécifiques par type d'élément")
    print()
    print("🔧 Options disponibles :")
    print("   --css-marker              : Active le marquage CSS")
    print("   --css-marker-delay N      : Délai d'observation en secondes")
    print()
    print("📋 Types d'éléments supportés :")
    print("   • Titres (h1-h6) : Bordure bleue à gauche")
    print("   • Images : Bordure en pointillés bleue")
    print("   • Liens : Soulignement bleu")
    print("   • Boutons : Bordure bleue avec coins arrondis")
    print("   • Formulaires : Bordure bleue avec padding")
    print("   • Landmarks : Bordure violette")
    print("   • Éléments ARIA : Bordure orange")
    print()
    print("🎯 Statuts de conformité :")
    print("   • ✅ Conforme : Bordure verte avec badge")
    print("   • ⚠️  Non conforme : Bordure rouge avec badge")
    print("   • 🔍 En cours d'analyse : Bordure jaune avec badge")

def main():
    """Fonction principale"""
    print("🎨 CSSMarker - Intégration avec main_ordered.py")
    print("=" * 50)
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        show_help()
        return
    
    print("Cette démonstration montre comment intégrer le CSSMarker")
    print("dans votre ligne de commande habituelle avec main_ordered.py")
    print()
    
    run_demo()
    
    print("\n📚 Documentation complète :")
    print("   • Guide d'utilisation : docs/CSS_MARKER_GUIDE.md")
    print("   • README dédié : README_CSS_MARKER.md")
    print("   • Tests : test_css_marker.py")
    print("   • Démonstration : demo_css_marker.py")
    print()
    print("🎯 Le CSSMarker transforme l'analyse d'accessibilité en une")
    print("   expérience visuelle intuitive pour les automaticiens !")

if __name__ == "__main__":
    main()
