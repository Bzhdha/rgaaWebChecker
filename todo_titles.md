## TODO - Module `titles` (RGAA 9.1.1 / 9.1.2 / 9.1.3)

### Objectif
Ajouter un module Python activable via `--modules titles` qui produit des notes `note_9_1_1`, `note_9_1_2`, `note_9_1_3` (1/0) et des preuves exportables pour revue humaine.

### Rappels RGAA (contraintes à respecter)
1. **9.1.1** : calcul sur headings DOM **visiblement non masqués** uniquement.  
   - Exclure les headings masquées **et restant masquées** (sr-only/visually-hidden + invisibilité CSS + aria-hidden="true").  
   - Malgré l’exclusion pour le score : produire un **rapport d’incohérences hiérarchiques** basé sur la hiérarchie des titres **éligibles**.
2. **9.1.2** : pour chaque titre, la section va **du titre jusqu’au suivant dont le niveau est `<=`** (ou fin doc).  
   - IA vision sur screenshots de section : note `ai_ok=1/0`.
3. **9.1.3 (RG11)** : mismatch = “titre-like détecté par l’IA mais absent du DOM heading au sens RGAA”.  
   - Comparaison **strict texte après normalisation NFKC + lower + strip + espaces normalisés**.
   - Export = **toutes** les détections IA non-matc hées pour validation humaine.

---

### Phase 0 - Pré-checks projet (1h)
1. Vérifier dans `core/crawler.py` que le module `screen_reader` se charge bien (il y a un branchement suspect : dépend d’une condition sur un nom incorrect).  
   - Action : aligner le chargement du “screen” pour que `screen_reader` tourne quand `--modules screen` est activé.
2. Définir le nom CLI attendu pour activer le module.
   - Attendu : `--modules titles`

---

### Phase 1 - Intégration framework modules (0.5h)
1. `core/config.py` :
   - Ajouter un flag `MODULE_TITLES` (puissance de 2).
   - Étendre `set_modules()` pour inclure `titles` dans `enabled_modules`.
   - Étendre `get_module_names()` pour exposer `titles`.
2. `main.py` :
   - Ajouter `titles` dans la liste `--modules ... choices`.
3. `core/crawler.py` :
   - Importer `TitlesAnalyzer` et ajouter un branchement `if 'titles' in config.get_enabled_modules(): ...`

---

### Phase 2 - Module `modules/titles_analyzer.py` (3-6h)
1. Créer le fichier `modules/titles_analyzer.py`
2. Structure minimale :
   - Classe `TitlesAnalyzer(driver, logger)`
   - Méthode `run()` qui :
     - collecte DOM headings
     - calcule 9.1.1, prépare preuves
     - lance 9.1.2 (captures + IA)
     - lance 9.1.3 (captures scroll + IA + matching strict)
     - écrit CSV/MD
3. Normalisation texte (à réutiliser partout) :
   - `normalize_heading_text(s)` :
     - NFKC unicode
     - `lower()`
     - suppression caractères invisibles courants (`\u200b`, `\uFEFF`)
     - `strip()`
     - collapse regex `\s+ -> ' '`

---

### Phase 3 - Extraction DOM headings RGAA (1-2h)
1. Récupérer headings DOM au sens RGAA :
   - HTML native `h1..h6`
   - et `*[role="heading"][aria-level]`
2. Construire un tableau `dom_headings_all[]` avec :
   - `text_raw`, `text_normalized`
   - `dom_level` (hxx => 1..6 ou aria-level => int)
   - `xpath` ou `css_selector`
   - `is_masked` (pour 9.1.1)
3. Définir `is_masked_heading(el)` qui exclut les masqués pour 9.1.1 :
   - `aria-hidden="true"`
   - `display:none` / `visibility:hidden`
   - dimensions nulles / hors rendu (selon les infos déjà utilisées côté screen)

---

### Phase 4 - Critère 9.1.1 (1-2h)
1. Déterminer `eligible_headings_9_1_1 = dom_headings_all où is_masked == False`
2. Calculer l’ordre hiérarchique :
   - Construire la suite des niveaux (dans l’ordre DOM)
   - Appliquer une règle de cohérence (“meaningful sequence”) :
     - montée de niveau autorisée seulement si pas de saut en avant (par ex. `next_level > prev_level` => `next_level - prev_level <= 1`)
     - toute violation => incohérence
3. Sorties :
   - `note_9_1_1 = 1/0`
   - `reports/titles_9_1_1_incoherences.csv` (toutes les incohérences)
   - Bloc dans `reports/titles_report.md`

---

### Phase 5 - Critère 9.1.2 (2-4h)
1. Définir la section pour un titre :
   - du titre courant jusqu’au prochain titre DOM dont `level <= current_level` (ou fin document)
2. Capturer preuves :
   - 1 screenshot “début de section” (centrer le titre/haut section)
   - optionnel 1 screenshot “milieu/fin” si faisable
3. Prompt IA 9.1.2 (vision) :
   - Entrées : texte du titre + screenshots de la section + niveaux
   - Sortie attendue : JSON strict `{ "ok": 1/0, "score": 0..1, "comment": "..." }`
4. Note globale :
   - `note_9_1_2 = 1` si tous ok, sinon `0`
5. Sorties :
   - `reports/titles_9_1_2_results.csv`
   - Bloc dans `reports/titles_report.md`

---

### Phase 6 - Critère 9.1.3 (2-5h)
1. Découpage page pour capture scroll :
   - segmenter sur `viewport_height` (ou multiple : ex 0.75) pour couvrir toute la page
   - sauver images : `reports/titles_9_1_3_segments/segment_XXX.png`
2. IA 9.1.3 :
   - Demander à l’IA une liste de “title-like” détectés sur chaque segment
   - Sortie attendue JSON strict :
     - `[{ "text_detected": "...", "ai_confidence": 0..1, "level_estimated": 1..6 (optionnel) }]`
3. DOM headings pour 9.1.3 :
   - utiliser `dom_headings_all` **sans filtrer** masqués (mode 2 confirmé)
4. Matching strict :
   - mismatch si aucun heading DOM n’a `normalize(ai_text) == normalize(dom_text)`
5. Export :
   - `reports/titles_9_1_3_ai_mismatches.csv` (toutes les lignes mismatch)
   - `note_9_1_3 = 1` si aucun mismatch, sinon `0`
   - Bloc dans `reports/titles_report.md`

---

### Phase 7 - Rapport global (0.5-1h)
1. Créer `reports/titles_report.md`
2. Y inclure sections :
   - RGAA 9.1.1 (note + incohérences)
   - RGAA 9.1.2 (note + top problèmes si utile)
   - RGAA 9.1.3 (note + mismatches)
3. Intégrer ensuite (si souhaité) dans `reports/accessibility_report.md` ou via `report_generator.py`.

---

### Phase 8 - Tests & validations (1-2h)
1. Ajouter tests unitaires sans Selenium :
   - test `normalize_heading_text()`
   - test cohérence 9.1.1 sur suites de niveaux synthétiques
   - test matching strict 9.1.3 sur couples (ai_text, dom_text)
2. Exécuter une passe sur une page réelle :
   - commande : `python main.py <url> --modules screen titles ...`
   - vérifier que les 3 CSV + MD existent
3. Vérifier que 9.1.1 exclut bien les titres masqués du score
4. Vérifier que 9.1.3 exporte bien toutes les detections IA mismatch (zéro filtrage “humain”).

---

### Critères de “Definition of Done”
- Le module `titles` est activable via CLI
- Les notes et CSV attendus sont générés pour une page
- La normalisation est identique pour 9.1.3
- 9.1.1 exclut les masqués du calcul
- 9.1.2 applique bien la frontière de section “jusqu’au suivant level <=”

