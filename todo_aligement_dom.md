# Todo — Alignement DOM (basculer vers l’analyse groupée)

Objectif : enrichir le passage **`DOM_COMPLET`** (`EnhancedScreenReader`, batch JS) pour qu’il porte les mêmes données et contrôles que **`DOMAnalyzer`**, puis **désactiver ou retirer** la phase 4 redondante sans perte de rapports.

**État (implémenté)** : détail dans **`ALIGNEMENT_DOM.md`**, code dans **`modules/dom_accessibility_from_batch.py`** + intégration **`modules/enhanced_screen_reader.py`** / **`core/ordered_crawler.py`**.

---

## Phase 0 — Cadrage

- [x] Lister les **consommateurs** actuels de `rapport_analyse_dom.csv` / `rapport_analyse_dom.json` (scripts, docs, habitudes métier).
- [x] Décider du **comportement par défaut** : un seul jeu d’artefacts (`accessibility_analysis` enrichi vs conservation des noms de fichiers `rapport_analyse_dom.*`).
- [x] Documenter les **écarts acceptés** vs Selenium (`is_displayed`, coordonnées) si on ne reproduit pas à l’identique.

---

## Phase 1 — Enrichir le batch JS (`enhanced_screen_reader.py`)

- [x] Ajouter **`type`**, **`value`**, **`placeholder`**, **`name`** pour champs de formulaire.
- [x] Exposer **`innerText`** (et garder ou renommer `textContent` pour ne pas casser l’existant).
- [x] Exporter le bloc **`computed_style`** aligné sur le `DOMAnalyzer` : `display`, `visibility`, `opacity`, `position`, `z-index`, `background-color`, `color`, `font-size`, `font-weight` (pour nœuds visibles selon la règle choisie).
- [x] Exposer **`rect`** complet (`x`, `y`, `width`, `height`) + option **coordonnées page** (`+ scrollX/Y`) si alignement avec `location`/`size` Selenium.
- [x] Aligner **`isFocusable`** avec la règle du `DOMAnalyzer` (balises natives + `tabindex` présent et ≠ `-1`).
- [x] Enrichir **`media_path` / `media_type`** : `video` + `source`, `iframe`/`frame`, `object`/`embed` + `data`, cohérent avec `dom_analyzer.py`.
- [x] Calculer **`hasLabelFor`** : présence de `label[for="id"]` lorsque `id` est défini (échappement sûr).
- [x] Implémenter **`accessible_name`** (objet `name` / `source` / `priority`) : résolution `aria-labelledby`, `aria-label`, texte, `alt`, première `img` dans `<a>`.
- [ ] Optionnel : même **algorithme XPath** que `_get_element_xpath` du `DOMAnalyzer` (dans la boucle du batch pour limiter les allers-retours).

---

## Phase 2 — Pipeline Python

- [x] Étendre le dict `info` / les colonnes CSV du lecteur d’écran pour les **nouveaux champs** (ou documenter un mapping explicite).
- [x] Extraire la logique de **`_check_accessibility_issues`** dans une couche **sans `WebElement`** (entrée : dict enrichi du batch).
- [x] Garantir un **sélecteur stable** par nœud (équivalent `_get_element_selector`) pour corréler les `issues` aux lignes CSV.
- [x] Générer **`rapport_analyse_dom.csv`** et **`rapport_analyse_dom.json`** à partir des données du batch (même schéma ou schéma versionné + note de migration).

---

## Phase 3 — Tests & non-régression

- [ ] Jeux de pages de **référence** (formulaires, `aria-labelledby`, liens + logo `img`, `video`/`source`, iframes).
- [ ] Comparaison **avant/après** : nombre et types d’issues, présence des colonnes critiques.
- [x] Tests unitaires sur le **calcul du nom accessible** et **`hasLabelFor`** (extraits JS ou snapshots JSON).

---

## Phase 4 — Bascule orchestration

- [x] Retirer **`DOMAnalyzer`** de la phase 4 du `OrderedAccessibilityCrawler` **ou** le faire **déléguer** au nouveau chemin (feature flag `USE_LEGACY_DOM_ANALYZER`).
- [x] Mettre à jour **`main.py` / `main_ordered.py`** / **`README.md`** : modules, options, fichiers produits.
- [ ] Supprimer ou archiver le code mort (`dom_analyzer.py` ou réduire à export des helpers partagés).

---

## Phase 5 — Perf & finitions

- [x] Supprimer **`time.sleep(0.5)`** entre lots côté ancien flux (si encore présent sur un chemin legacy).
- [ ] Vérifier la **taille mémoire** des réponses `execute_script` sur très gros DOM (pagination des lots si besoin).
- [ ] Journalisation : une seule barre de progression / section « DOM » pour éviter la confusion utilisateur.

---

## Références code

| Élément | Fichier principal |
|--------|-------------------|
| Batch actuel | `modules/enhanced_screen_reader.py` — `_analyze_elements_integrated` |
| Cible fonctionnelle | `modules/dom_analyzer.py` — `_analyze_element`, `_check_accessibility_issues`, rapports CSV/JSON |
| Orchestration | `core/ordered_crawler.py` — phase 4 |

---

*Fichier : `todo_aligement_dom.md` — même contenu que la checklist d’alignement DOM.*
