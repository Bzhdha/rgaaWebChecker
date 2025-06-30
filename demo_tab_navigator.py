#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Démonstration du module de navigation tabulaire
Affiche les résultats et explique la liaison avec l'analyse DOM
"""

import json
import csv
import os
import sys
from modules.tab_navigator import TabNavigator
from utils.log_utils import setup_logger

def display_tab_results():
    """Affiche les résultats de l'analyse tabulaire"""
    
    print("🔍 ANALYSE DE NAVIGATION TABULAIRE")
    print("=" * 60)
    
    # Vérifier l'existence des fichiers de rapport
    csv_file = "rapport_analyse_tab.csv"
    json_file = "rapport_analyse_tab.json"
    
    if not os.path.exists(csv_file) and not os.path.exists(json_file):
        print("❌ Aucun rapport d'analyse tabulaire trouvé.")
        print("💡 Exécutez d'abord l'analyse avec le module tab:")
        print("   python main.py <URL> --modules tab")
        return
    
    # Lire le rapport JSON
    if os.path.exists(json_file):
        print(f"📄 Lecture du rapport JSON: {json_file}")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                tab_results = json.load(f)
            
            print(f"✅ {len(tab_results)} éléments capturés lors de la navigation tabulaire")
            
            # Afficher les statistiques
            print("\n📊 STATISTIQUES:")
            print("-" * 30)
            
            # Compter les éléments par type
            tag_counts = {}
            elements_with_xpath = 0
            elements_with_accessible_name = 0
            elements_with_aria = 0
            
            for result in tab_results:
                tag = result['tag']
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
                
                if result['xpath'] and result['xpath'] != 'unknown':
                    elements_with_xpath += 1
                
                if result['accessible_name']['name']:
                    elements_with_accessible_name += 1
                
                if result['aria_attributes']:
                    elements_with_aria += 1
            
            print(f"🔗 Éléments avec XPath unique: {elements_with_xpath}/{len(tab_results)}")
            print(f"📝 Éléments avec nom accessible: {elements_with_accessible_name}/{len(tab_results)}")
            print(f"♿ Éléments avec attributs ARIA: {elements_with_aria}/{len(tab_results)}")
            
            # Top 5 des types d'éléments
            print(f"\n🏆 Top 5 des types d'éléments:")
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            for tag, count in sorted_tags:
                print(f"   {tag}: {count}")
            
            # Afficher quelques exemples détaillés
            print(f"\n📋 EXEMPLES D'ÉLÉMENTS (5 premiers):")
            print("-" * 50)
            
            for i, result in enumerate(tab_results[:5]):
                print(f"\n{i+1}. Élément #{result['tab_index']}")
                print(f"   Tag: {result['tag']}")
                print(f"   XPath: {result['xpath']}")
                print(f"   CSS Selector: {result['css_selector']}")
                
                if result['text']:
                    print(f"   Texte: {result['text'][:50]}{'...' if len(result['text']) > 50 else ''}")
                
                if result['accessible_name']['name']:
                    print(f"   Nom accessible: {result['accessible_name']['name']} (source: {result['accessible_name']['source']})")
                else:
                    print(f"   Nom accessible: Aucun")
                
                if result['aria_attributes'].get('role'):
                    print(f"   Rôle ARIA: {result['aria_attributes']['role']}")
                
                if result['basic_attributes']['id']:
                    print(f"   ID: {result['basic_attributes']['id']}")
                
                if result['screenshots']['immediate']:
                    print(f"   Capture: {result['screenshots']['immediate']}")
            
            # Expliquer la liaison avec l'analyse DOM
            print(f"\n🔗 LIAISON AVEC L'ANALYSE DOM:")
            print("-" * 40)
            print("Les identifiants uniques (XPath) permettent de faire le lien")
            print("entre les éléments capturés lors de la navigation tabulaire")
            print("et les éléments analysés dans le rapport DOM.")
            print("\nPour faire la liaison:")
            print("1. Utilisez le XPath comme clé de correspondance")
            print("2. Comparez les propriétés d'accessibilité")
            print("3. Vérifiez la cohérence des noms accessibles")
            
        except Exception as e:
            print(f"❌ Erreur lors de la lecture du fichier JSON: {str(e)}")
    
    # Lire le rapport CSV
    if os.path.exists(csv_file):
        print(f"\n📄 Lecture du rapport CSV: {csv_file}")
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            print(f"✅ {len(rows)} lignes dans le fichier CSV")
            
            # Afficher les colonnes disponibles
            print(f"\n📋 Colonnes disponibles dans le CSV:")
            if rows:
                for i, column in enumerate(rows[0].keys(), 1):
                    print(f"   {i:2d}. {column}")
            
        except Exception as e:
            print(f"❌ Erreur lors de la lecture du fichier CSV: {str(e)}")

def show_usage_examples():
    """Affiche des exemples d'utilisation"""
    
    print(f"\n💡 EXEMPLES D'UTILISATION:")
    print("=" * 40)
    
    print("1. Analyse complète avec navigation tabulaire:")
    print("   python main.py https://example.com --modules tab")
    
    print("\n2. Analyse ciblée (tabulation + DOM):")
    print("   python main.py https://example.com --modules tab dom")
    
    print("\n3. Analyse avec debug pour voir les détails:")
    print("   python main.py https://example.com --modules tab --debug")
    
    print("\n4. Analyse avec gestion des cookies:")
    print("   python main.py https://example.com --modules tab --cookie-banner 'Accepter'")
    
    print("\n5. Test spécifique du module tabulaire:")
    print("   python test_tab_navigator.py")
    
    print("\n6. Options de délai de tabulation:")
    print("   python main.py https://example.com --modules tab --enable-tab-delay")
    print("   python main.py https://example.com --modules tab --tab-delay 1.0")
    print("   python main.py https://example.com --modules tab --tab-delay 2.5")
    
    print("\n7. Test des options de délai:")
    print("   python test_tab_delay.py")

def main():
    """Fonction principale de démonstration"""
    
    print("🎯 DÉMONSTRATION - NAVIGATION TABULAIRE")
    print("=" * 60)
    print("Ce script affiche les résultats de l'analyse de navigation tabulaire")
    print("et explique comment les identifiants uniques permettent la liaison")
    print("avec l'analyse DOM.")
    print()
    
    # Afficher les résultats
    display_tab_results()
    
    # Afficher les exemples d'utilisation
    show_usage_examples()
    
    print(f"\n✅ Démonstration terminée !")
    print("📁 Les fichiers de rapport sont disponibles dans le répertoire courant.")

if __name__ == "__main__":
    main() 