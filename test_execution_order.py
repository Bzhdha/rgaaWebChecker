#!/usr/bin/env python3
"""
Script de test pour vérifier l'ordre d'exécution des modules
"""

from core.config import Config
from core.execution_config import ExecutionConfig

def test_execution_order():
    """Teste l'ordre d'exécution avec les modules tab et screen"""
    
    # Créer une configuration avec les modules tab et screen
    config = Config()
    config.set_modules(24)  # 8 (tab) + 16 (screen) = 24
    
    # Récupérer les modules activés
    enabled_modules = config.get_enabled_modules()
    print(f"Modules activés: {enabled_modules}")
    
    # Valider le plan d'exécution
    execution_plan = ExecutionConfig.get_execution_plan(enabled_modules)
    
    if not execution_plan['valid']:
        print(f"❌ Erreur: {execution_plan['error']}")
        return False
    
    print("✅ Plan d'exécution validé:")
    print(f"   - Phases d'exécution: {execution_plan['total_phases']}")
    print(f"   - Temps estimé: {execution_plan['estimated_time']} secondes")
    
    print("\n📋 Ordre d'exécution:")
    for phase, modules in execution_plan['execution_order'].items():
        print(f"   Phase {phase}: {', '.join(modules)}")
    
    # Vérifier que screen_reader est en phase 1
    if 1 in execution_plan['execution_order']:
        phase_1_modules = execution_plan['execution_order'][1]
        if 'screen_reader' in phase_1_modules:
            print("✅ ScreenReader est bien en Phase 1")
        else:
            print("❌ ScreenReader n'est pas en Phase 1")
            return False
    else:
        print("❌ Aucune Phase 1 trouvée")
        return False
    
    # Vérifier que tab_navigation est en phase 2
    if 2 in execution_plan['execution_order']:
        phase_2_modules = execution_plan['execution_order'][2]
        if 'tab_navigation' in phase_2_modules:
            print("✅ TabNavigator est bien en Phase 2")
        else:
            print("❌ TabNavigator n'est pas en Phase 2")
            return False
    else:
        print("❌ Aucune Phase 2 trouvée")
        return False
    
    print("\n🎉 Test réussi ! L'ordre d'exécution est correct.")
    return True

if __name__ == "__main__":
    test_execution_order()
