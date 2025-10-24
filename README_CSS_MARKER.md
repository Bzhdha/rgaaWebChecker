# 🎨 Système de marquage CSS pour l'analyse d'accessibilité

## Vue d'ensemble

Le système de marquage CSS permet d'ajouter des balises visuelles aux éléments analysés par le RGAA Web Checker, facilitant ainsi l'identification et le débogage des problèmes d'accessibilité pour les automaticiens.

## ✨ Fonctionnalités principales

### 🎯 Marquage visuel intelligent
- **Éléments conformes** : Bordure verte avec badge ✅
- **Éléments non conformes** : Bordure rouge avec badge ⚠️  
- **Éléments en cours d'analyse** : Bordure jaune avec badge 🔍

### 📋 Support complet des types d'éléments
- **Titres** (h1-h6) : Bordure bleue à gauche
- **Images** : Bordure en pointillés bleue
- **Liens** : Soulignement bleu
- **Boutons** : Bordure bleue avec coins arrondis
- **Formulaires** : Bordure bleue avec padding
- **Landmarks** : Bordure violette
- **Éléments ARIA** : Bordure orange

### 💡 Tooltips informatifs
- Informations détaillées au survol
- Statut de conformité
- Liste des problèmes détectés
- Nom accessible et rôle ARIA

## 🚀 Démarrage rapide

### Installation

```bash
# Cloner le projet
git clone <repository-url>
cd rgaaWebChecker

# Installer les dépendances
pip install -r requirements.txt

# Activer l'environnement virtuel (optionnel)
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### Lancement de la démonstration

#### Linux/Mac
```bash
chmod +x launch_css_marker_demo.sh
./launch_css_marker_demo.sh
```

#### Windows
```powershell
.\launch_css_marker_demo.ps1
```

#### Lancement direct
```bash
# Démonstration simple
python demo_css_marker.py

# Tests complets
python test_css_marker.py
```

## 📖 Utilisation

### Utilisation basique

```python
from modules.css_marker import CSSMarker
from modules.dom_analyzer import DOMAnalyzer

# Avec DOMAnalyzer (recommandé)
dom_analyzer = DOMAnalyzer(driver, logger, enable_css_marking=True)
result = dom_analyzer.run()

# Utilisation directe
css_marker = CSSMarker(driver, logger)
css_marker.mark_element(element, "image", [], True, "Image conforme")
```

### Marquage personnalisé

```python
# Marquer un élément avec des problèmes
css_marker.mark_element(
    element=element,
    element_type="link",
    issues=["Lien sans texte visible"],
    compliant=False,
    info="Lien non conforme - pas de texte visible"
)
```

### Marquage en lot (optimisé)

```python
elements_data = []
for element in elements:
    elements_data.append({
        'element': element,
        'type': 'heading',
        'issues': [],
        'compliant': True,
        'info': f"Titre {element.tag_name} - conforme"
    })

css_marker.mark_elements_batch(elements_data)
```

## 🎨 Personnalisation des styles

### Styles CSS par défaut

Le système injecte automatiquement des styles CSS optimisés :

```css
/* Éléments conformes */
.rgaa-compliant {
    outline: 2px solid #28a745 !important;
    background-color: rgba(40, 167, 69, 0.1) !important;
}

/* Éléments non conformes */
.rgaa-issue {
    outline: 2px solid #dc3545 !important;
    background-color: rgba(220, 53, 69, 0.1) !important;
}

/* Badges informatifs */
.rgaa-badge-compliant {
    background: #28a745 !important;
}
```

### Personnalisation avancée

```python
# Injecter des styles personnalisés
custom_css = """
<style>
.rgaa-analyzed {
    outline: 3px solid #ff6b6b !important;
    outline-offset: 3px !important;
}
</style>
"""

driver.execute_script(f"""
    var style = document.createElement('style');
    style.innerHTML = `{custom_css}`;
    document.head.appendChild(style);
""")
```

## 🔧 Intégration avec les modules

### DOMAnalyzer

```python
# Activation automatique du marquage
dom_analyzer = DOMAnalyzer(driver, logger, enable_css_marking=True)
result = dom_analyzer.run()

# Accès au CSSMarker
if dom_analyzer.css_marker:
    dom_analyzer.css_marker.toggle_production_mode(hide=True)
```

### ScreenReader

```python
# Activation du marquage
screen_reader = ScreenReader(driver, logger, enable_css_marking=True)
screen_reader.run()
```

## 🎯 Mode production

Le système inclut un mode production pour masquer les marquages :

```python
# Masquer les marquages (production)
css_marker.toggle_production_mode(hide=True)

# Afficher les marquages (développement)
css_marker.toggle_production_mode(hide=False)
```

## 📊 Gestion des marquages

### Informations sur les éléments marqués

```python
marked_info = css_marker.get_marked_elements_info()
print(f"Éléments marqués : {marked_info['total_marked']}")
print(f"CSS injecté : {marked_info['css_injected']}")
```

### Nettoyage

```python
# Supprimer le marquage d'un élément
css_marker.unmark_element(element)

# Supprimer tous les marquages
css_marker.clear_all_markings()
```

## 🧪 Tests et validation

### Tests unitaires

```bash
# Lancer tous les tests
python test_css_marker.py

# Tests spécifiques
python -m pytest test_css_marker.py::test_basic_marking
```

### Démonstration interactive

```bash
# Démonstration simple
python demo_css_marker.py

# Démonstration avec page réelle
python demo_css_marker.py --url https://example.com
```

## 📚 Documentation complète

- **Guide d'utilisation** : `docs/CSS_MARKER_GUIDE.md`
- **Tests unitaires** : `test_css_marker.py`
- **Démonstration** : `demo_css_marker.py`
- **Scripts de lancement** : `launch_css_marker_demo.sh` / `launch_css_marker_demo.ps1`

## 🎯 Avantages pour les automaticiens

### 🔍 Identification visuelle
- **Éléments conformes** : Facilement identifiables par la bordure verte
- **Problèmes d'accessibilité** : Mis en évidence par la bordure rouge
- **Types d'éléments** : Styles spécifiques pour chaque catégorie

### 💡 Informations contextuelles
- **Tooltips détaillés** : Informations complètes au survol
- **Badges informatifs** : Statut de conformité visible
- **Problèmes listés** : Détail des non-conformités

### ⚡ Performance optimisée
- **Marquage en lot** : Traitement groupé pour de meilleures performances
- **Mode production** : Masquage des marquages en production
- **Nettoyage automatique** : Gestion de la mémoire

### 🔧 Intégration transparente
- **Modules existants** : Intégration sans modification majeure
- **Configuration flexible** : Activation/désactivation facile
- **Styles personnalisables** : Adaptation aux besoins spécifiques

## 🚀 Exemples d'utilisation

### Exemple 1 : Analyse simple

```python
from modules.dom_analyzer import DOMAnalyzer

# Analyse avec marquage automatique
dom_analyzer = DOMAnalyzer(driver, logger, enable_css_marking=True)
result = dom_analyzer.run()

# Les éléments sont automatiquement marqués
print(f"Éléments analysés : {result['summary']['analyzed_elements']}")
```

### Exemple 2 : Marquage personnalisé

```python
from modules.css_marker import CSSMarker

css_marker = CSSMarker(driver, logger)

# Marquer des éléments spécifiques
for element in elements:
    issues = detect_accessibility_issues(element)
    compliant = len(issues) == 0
    
    css_marker.mark_element(
        element=element,
        element_type="custom",
        issues=issues,
        compliant=compliant,
        info=f"Élément {element.tag_name} - {len(issues)} problème(s)"
    )
```

### Exemple 3 : Mode production

```python
# Pendant le développement
css_marker.toggle_production_mode(hide=False)

# En production
css_marker.toggle_production_mode(hide=True)
```

## 🎨 Captures d'écran

Le système de marquage CSS ajoute des éléments visuels clairs :

- **Bordure verte** : Éléments conformes
- **Bordure rouge** : Éléments avec problèmes
- **Badges colorés** : Statut de conformité
- **Tooltips** : Informations détaillées au survol

## 🤝 Contribution

Pour contribuer au système de marquage CSS :

1. **Fork** le projet
2. **Créer** une branche feature
3. **Implémenter** les modifications
4. **Tester** avec les scripts fournis
5. **Soumettre** une pull request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

Pour obtenir de l'aide :

- **Documentation** : `docs/CSS_MARKER_GUIDE.md`
- **Issues** : Créer une issue sur GitHub
- **Tests** : Utiliser `test_css_marker.py` pour diagnostiquer

---

**🎯 Le système de marquage CSS transforme l'analyse d'accessibilité en une expérience visuelle intuitive pour les automaticiens !**
