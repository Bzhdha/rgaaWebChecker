"""
Configuration pour l'ordre d'exécution des modules d'accessibilité
"""

class ExecutionConfig:
    """Configuration de l'ordre d'exécution des modules"""
    
    # Définition des dépendances entre modules
    DEPENDENCIES = {
        'tab_navigation': ['screen_reader'],  # TabNavigator dépend de ScreenReader
        'enhanced_tab_navigation': ['screen_reader'],  # EnhancedTabNavigator dépend de ScreenReader
        'image_analyzer': [],  # ImageAnalyzer est indépendant
        'contrast': [],  # ContrastChecker est indépendant
        'daltonism': [],  # ColorSimulator est indépendant
        'navigation': [],  # NavigationModule est indépendant
        'dom_analyzer': []  # DOMAnalyzer est indépendant
    }
    
    # Priorités d'exécution (plus le nombre est bas, plus c'est prioritaire)
    PRIORITIES = {
        'screen_reader': 1,      # DOIT être en premier
        'tab_navigation': 2,     # DOIT être en second
        'enhanced_tab_navigation': 2,  # Alternative au TabNavigator
        'contrast': 3,           # Peut s'exécuter en parallèle
        'daltonism': 3,          # Peut s'exécuter en parallèle
        'image_analyzer': 3,     # Peut s'exécuter en parallèle
        'navigation': 3,         # Peut s'exécuter en parallèle
        'dom_analyzer': 4        # En dernier
    }
    
    # Modules qui peuvent s'exécuter en parallèle
    PARALLEL_MODULES = {
        3: ['contrast', 'daltonism', 'image_analyzer', 'navigation']
    }
    
    @classmethod
    def get_execution_order(cls, enabled_modules):
        """
        Calcule l'ordre d'exécution optimal pour les modules activés
        
        Args:
            enabled_modules: Liste des modules activés
            
        Returns:
            dict: Ordre d'exécution par phase
        """
        execution_order = {}
        
        # Phase 1: Modules de collecte de données (priorité 1)
        phase_1 = []
        for module in enabled_modules:
            if cls.PRIORITIES.get(module, 999) == 1:
                phase_1.append(module)
        if phase_1:
            execution_order[1] = phase_1
        
        # Phase 2: Modules dépendants (priorité 2)
        phase_2 = []
        for module in enabled_modules:
            if cls.PRIORITIES.get(module, 999) == 2:
                phase_2.append(module)
        if phase_2:
            execution_order[2] = phase_2
        
        # Phase 3: Modules parallèles (priorité 3)
        phase_3 = []
        for module in enabled_modules:
            if cls.PRIORITIES.get(module, 999) == 3:
                phase_3.append(module)
        if phase_3:
            execution_order[3] = phase_3
        
        # Phase 4: Modules finaux (priorité 4+)
        phase_4 = []
        for module in enabled_modules:
            if cls.PRIORITIES.get(module, 999) >= 4:
                phase_4.append(module)
        if phase_4:
            execution_order[4] = phase_4
        
        return execution_order
    
    @classmethod
    def validate_dependencies(cls, enabled_modules):
        """
        Valide que toutes les dépendances sont satisfaites
        
        Args:
            enabled_modules: Liste des modules activés
            
        Returns:
            tuple: (is_valid, missing_dependencies)
        """
        missing_deps = []
        
        for module in enabled_modules:
            dependencies = cls.DEPENDENCIES.get(module, [])
            for dep in dependencies:
                if dep not in enabled_modules:
                    missing_deps.append((module, dep))
        
        is_valid = len(missing_deps) == 0
        return is_valid, missing_deps
    
    @classmethod
    def get_parallel_groups(cls, enabled_modules):
        """
        Identifie les groupes de modules qui peuvent s'exécuter en parallèle
        
        Args:
            enabled_modules: Liste des modules activés
            
        Returns:
            dict: Groupes de modules parallèles par phase
        """
        parallel_groups = {}
        
        for phase, modules in cls.PARALLEL_MODULES.items():
            available_modules = [m for m in modules if m in enabled_modules]
            if available_modules:
                parallel_groups[phase] = available_modules
        
        return parallel_groups
    
    @classmethod
    def get_execution_plan(cls, enabled_modules):
        """
        Génère un plan d'exécution complet
        
        Args:
            enabled_modules: Liste des modules activés
            
        Returns:
            dict: Plan d'exécution détaillé
        """
        # Valider les dépendances
        is_valid, missing_deps = cls.validate_dependencies(enabled_modules)
        if not is_valid:
            return {
                'valid': False,
                'error': f"Dépendances manquantes: {missing_deps}",
                'plan': None
            }
        
        # Calculer l'ordre d'exécution
        execution_order = cls.get_execution_order(enabled_modules)
        parallel_groups = cls.get_parallel_groups(enabled_modules)
        
        return {
            'valid': True,
            'execution_order': execution_order,
            'parallel_groups': parallel_groups,
            'total_phases': len(execution_order),
            'estimated_time': cls._estimate_execution_time(enabled_modules)
        }
    
    @classmethod
    def _estimate_execution_time(cls, enabled_modules):
        """
        Estime le temps d'exécution basé sur les modules activés
        
        Args:
            enabled_modules: Liste des modules activés
            
        Returns:
            int: Temps estimé en secondes
        """
        # Temps estimés par module (en secondes)
        module_times = {
            'screen_reader': 30,
            'tab_navigation': 20,
            'enhanced_tab_navigation': 25,
            'contrast': 15,
            'daltonism': 10,
            'image_analyzer': 20,
            'navigation': 15,
            'dom_analyzer': 25
        }
        
        total_time = 0
        for module in enabled_modules:
            total_time += module_times.get(module, 10)
        
        return total_time
