# Règles de Contexte - RGAA Web Checker

## Automatisation d'altération du code
- **Autorisation pour cursor** : autorisation accordée sauf contre ordre spécifique

## 🎯 Priorité de Développement
- **Développement des modules d'analyse** : prioriser la version ligne de commande
- **Intégration des modules d'analyse dans l'interface** : doit se faire sans rendre dysfonctionnel l'exécution en ligne de commande de ces modules

### Environnement Principal : Ubuntu/Linux
- **OS cible principal** : Ubuntu/Linux (WSL inclus)
- **Scripts prioritaires** : Bash (.sh)
- **Commandes** : Linux/Unix
- **Navigateur** : Chromium (plus léger) puis Chrome
- **Gestion des erreurs** : Solutions Linux d'abord

### Environnement Secondaire : Windows
- **OS cible secondaire** : Windows
- **Scripts secondaires** : PowerShell (.ps1)
- **Commandes** : Windows/PowerShell
- **Navigateur** : Chrome
- **Gestion des erreurs** : Solutions Windows en second

## 🛠️ Règles de Développement
-- **Mise en place de tests unitaires** : Toute nouvelle fonction doit disposer de testss unitaires

## Sécutité
-- **Librairie maintenue** : les librairies utilisées doivent privilégier les librairies maintenues

### 1. Scripts et Installation
```bash
# PRIORITÉ : Scripts bash pour Ubuntu/Linux
chmod +x install_ubuntu.sh
./install_ubuntu.sh
./install_chromium.sh

# SECONDAIRE : Scripts PowerShell pour Windows
.\install_with_conda.ps1
.\activate_venv.ps1
```

### 2. Dépendances et Packages
```bash
# PRIORITÉ : Packages Linux
sudo apt install python3-tk python3-venv
pip install tksheet==6.1.12

# SECONDAIRE : Packages Windows
pip install tksheet==6.1.12
```

### 3. Tests et Validation
```bash
# PRIORITÉ : Tests Linux
python test_tksheet.py
python test_chromium_wsl.py
python test_crawler.py

# SECONDAIRE : Tests Windows
python test_tksheet.py
```

### 4. Gestion des Erreurs
- **Première approche** : Solutions Ubuntu/Linux
- **Deuxième approche** : Solutions Windows
- **Logs** : Fichiers de logs Linux en priorité
- **Diagnostic** : Scripts bash de diagnostic

## 📋 Règles de Documentation

### Structure des README
1. **Section Ubuntu/Linux** : Détaillée, en premier
2. **Section Windows** : Plus concise, en second
3. **Exemples** : Commandes bash en priorité
4. **Dépannage** : Solutions Linux d'abord

### Exemples de Code
```bash
# PRIORITÉ : Exemples bash
chmod +x script.sh
./script.sh

# SECONDAIRE : Exemples PowerShell
.\script.ps1
```

## 🔧 Règles Techniques

### Navigateurs
1. **Chromium** : Premier choix (plus léger, open source)
2. **Chrome** : Deuxième choix
3. **Firefox** : Alternative si problèmes avec Chrome/Chromium

### Environnements Virtuels
```bash
# PRIORITÉ : venv Linux
python3 -m venv venv
source venv/bin/activate

# SECONDAIRE : venv Windows
python -m venv venv
.\venv\Scripts\activate
```

### Gestion des Fichiers
- **Permissions** : `chmod +x` pour les scripts bash
- **Chemins** : Chemins Unix/Linux en priorité
- **Encodage** : UTF-8 par défaut

## 🚀 Règles de Déploiement

### Installation
1. **Scripts bash** : Création et test en premier
2. **Scripts PowerShell** : Adaptation en second
3. **Documentation** : Instructions Linux détaillées
4. **Tests** : Validation Ubuntu/Linux prioritaire

### Maintenance
- **Logs** : Fichiers de logs Linux
- **Diagnostic** : Scripts bash de diagnostic
- **Mise à jour** : Packages Linux en premier

## 📝 Règles de Communication

### Réponses aux Demandes
1. **Solutions Linux** : Détaillées et prioritaires
2. **Solutions Windows** : Mentionnées mais secondaires
3. **Exemples** : Commandes bash en premier
4. **Dépannage** : Approche Linux d'abord

### Documentation des Changements
- **Impact Linux** : Détail complet
- **Impact Windows** : Résumé
- **Tests** : Validation Linux prioritaire

## 🎯 Application de ces Règles

Ces règles s'appliquent à :
- ✅ Développement de nouvelles fonctionnalités
- ✅ Correction de bugs
- ✅ Amélioration de l'interface
- ✅ Ajout de dépendances
- ✅ Création de scripts
- ✅ Documentation
- ✅ Tests et validation
- ✅ Dépannage et support

## 📋 Checklist de Validation

Avant de considérer un travail terminé :
- [ ] Testé sur Ubuntu/Linux
- [ ] Scripts bash créés et testés
- [ ] Documentation Linux détaillée
- [ ] Solutions de dépannage Linux documentées
- [ ] Compatibilité Windows vérifiée (secondaire)
- [ ] README mis à jour avec priorité Linux

---

**Note** : Ces règles garantissent que l'application est optimisée pour l'environnement de travail principal (Ubuntu/Linux) tout en maintenant la compatibilité Windows. 