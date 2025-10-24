# Guide d'utilisation du système de marquage CSS

## Vue d'ensemble

Le système de marquage CSS permet d'ajouter des balises visuelles aux éléments analysés par le RGAA Web Checker, facilitant ainsi l'identification et le débogage des problèmes d'accessibilité pour les automaticiens.

## Fonctionnalités principales

### 🎨 Marquage visuel
- **Éléments conformes** :** Bordure verte avec badge ✅
- **Éléments non conformes** :** Bordure rouge avec badge ⚠️
- **Éléments en cours d'analyse** :** Bordure jaune avec badge 🔍

### 📋 Types d'éléments supportés
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
- Problèmes détectés
- Nom accessible
- Rôle ARIA

## Utilisation

### 1. Activation du marquage CSS

```python
from modules.dom_analyzer import DOMAnalyzer
from modules.css_marker import CSSMarker

# Avec DOMAnalyzer (recommandé)
dom_analyzer = DOMAnalyzer(driver, logger, enable_css_marking=True)
result = dom_analyzer.run()

# Utilisation directe du CSSMarker
css_marker = CSSMarker(driver, logger)
```

### 2. Marquage d'éléments individuels

```python
# Marquer un élément conforme
css_marker.mark_element(
    element=element,
    element_type="image",
    issues=[],
    compliant=True,
    info="Image avec attribut alt conforme"
)

# Marquer un élément non conforme
css_marker.mark_element(
    element=element,
    element_type="link",
    issues=["Lien sans texte visible"],
    compliant=False,
    info="Lien sans texte visible - non conforme"
)
```

### 3. Marquage en lot (optimisé)

```python
# Préparer les données
elements_data = []
for element in elements:
    elements_data.append({
        'element': element,
        'type': 'heading',
        'issues': [],
        'compliant': True,
        'info': f"Titre {element.tag_name} - conforme"
    })

# Marquage en lot
css_marker.mark_elements_batch(elements_data)
```

### 4. Gestion des marquages

```python
# Supprimer le marquage d'un élément
css_marker.unmark_element(element)

# Supprimer tous les marquages
css_marker.clear_all_markings()

# Activer/désactiver le mode production
css_marker.toggle_production_mode(hide=True)  # Masquer
css_marker.toggle_production_mode(hide=False) # Afficher
```

### 5. Informations sur les éléments marqués

```python
# Récupérer les informations
marked_info = css_marker.get_marked_elements_info()
print(f"Éléments marqués : {marked_info['total_marked']}")
print(f"CSS injecté : {marked_info['css_injected']}")
```

## Styles CSS personnalisés

### Classes CSS disponibles

```css
/* Éléments analysés */
.rgaa-analyzed { /* Style de base */ }
.rgaa-issue { /* Éléments avec problèmes */ }
.rgaa-compliant { /* Éléments conformes */ }
.rgaa-analyzing { /* Éléments en cours d'analyse */ }

/* Types d'éléments */
.rgaa-heading { /* Titres */ }
.rgaa-image { /* Images */ }
.rgaa-link { /* Liens */ }
.rgaa-button { /* Boutons */ }
.rgaa-form { /* Formulaires */ }
.rgaa-landmark { /* Landmarks */ }
.rgaa-aria { /* Éléments ARIA */ }

/* Badges */
.rgaa-badge { /* Badge général */ }
.rgaa-badge-issue { /* Badge pour problèmes */ }
.rgaa-badge-compliant { /* Badge pour conformes */ }
.rgaa-badge-analyzing { /* Badge pour analyse */ }

/* Tooltips */
.rgaa-tooltip { /* Tooltip d'information */ }
```

### Personnalisation des styles

```python
# Injecter des styles personnalisés
custom_css = """
<style>
.rgaa-analyzed {
    outline: 3px solid #ff6b6b !important;
    outline-offset: 3px !important;
}

.rgaa-compliant {
    background-color: rgba(46, 204, 113, 0.2) !important;
}
</style>
"""

driver.execute_script(f"""
    var style = document.createElement('style');
    style.innerHTML = `{custom_css}`;
    document.head.appendChild(style);
""")
```

## Intégration avec les modules d'analyse

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

## Exemples d'utilisation

### Exemple 1 : Analyse simple avec marquage

```python
from modules.dom_analyzer import DOMAnalyzer
import logging

# Configuration
logger = logging.getLogger(__name__)

# Analyse avec marquage CSS
dom_analyzer = DOMAnalyzer(driver, logger, enable_css_marking=True)
result = dom_analyzer.run()

# Les éléments sont automatiquement marqués
print(f"Éléments analysés : {result['summary']['analyzed_elements']}")
print(f"Problèmes détectés : {result['summary']['issues_found']}")
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

## Bonnes pratiques

### 1. Performance
- Utilisez le marquage en lot pour de nombreux éléments
- Désactivez le marquage en production si nécessaire
- Nettoyez les marquages après analyse

### 2. Accessibilité
- Les marquages n'interfèrent pas avec l'accessibilité
- Utilisez des couleurs contrastées
- Fournissez des informations claires dans les tooltips

### 3. Maintenance
- Documentez les styles personnalisés
- Testez sur différents navigateurs
- Surveillez les performances

## Dépannage

### Problèmes courants

1. **Marquages non visibles**
   ```python
   # Vérifier que le CSS est injecté
   marked_info = css_marker.get_marked_elements_info()
   print(f"CSS injecté : {marked_info['css_injected']}")
   ```

2. **Éléments non marqués**
   ```python
   # Vérifier que l'élément est valide
   try:
       element.is_displayed()
   except StaleElementReferenceException:
       print("Élément devenu obsolète")
   ```

3. **Styles CSS conflictuels**
   ```python
   # Utiliser !important dans les styles
   .rgaa-analyzed {
       outline: 2px solid #007cba !important;
   }
   ```

### Logs et débogage

```python
import logging

# Activer les logs détaillés
logging.getLogger('modules.css_marker').setLevel(logging.DEBUG)

# Vérifier les éléments marqués
marked_info = css_marker.get_marked_elements_info()
for element_info in marked_info['elements']:
    print(f"Élément : {element_info['element_id']}")
    print(f"Type : {element_info['element_type']}")
    print(f"Conforme : {element_info['compliant']}")
```

## API de référence

### CSSMarker

#### `__init__(driver, logger)`
Initialise le marqueur CSS.

#### `mark_element(element, element_type, issues, compliant, info)`
Marque un élément avec les classes CSS appropriées.

**Paramètres :**
- `element` : Élément Selenium à marquer
- `element_type` : Type d'élément ("analyzed", "heading", "image", etc.)
- `issues` : Liste des problèmes détectés
- `compliant` : Booléen indiquant la conformité
- `info` : Informations pour le tooltip

#### `mark_elements_batch(elements_data)`
Marque plusieurs éléments en lot.

#### `unmark_element(element)`
Supprime le marquage d'un élément.

#### `clear_all_markings()`
Supprime tous les marquages de la page.

#### `toggle_production_mode(hide)`
Active/désactive le mode production.

#### `get_marked_elements_info()`
Retourne les informations sur les éléments marqués.

## Conclusion

Le système de marquage CSS facilite grandement l'identification et le débogage des problèmes d'accessibilité. Il s'intègre parfaitement avec les modules d'analyse existants et offre une flexibilité maximale pour la personnalisation des styles.

Pour plus d'informations, consultez les tests dans `test_css_marker.py` et les exemples d'intégration dans les modules d'analyse.
