# Plan d'actions – RGAA Web Checker

> Objectif :  
> 1️⃣ garantir la prise en compte de **toutes les règles RGAA 4.1** dans l'analyse,  
> 2️⃣ consolider l'architecture et le reporting pour un outil cohérent, extensible et testable.

---

## 0. Alignement complet sur le RGAA 4.1
- [ ] **0.1 Récupérer la source officielle**  
      • Télécharger la dernière publication (PDF + annexe technique) depuis https://accessibilite.numerique.gouv.fr.  
- [ ] **0.2 Extraire la liste des 106 critères et 13 thématiques**  
      • Script d'extraction vers `docs/rgaa_4_1_criteria.yaml` (id, thématique, critère, test, niveau).  
- [ ] **0.3 Définir un format d'implémentation**  
      • Décider d'un modèle *rule engine* (JSON/YAML + fonctions Python).  
      • Chaque critère reçoit : id, description, méthode de test, module responsable, statut (pass/fail/NA).  
- [ ] **0.4 Mapper critères ↔ modules**  
      • Table de correspondance dans `core/rgaa_mapping.py`.  
      • Exemple : contraste → module `contrast`, intitulé 3.1 ; navigation clavier → modules `tab` et `screen`, etc.  
- [ ] **0.5 Étendre / créer les modules pour couvrir 100 % des critères**  
      • Ajouter des sous-tests internes si un module couvre plusieurs critères.  
      • Ajouter les modules manquants (formulaires, multimédia, structuration…).  
- [ ] **0.6 Collecte des résultats par critère**  
      • Mettre à jour chaque module pour écrire dans `Scenario.violations` la liste `(critère_id, élément, description)`.  
- [ ] **0.7 Reporting détaillé RGAA**  
      • `report_generator.py` : section par thématique, tableau OK/KO/NA pour les 106 critères.  
      • Statistiques : % succès global + par thématique.  
- [ ] **0.8 Tests automatisés RGAA**  
      • Générer des pages HTML de test positives/négatives par critère (`tests/fixtures/`).  
      • Vérifier qu'un critère négatif ressort bien en échec.  
- [ ] **0.9 Documentation**  
      • Fiche « Couverture » dans `docs/`, statut d'implémentation par critère.  
      • Procédure de mise à jour vers RGAA 4.2 (lorsqu'elle sera publiée).

---

## 1. Normalisation des noms de modules
- [ ] Définir une nomenclature unique : `contrast`, `dom`, `daltonism`, `tab`, `screen`, `image`.
- [ ] Mettre à jour :
  - `core/config.py` (méthode `get_module_names()` + `set_modules()`),  
  - l'option CLI `--modules` dans `main.py`,  
  - `_load_modules()` de `core/crawler.py`.

## 2. Refactorisation de l'orchestration
- [ ] Utiliser **AccessibilityCrawler** comme orchestrateur unique :
  - Déplacer l'initialisation des modules hors de `main.py` vers `AccessibilityCrawler`.  
  - Adapter `main.py` : créer `Config` → driver Selenium → `AccessibilityCrawler` → `crawl()` → `generate_report()`.  
- [ ] Retirer les appels directs aux modules dans `main.py`.

## 3. Chaîne de résultat (Scenario & Reporting)
- [ ] Créer une classe `Scenario` (`core/scenario.py`) stockant : `base_url`, `start_time`, `pages_visited`, `violations`, `images_info`, `tab_order`, etc.  
- [ ] Passer `Scenario` à chaque module (`run(self, scenario)`).  
- [ ] Adapter chaque module pour renseigner ses résultats dans `scenario`.  
- [ ] Modifier `report_generator.py` pour consommer `Scenario` et générer Markdown + PDF.  
- [ ] Limiter `utils/log_utils.py` au seul logging.

## 4. Uniformisation des modules
- [ ] Vérifier cohérence nom de classe / fichier / flag.  
- [ ] Chaque module doit :
  - accepter `driver`, `logger`, `scenario`,  
  - exposer `run()`,  
  - renvoyer un statut clair (succès, nombre d'erreurs…).

## 5. Couverture de tests
- [ ] Étendre `test_crawler.py` : tests unitaires pour tous les modules + tests du nouvel orchestrateur.  
- [ ] Ajouter un test d'intégration headless : exécuter le crawler sur une page de démo, vérifier création du rapport et % de conformité RGAA.

## 6. Automatisation & portabilité
- [ ] Script PowerShell ou `.bat` équivalent à `install.sh`.  
- [ ] Cibles VS Code / Makefile : `test`, `lint`, `format`.  
- [ ] Workflow GitHub Actions : installation, lint (`ruff`/`flake8`), tests.

## 7. Documentation
- [ ] Mettre à jour le README après refactorisation.  
- [ ] Ajouter un diagramme d'architecture (`docs/`).  
- [ ] Documenter la procédure de mise à jour du référentiel RGAA.

## 8. Qualité de code
- [ ] Mettre en place `black` + `isort` (ou `ruff --fix`).  
- [ ] Activer un linter (`ruff`/`flake8`) dans la CI. 