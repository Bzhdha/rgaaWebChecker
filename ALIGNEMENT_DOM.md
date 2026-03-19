# Alignement DOM (batch vs DOMAnalyzer)

## Phase 0 — Cadrage

### Consommateurs connus de `rapport_analyse_dom.*`

| Usage | Emplacement |
|--------|-------------|
| Exécution directe du module | `modules/dom_analyzer.py` (legacy) |
| GUI — chargement / rapports | `gui_app.py` |
| Lanceurs / packaging | `launch_gui.py`, `launch_gui.ps1`, `launch_gui.sh` |
| Chaîne ordonnée | `main_ordered.py` + `core/ordered_crawler.py` |
| Autre entrée | `main_enhanced.py`, `core/crawler.py` (flux classique `ScreenReader`, non batch) |

### Comportement par défaut (`main_ordered` + modules `screen` + `dom`)

- Les fichiers **`rapport_analyse_dom.csv`** et **`rapport_analyse_dom.json`** sont produits par le **batch JS** dans `EnhancedScreenReader` (données enrichies alignées sur l’ancien `DOMAnalyzer`).
- **`reports/accessibility_analysis.csv`** reste le export détaillé lecteur d’écran, avec **colonnes supplémentaires** en fin de ligne (InnerText, champs formulaire, nom accessible, rect page, résumé de style).
- La **phase 4 `DOMAnalyzer`** Selenium n’est **pas** exécutée dans ce mode (pas de double parcours DOM).

### Forcer l’ancien analyseur

Variable d’environnement : **`USE_LEGACY_DOM_ANALYZER=1`** (ou `true` / `yes` / `on`).  
Réactive la phase 4 `DOMAnalyzer` et **désactive** la génération batch des `rapport_analyse_dom.*` depuis `EnhancedScreenReader`.

### Cas particuliers

- **`HierarchicalScreenReader`** : pas d’export batch DOM pour l’instant → la phase 4 **`DOMAnalyzer`** reste utilisée si le module `dom` est activé.
- **`core/crawler.py` + main classique** : utilise `ScreenReader` (non enrichi batch) → **`DOMAnalyzer`** inchangé si le module `dom` est activé.

### Écarts acceptés vs Selenium (`DOMAnalyzer` legacy)

| Sujet | Batch JS |
|--------|-----------|
| Visibilité / `is_displayed` | Heuristique `display`, `visibility`, taille du `getBoundingClientRect()`, `opacity` — pas l’algorithme complet `isDisplayed()` de Selenium. |
| Position | `rectPage` = viewport + `scrollX` / `scrollY` (proche document), pas `element.location` Selenium. |
| Stale elements | Un seul snapshot par lot ; pas de re-vérification entre deux appels (comme tout parcours groupé). |

### Schéma JSON

- `rapport_analyse_dom.json` inclut **`schema_version`: 2** et les champs additionnels : `inner_text`, `name`, `has_label_for` (et clés snake_case cohérentes avec l’export élément).

### Fichiers de code

| Rôle | Fichier |
|------|---------|
| Script batch + issues + écriture rapports | `modules/dom_accessibility_from_batch.py` |
| Intégration CSV + déclenchement rapports | `modules/enhanced_screen_reader.py` |
| Orchestration | `core/ordered_crawler.py`, `core/config.py` |
| Legacy | `modules/dom_analyzer.py` |
