# -*- coding: utf-8 -*-
"""
Configuration pour l'interface graphique RGAA Web Checker
"""

# Configuration des couleurs et thèmes
THEMES = {
    'default': {
        'bg_color': '#f0f0f0',
        'fg_color': '#333333',
        'accent_color': '#007acc',
        'success_color': '#28a745',
        'warning_color': '#ffc107',
        'error_color': '#dc3545',
        'card_bg': '#ffffff',
        'border_color': '#dee2e6',
        'text_color': '#212529',
        'button_bg': '#007acc',
        'button_fg': '#ffffff',
        'button_hover': '#0056b3'
    },
    'dark': {
        'bg_color': '#2d3748',
        'fg_color': '#e2e8f0',
        'accent_color': '#4299e1',
        'success_color': '#48bb78',
        'warning_color': '#ed8936',
        'error_color': '#f56565',
        'card_bg': '#4a5568',
        'border_color': '#718096',
        'text_color': '#f7fafc',
        'button_bg': '#4299e1',
        'button_fg': '#ffffff',
        'button_hover': '#3182ce'
    },
    'light': {
        'bg_color': '#ffffff',
        'fg_color': '#000000',
        'accent_color': '#0066cc',
        'success_color': '#198754',
        'warning_color': '#fd7e14',
        'error_color': '#dc3545',
        'card_bg': '#f8f9fa',
        'border_color': '#ced4da',
        'text_color': '#212529',
        'button_bg': '#0066cc',
        'button_fg': '#ffffff',
        'button_hover': '#0056b3'
    }
}

# Configuration des polices
FONTS = {
    'title': ('Segoe UI', 16, 'bold'),
    'subtitle': ('Segoe UI', 12, 'bold'),
    'body': ('Segoe UI', 10),
    'button': ('Segoe UI', 10, 'bold'),
    'code': ('Consolas', 9),
    'small': ('Segoe UI', 8)
}

# Configuration des tailles
SIZES = {
    'window_min_width': 1000,
    'window_min_height': 600,
    'window_default_width': 1200,
    'window_default_height': 800,
    'padding': 10,
    'button_height': 30,
    'entry_height': 25,
    'tree_row_height': 20
}

# Configuration des modules
MODULES_CONFIG = {
    'contrast': {
        'name': 'Analyse des contrastes',
        'description': 'Vérifie les ratios de contraste selon WCAG',
        'icon': '🎨',
        'severity_colors': {
            'critical': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745'
        }
    },
    'dom': {
        'name': 'Analyse DOM',
        'description': 'Analyse la structure DOM et les attributs d\'accessibilité',
        'icon': '🏗️',
        'severity_colors': {
            'critical': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745'
        }
    },
    'daltonism': {
        'name': 'Simulation daltonisme',
        'description': 'Simule différents types de daltonisme',
        'icon': '👁️',
        'severity_colors': {
            'critical': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745'
        }
    },
    'tab': {
        'name': 'Navigation tabulation',
        'description': 'Teste la navigation au clavier',
        'icon': '⌨️',
        'severity_colors': {
            'critical': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745'
        }
    },
    'screen': {
        'name': 'Lecteur d\'écran',
        'description': 'Analyse pour les lecteurs d\'écran',
        'icon': '🔊',
        'severity_colors': {
            'critical': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745'
        }
    },
    'image': {
        'name': 'Analyse d\'images',
        'description': 'Vérifie l\'accessibilité des images',
        'icon': '🖼️',
        'severity_colors': {
            'critical': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745'
        }
    }
}

# Configuration des messages
MESSAGES = {
    'app_title': 'RGAA Web Checker - Analyseur d\'Accessibilité',
    'ready': 'Prêt',
    'analyzing': 'Analyse en cours...',
    'finished': 'Analyse terminée',
    'error': 'Erreur',
    'warning': 'Avertissement',
    'info': 'Information',
    'success': 'Succès',
    
    # Messages d'erreur
    'url_required': 'Veuillez saisir une URL',
    'no_results': 'Aucun résultat à exporter',
    'no_images': 'Aucune image trouvée',
    'analysis_error': 'Une erreur s\'est produite lors de l\'analyse',
    'launch_error': 'Impossible de lancer l\'interface graphique',
    
    # Messages de succès
    'analysis_complete': 'Analyse terminée avec succès',
    'export_success': 'Export réussi',
    'save_success': 'Sauvegarde réussie',
    
    # Messages d'information
    'no_results_folder': 'Le dossier de résultats n\'existe pas encore',
    'dependencies_missing': 'Dépendances manquantes',
    'modules_missing': 'Modules de l\'application manquants'
}

# Configuration des colonnes pour le tableau de résultats
RESULTS_COLUMNS = [
    {
        'id': 'module',
        'name': 'Module',
        'width': 150,
        'stretch': False
    },
    {
        'id': 'type',
        'name': 'Type',
        'width': 150,
        'stretch': False
    },
    {
        'id': 'message',
        'name': 'Message',
        'width': 300,
        'stretch': True
    },
    {
        'id': 'severity',
        'name': 'Sévérité',
        'width': 100,
        'stretch': False
    }
]

# Configuration des formats d'export
EXPORT_FORMATS = {
    'csv': {
        'name': 'CSV',
        'extension': '.csv',
        'description': 'Format CSV pour Excel'
    },
    'json': {
        'name': 'JSON',
        'extension': '.json',
        'description': 'Format JSON structuré'
    },
    'txt': {
        'name': 'Texte',
        'extension': '.txt',
        'description': 'Format texte simple'
    }
}

# Configuration des navigateurs
BROWSERS = {
    'auto': {
        'name': 'Détection automatique',
        'description': 'Chrome puis Chromium'
    },
    'chrome': {
        'name': 'Google Chrome',
        'description': 'Navigateur Chrome'
    },
    'chromium': {
        'name': 'Chromium',
        'description': 'Navigateur Chromium'
    }
}

# Configuration des encodages
ENCODINGS = {
    'utf-8': {
        'name': 'UTF-8',
        'description': 'Encodage Unicode standard'
    },
    'cp1252': {
        'name': 'CP1252',
        'description': 'Encodage Windows'
    }
}

# Configuration des raccourcis clavier
KEYBOARD_SHORTCUTS = {
    'start_analysis': '<Control-Return>',
    'stop_analysis': '<Control-s>',
    'export_csv': '<Control-e>',
    'export_json': '<Control-j>',
    'open_results': '<Control-o>',
    'clear_logs': '<Control-l>',
    'save_logs': '<Control-s>',
    'next_image': '<Right>',
    'prev_image': '<Left>',
    'quit': '<Control-q>'
}

# Configuration des tooltips
TOOLTIPS = {
    'url_entry': 'Saisissez l\'URL complète du site à analyser (ex: https://example.com)',
    'modules_frame': 'Sélectionnez les modules d\'analyse à activer',
    'browser_combo': 'Choisissez le navigateur à utiliser pour l\'analyse',
    'encoding_combo': 'Sélectionnez l\'encodage pour les rapports',
    'cookie_entry': 'Texte du bouton de la bannière de cookies à cliquer',
    'output_entry': 'Dossier où sauvegarder les résultats et images',
    'debug_check': 'Affiche les logs détaillés pendant l\'analyse',
    'start_button': 'Démarre l\'analyse d\'accessibilité',
    'stop_button': 'Arrête l\'analyse en cours',
    'open_folder_button': 'Ouvre le dossier des résultats dans l\'explorateur',
    'export_csv_button': 'Exporte les résultats au format CSV',
    'export_json_button': 'Exporte les résultats au format JSON',
    'clear_logs_button': 'Efface tous les logs affichés',
    'save_logs_button': 'Sauvegarde les logs dans un fichier',
    'prev_image_button': 'Image précédente',
    'next_image_button': 'Image suivante'
}

# Configuration des validations
VALIDATIONS = {
    'url_pattern': r'^https?://.+',
    'url_message': 'L\'URL doit commencer par http:// ou https://',
    'min_url_length': 10,
    'max_url_length': 500,
    'min_cookie_text_length': 2,
    'max_cookie_text_length': 100,
    'min_output_dir_length': 1,
    'max_output_dir_length': 200
}

# Configuration des timeouts
TIMEOUTS = {
    'page_load': 30,
    'element_wait': 10,
    'analysis_timeout': 300,
    'image_load': 5,
    'driver_startup': 15
}

# Configuration des limites
LIMITS = {
    'max_images_display': 100,
    'max_results_display': 1000,
    'max_log_lines': 10000,
    'max_image_size_mb': 10,
    'max_concurrent_analyses': 1
} 