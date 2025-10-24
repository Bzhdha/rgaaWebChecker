#!/bin/bash
# Script de lancement pour le CSSMarker avec main_ordered.py

echo "🎨 CSSMarker - Intégration avec main_ordered.py"
echo "=============================================="
echo ""

# Vérifier que Python est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

# Activer l'environnement virtuel si disponible
if [ -d "venv" ]; then
    echo "🔧 Activation de l'environnement virtuel..."
    source venv/bin/activate
fi

echo "📋 Votre ligne de commande habituelle :"
echo "python main_ordered.py https://www.ouest-france.fr --modules screen --cookies \"OptanonAlertBoxClosed=2025-10-23T07:06:37.754Z\" --max-screenshots 200 --export-csv"
echo ""

echo "🎯 Avec le CSSMarker activé :"
echo "python main_ordered.py https://www.ouest-france.fr --modules screen --cookies \"OptanonAlertBoxClosed=2025-10-23T07:06:37.754Z\" --max-screenshots 200 --export-csv --css-marker --css-marker-delay 10"
echo ""

echo "✨ Nouvelles options disponibles :"
echo "   --css-marker              : Active le marquage CSS des éléments analysés"
echo "   --css-marker-delay N      : Délai en secondes pour observer les marquages (défaut: 5)"
echo ""

# Menu de choix
echo "Choisissez une option :"
echo "1) Lancer votre commande habituelle avec CSSMarker"
echo "2) Démonstration interactive"
echo "3) Afficher l'aide"
echo "4) Quitter"
echo ""

read -p "Votre choix (1-4) : " choice

case $choice in
    1)
        echo "🚀 Lancement avec CSSMarker..."
        echo "⏳ Cela peut prendre quelques minutes..."
        echo ""
        
        python main_ordered.py https://www.ouest-france.fr \
            --modules screen \
            --cookies "OptanonAlertBoxClosed=2025-10-23T07:06:37.754Z" \
            --max-screenshots 200 \
            --export-csv \
            --css-marker \
            --css-marker-delay 10
        ;;
    2)
        echo "🎯 Lancement de la démonstration interactive..."
        python demo_css_marker_ordered.py
        ;;
    3)
        echo "📖 Affichage de l'aide..."
        python demo_css_marker_ordered.py --help
        ;;
    4)
        echo "👋 Au revoir !"
        exit 0
        ;;
    *)
        echo "❌ Choix invalide"
        exit 1
        ;;
esac

echo ""
echo "✅ Opération terminée !"
echo ""
echo "🎨 Pendant l'analyse, vous avez pu observer :"
echo "   • Les éléments analysés marqués visuellement"
echo "   • Les éléments conformes avec bordure verte et badge ✅"
echo "   • Les éléments non conformes avec bordure rouge et badge ⚠️"
echo "   • Les tooltips informatifs au survol des éléments"
echo "   • Les styles spécifiques par type d'élément"
echo ""
echo "📚 Pour plus d'informations :"
echo "   • Guide d'utilisation : docs/CSS_MARKER_GUIDE.md"
echo "   • README dédié : README_CSS_MARKER.md"
echo "   • Tests : test_css_marker.py"
echo "   • Démonstration : demo_css_marker.py"
