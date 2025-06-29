# Référence Rapide - Règles de Contexte

## 🎯 Priorité : Ubuntu/Linux > Windows

### Scripts
```bash
# PRIORITÉ : Bash (.sh)
chmod +x script.sh
./script.sh

# SECONDAIRE : PowerShell (.ps1)
.\script.ps1
```

### Installation
```bash
# PRIORITÉ : Ubuntu/Linux
sudo apt install python3-tk
pip install package==version
./install_ubuntu.sh

# SECONDAIRE : Windows
pip install package==version
.\install_with_conda.ps1
```

### Tests
```bash
# PRIORITÉ : Ubuntu/Linux
python3 test_script.py
./test_script.sh

# SECONDAIRE : Windows
python test_script.py
```

### Navigateurs
1. **Chromium** (Ubuntu/Linux - PRIORITÉ)
2. **Chrome** (Windows - SECONDAIRE)
3. **Firefox** (Alternative)

### Documentation
- **Section Ubuntu/Linux** : Détaillée, en premier
- **Section Windows** : Concise, en second
- **Exemples** : Commandes bash en priorité

---

**Règles complètes** : Voir `CONTEXT_RULES.md` 