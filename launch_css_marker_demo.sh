#!/bin/bash
# Script de lancement pour la démonstration du système de marquage CSS

echo "🎨 Lancement de la démonstration CSS Marker"
echo "============================================="

# Vérifier que Python est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

# Vérifier que les dépendances sont installées
echo "🔍 Vérification des dépendances..."

if ! python3 -c "import selenium" 2>/dev/null; then
    echo "⚠️  Selenium n'est pas installé. Installation..."
    pip3 install selenium
fi

# Activer l'environnement virtuel si disponible
if [ -d "venv" ]; then
    echo "🔧 Activation de l'environnement virtuel..."
    source venv/bin/activate
fi

# Lancer la démonstration
echo "🚀 Lancement de la démonstration..."
echo ""

# Choisir le type de démonstration
echo "Choisissez le type de démonstration :"
echo "1) Démonstration simple (recommandé)"
echo "2) Tests complets"
echo "3) Démonstration avec DOMAnalyzer"
echo ""
read -p "Votre choix (1-3) : " choice

case $choice in
    1)
        echo "🎯 Lancement de la démonstration simple..."
        python3 demo_css_marker.py
        ;;
    2)
        echo "🧪 Lancement des tests complets..."
        python3 test_css_marker.py
        ;;
    3)
        echo "🔍 Lancement de la démonstration avec DOMAnalyzer..."
        echo "Note: Cette option nécessite une page web réelle"
        echo "Modifiez le script pour pointer vers une URL spécifique"
        ;;
    *)
        echo "❌ Choix invalide"
        exit 1
        ;;
esac

echo ""
echo "✅ Démonstration terminée !"
echo ""
echo "📚 Pour plus d'informations :"
echo "   • Guide d'utilisation : docs/CSS_MARKER_GUIDE.md"
echo "   • Tests unitaires : test_css_marker.py"
echo "   • Démonstration : demo_css_marker.py"
echo ""
echo "🎯 Fonctionnalités principales :"
echo "   • Marquage visuel des éléments analysés"
echo "   • Indication de la conformité (vert/rouge)"
echo "   • Tooltips informatifs au survol"
echo "   • Mode production pour masquer les marquages"
echo "   • Intégration avec tous les modules d'analyse"
