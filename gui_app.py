import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
import subprocess
from PIL import Image, ImageTk
import json
import csv
from datetime import datetime
import webbrowser
from pathlib import Path

# Import des modules de l'application
from core.config import Config
from core.crawler import AccessibilityCrawler
from utils.log_utils import setup_logger, log_with_step
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class RGAAWebCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RGAA Web Checker - Analyseur d'Accessibilité")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # Variables
        self.url_var = tk.StringVar()
        self.browser_var = tk.StringVar(value="auto")
        self.encoding_var = tk.StringVar(value="utf-8")
        self.cookie_banner_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value="site_images")
        self.debug_var = tk.BooleanVar()
        
        # Modules disponibles
        self.modules = {
            'contrast': {'name': 'Analyse des contrastes', 'enabled': tk.BooleanVar(value=True)},
            'dom': {'name': 'Analyse DOM', 'enabled': tk.BooleanVar(value=True)},
            'daltonism': {'name': 'Simulation daltonisme', 'enabled': tk.BooleanVar(value=True)},
            'tab': {'name': 'Navigation tabulation', 'enabled': tk.BooleanVar(value=True)},
            'screen': {'name': 'Lecteur d\'écran', 'enabled': tk.BooleanVar(value=True)},
            'image': {'name': 'Analyse d\'images', 'enabled': tk.BooleanVar(value=True)}
        }
        
        # État de l'analyse
        self.analysis_running = False
        self.results_data = {}
        self.current_images = []
        self.current_image_index = 0
        self.dom_results = {}  # Résultats détaillés de l'analyse DOM
        
        # Configuration
        self.config = Config()
        self.logger = None
        
        self.setup_ui()
        self.setup_styles()
        
    def setup_styles(self):
        """Configure les styles de l'interface"""
        style = ttk.Style()
        
        # Configuration des couleurs
        self.root.configure(bg='#f0f0f0')
        
        # Style pour les boutons
        style.configure('Action.TButton', 
                       background='#007acc', 
                       foreground='white',
                       font=('Segoe UI', 10, 'bold'))
        
        # Style pour les labels de titre
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 12, 'bold'),
                       background='#f0f0f0')
        
        # Style pour les frames
        style.configure('Card.TFrame', 
                       background='white',
                       relief='raised',
                       borderwidth=1)
    
    def setup_ui(self):
        """Configure l'interface utilisateur principale"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuration du grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Titre
        title_label = ttk.Label(main_frame, 
                               text="RGAA Web Checker", 
                               style='Title.TLabel',
                               font=('Segoe UI', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Frame de configuration
        config_frame = self.create_config_frame(main_frame)
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Notebook pour les résultats
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Onglets
        self.setup_results_tab()
        self.setup_dom_tab()  # Nouvel onglet pour l'analyse DOM
        self.setup_images_tab()
        self.setup_logs_tab()
        
        # Barre de statut
        self.status_var = tk.StringVar(value="Prêt")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def create_config_frame(self, parent):
        """Crée le frame de configuration"""
        config_frame = ttk.LabelFrame(parent, text="Configuration de l'analyse", padding="10")
        config_frame.columnconfigure(1, weight=1)
        
        # URL
        ttk.Label(config_frame, text="URL du site:").grid(row=0, column=0, sticky=tk.W, pady=2)
        url_entry = ttk.Entry(config_frame, textvariable=self.url_var, width=50)
        url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Modules
        ttk.Label(config_frame, text="Modules à activer:").grid(row=1, column=0, sticky=tk.W, pady=2)
        modules_frame = ttk.Frame(config_frame)
        modules_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Grille de modules (2 colonnes)
        for i, (key, module) in enumerate(self.modules.items()):
            row = i // 2
            col = i % 2
            cb = ttk.Checkbutton(modules_frame, 
                                text=module['name'], 
                                variable=module['enabled'])
            cb.grid(row=row, column=col, sticky=tk.W, padx=(0, 20))
        
        # Options avancées
        options_frame = ttk.LabelFrame(config_frame, text="Options avancées", padding="5")
        options_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        options_frame.columnconfigure(1, weight=1)
        
        # Navigateur
        ttk.Label(options_frame, text="Navigateur:").grid(row=0, column=0, sticky=tk.W, pady=2)
        browser_combo = ttk.Combobox(options_frame, 
                                   textvariable=self.browser_var,
                                   values=["auto", "chrome", "chromium"],
                                   state="readonly",
                                   width=15)
        browser_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Encodage
        ttk.Label(options_frame, text="Encodage:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0), pady=2)
        encoding_combo = ttk.Combobox(options_frame, 
                                    textvariable=self.encoding_var,
                                    values=["utf-8", "cp1252"],
                                    state="readonly",
                                    width=10)
        encoding_combo.grid(row=0, column=3, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Bannière cookies
        ttk.Label(options_frame, text="Bannière cookies:").grid(row=1, column=0, sticky=tk.W, pady=2)
        cookie_entry = ttk.Entry(options_frame, textvariable=self.cookie_banner_var, width=20)
        cookie_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Répertoire de sortie
        ttk.Label(options_frame, text="Répertoire:").grid(row=1, column=2, sticky=tk.W, padx=(20, 0), pady=2)
        output_entry = ttk.Entry(options_frame, textvariable=self.output_dir_var, width=20)
        output_entry.grid(row=1, column=3, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Debug
        debug_cb = ttk.Checkbutton(options_frame, 
                                 text="Mode debug", 
                                 variable=self.debug_var)
        debug_cb.grid(row=1, column=4, sticky=tk.W, padx=(20, 0), pady=2)
        
        # Boutons d'action
        buttons_frame = ttk.Frame(config_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=(15, 0))
        
        self.start_button = ttk.Button(buttons_frame, 
                                      text="Démarrer l'analyse", 
                                      command=self.start_analysis,
                                      style='Action.TButton')
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(buttons_frame, 
                                     text="Arrêter", 
                                     command=self.stop_analysis,
                                     state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(buttons_frame, 
                  text="Ouvrir dossier résultats", 
                  command=self.open_results_folder).pack(side=tk.LEFT)
        
        return config_frame
    
    def setup_results_tab(self):
        """Configure l'onglet des résultats"""
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="Résultats")
        
        # Frame pour les statistiques
        stats_frame = ttk.LabelFrame(results_frame, text="Statistiques", padding="10")
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=4, wrap=tk.WORD)
        self.stats_text.pack(fill=tk.X)
        
        # Frame pour les résultats détaillés
        results_detail_frame = ttk.LabelFrame(results_frame, text="Résultats détaillés", padding="10")
        results_detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview pour les résultats
        columns = ('Module', 'Type', 'Message', 'Sévérité')
        self.results_tree = ttk.Treeview(results_detail_frame, columns=columns, show='headings')
        
        # Configuration des colonnes
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_detail_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Boutons d'export
        export_frame = ttk.Frame(results_frame)
        export_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(export_frame, text="Exporter CSV", command=self.export_results_csv).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(export_frame, text="Exporter JSON", command=self.export_results_json).pack(side=tk.LEFT)
    
    def setup_dom_tab(self):
        """Configure l'onglet d'analyse DOM avec tableau interactif"""
        dom_frame = ttk.Frame(self.notebook)
        self.notebook.add(dom_frame, text="Analyse DOM")
        
        # Frame pour les contrôles de filtrage
        controls_frame = ttk.LabelFrame(dom_frame, text="Filtres et recherche", padding="10")
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Barre de recherche
        search_frame = ttk.Frame(controls_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Recherche:").pack(side=tk.LEFT)
        self.dom_search_var = tk.StringVar()
        self.dom_search_entry = ttk.Entry(search_frame, textvariable=self.dom_search_var, width=40)
        self.dom_search_entry.pack(side=tk.LEFT, padx=(10, 0))
        self.dom_search_entry.bind('<KeyRelease>', self.filter_dom_data)
        
        # Filtres par type d'élément
        filter_frame = ttk.Frame(controls_frame)
        filter_frame.pack(fill=tk.X)
        
        ttk.Label(filter_frame, text="Filtrer par:").pack(side=tk.LEFT)
        
        # Filtre par tag
        ttk.Label(filter_frame, text="Tag:").pack(side=tk.LEFT, padx=(10, 0))
        self.tag_filter_var = tk.StringVar()
        self.tag_filter_combo = ttk.Combobox(filter_frame, textvariable=self.tag_filter_var, 
                                           values=["Tous", "div", "span", "a", "button", "input", "img", "p", "h1", "h2", "h3", "h4", "h5", "h6"],
                                           state="readonly", width=10)
        self.tag_filter_combo.pack(side=tk.LEFT, padx=(5, 0))
        self.tag_filter_combo.bind('<<ComboboxSelected>>', self.filter_dom_data)
        
        # Filtre par visibilité
        ttk.Label(filter_frame, text="Visibilité:").pack(side=tk.LEFT, padx=(10, 0))
        self.visibility_filter_var = tk.StringVar(value="Tous")
        self.visibility_filter_combo = ttk.Combobox(filter_frame, textvariable=self.visibility_filter_var,
                                                  values=["Tous", "Visible", "Masqué"],
                                                  state="readonly", width=10)
        self.visibility_filter_combo.pack(side=tk.LEFT, padx=(5, 0))
        self.visibility_filter_combo.bind('<<ComboboxSelected>>', self.filter_dom_data)
        
        # Bouton pour réinitialiser les filtres
        ttk.Button(filter_frame, text="Réinitialiser", command=self.reset_dom_filters).pack(side=tk.RIGHT)
        
        # Frame pour les statistiques DOM
        dom_stats_frame = ttk.LabelFrame(dom_frame, text="Statistiques DOM", padding="10")
        dom_stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.dom_stats_text = tk.Text(dom_stats_frame, height=3, wrap=tk.WORD)
        self.dom_stats_text.pack(fill=tk.X)
        
        # Frame pour le tableau des éléments DOM
        dom_table_frame = ttk.LabelFrame(dom_frame, text="Éléments DOM analysés", padding="10")
        dom_table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- Correction placement ascenseurs ---
        # Frame conteneur pour le tableau et les scrollbars
        table_container = ttk.Frame(dom_table_frame)
        table_container.pack(fill=tk.BOTH, expand=True)
        # Colonnes pour le tableau DOM (toutes les colonnes du JSON)
        dom_columns = (
            'Tag', 'ID', 'Classe', 'Rôle', 'Aria-label', 'Aria-describedby', 'Aria-hidden', 'Aria-expanded', 'Aria-controls', 'Aria-labelledby',
            'Texte', 'Alt', 'Title', 'Href', 'Src', 'Type', 'Value', 'Placeholder',
            'Media Path', 'Media Type', 'XPath', 'CSS Selector',
            'Is Visible', 'Is Displayed', 'Is Enabled', 'Is Focusable',
            'Position', 'Computed Style', 'Accessible Name'
        )
        self.dom_tree = ttk.Treeview(table_container, columns=dom_columns, show='headings', height=15)
        # Configuration des colonnes avec tri
        for col in dom_columns:
            self.dom_tree.heading(col, text=col, command=lambda c=col: self.sort_dom_tree(c))
            self.dom_tree.column(col, width=140)
        # Scrollbars
        dom_v_scrollbar = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.dom_tree.yview)
        dom_h_scrollbar = ttk.Scrollbar(table_container, orient=tk.HORIZONTAL, command=self.dom_tree.xview)
        self.dom_tree.configure(yscrollcommand=dom_v_scrollbar.set, xscrollcommand=dom_h_scrollbar.set)
        # Placement dans le frame conteneur
        self.dom_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        dom_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        dom_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        # Ajout du binding double-clic pour copier le xpath
        self.dom_tree.bind('<Double-1>', self.copy_xpath_on_double_click)
        
        # Boutons d'export pour DOM
        dom_export_frame = ttk.Frame(dom_frame)
        dom_export_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(dom_export_frame, text="Exporter DOM CSV", command=self.export_dom_csv).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(dom_export_frame, text="Exporter DOM JSON", command=self.export_dom_json).pack(side=tk.LEFT)
        
        # Variables pour le tri
        self.dom_sort_column = None
        self.dom_sort_reverse = False
        self.dom_data = []  # Données brutes pour le filtrage
    
    def setup_images_tab(self):
        """Configure l'onglet des images"""
        images_frame = ttk.Frame(self.notebook)
        self.notebook.add(images_frame, text="Images capturées")
        
        # Frame pour la navigation des images
        nav_frame = ttk.Frame(images_frame)
        nav_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.prev_button = ttk.Button(nav_frame, text="← Précédente", command=self.prev_image)
        self.prev_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.image_info_label = ttk.Label(nav_frame, text="Aucune image")
        self.image_info_label.pack(side=tk.LEFT, expand=True)
        
        self.next_button = ttk.Button(nav_frame, text="Suivante →", command=self.next_image)
        self.next_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Frame pour l'affichage de l'image
        image_display_frame = ttk.Frame(images_frame)
        image_display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Canvas pour l'image
        self.image_canvas = tk.Canvas(image_display_frame, bg='white')
        self.image_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars pour le canvas
        h_scrollbar = ttk.Scrollbar(image_display_frame, orient=tk.HORIZONTAL, command=self.image_canvas.xview)
        v_scrollbar = ttk.Scrollbar(image_display_frame, orient=tk.VERTICAL, command=self.image_canvas.yview)
        self.image_canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.image_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    def setup_logs_tab(self):
        """Configure l'onglet des logs"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logs")
        
        # Zone de texte pour les logs
        self.logs_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD, height=20)
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Boutons pour les logs
        logs_buttons_frame = ttk.Frame(logs_frame)
        logs_buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(logs_buttons_frame, text="Effacer les logs", command=self.clear_logs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(logs_buttons_frame, text="Sauvegarder les logs", command=self.save_logs).pack(side=tk.LEFT)
    
    def start_analysis(self):
        """Démarre l'analyse dans un thread séparé"""
        if not self.url_var.get().strip():
            messagebox.showerror("Erreur", "Veuillez saisir une URL")
            return
        
        if self.analysis_running:
            return
        
        # Préparer l'interface
        self.analysis_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set("Analyse en cours...")
        
        # Effacer les résultats précédents
        self.clear_results()
        self.clear_logs()
        
        # Démarrer l'analyse dans un thread séparé
        self.analysis_thread = threading.Thread(target=self.run_analysis)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
    
    def run_analysis(self):
        """Exécute l'analyse"""
        try:
            # Configuration
            url = self.url_var.get().strip()
            self.config.set_base_url(url)
            self.config.set_output_dir(self.output_dir_var.get())
            
            # Modules
            module_flags = 0
            for key, module in self.modules.items():
                if module['enabled'].get():
                    module_flags |= getattr(Config, f'MODULE_{key.upper()}')
            self.config.set_modules(module_flags)
            
            # Logger
            self.logger = setup_logger(debug=self.debug_var.get(), encoding=self.encoding_var.get())
            
            # Options Chrome
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Naviguer vers l'URL
            driver.get(url)
            self.update_logs(f"Navigation vers: {url}")
            
            # Attendre que la page soit chargée
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            
            # Gérer la bannière de cookies si spécifiée
            if self.cookie_banner_var.get().strip():
                self.handle_cookie_banner(driver)
            
            # Exécuter les modules activés
            results = {}
            dom_results = None
            
            # Analyse DOM
            if self.modules['dom']['enabled'].get():
                self.update_logs("Démarrage de l'analyse DOM...")
                from modules.dom_analyzer import DOMAnalyzer
                dom_analyzer = DOMAnalyzer(driver, self.logger)
                dom_results = dom_analyzer.run()
                results['dom'] = dom_results
                self.update_logs("Analyse DOM terminée")
            
            # Autres modules si activés
            if self.modules['contrast']['enabled'].get():
                self.update_logs("Démarrage de l'analyse des contrastes...")
                from modules.contrast_checker import ContrastChecker
                contrast_checker = ContrastChecker(driver, self.logger)
                results['contrast'] = contrast_checker.run()
                self.update_logs("Analyse des contrastes terminée")
            
            if self.modules['daltonism']['enabled'].get():
                self.update_logs("Démarrage de la simulation daltonisme...")
                from modules.color_simulator import ColorSimulator
                color_simulator = ColorSimulator(driver, self.logger)
                results['daltonism'] = color_simulator.run()
                self.update_logs("Simulation daltonisme terminée")
            
            if self.modules['tab']['enabled'].get():
                self.update_logs("Démarrage de l'analyse de navigation tabulation...")
                from modules.tab_navigator import TabNavigator
                tab_navigator = TabNavigator(driver, self.logger)
                results['tab'] = tab_navigator.run()
                self.update_logs("Analyse de navigation tabulation terminée")
            
            if self.modules['screen']['enabled'].get():
                self.update_logs("Démarrage de l'analyse lecteur d'écran...")
                from modules.screen_reader import ScreenReader
                screen_reader = ScreenReader(driver, self.logger)
                results['screen'] = screen_reader.run()
                self.update_logs("Analyse lecteur d'écran terminée")
            
            if self.modules['image']['enabled'].get():
                self.update_logs("Démarrage de l'analyse d'images...")
                from modules.image_analyzer import ImageAnalyzer
                image_analyzer = ImageAnalyzer(driver, self.logger, url, self.output_dir_var.get())
                results['image'] = image_analyzer.run()
                self.update_logs("Analyse d'images terminée")
            
            # Mettre à jour l'interface avec les résultats
            self.root.after(0, lambda: self.process_results(results, dom_results))
            
        except ImportError as e:
            error_msg = f"Module manquant: {str(e)}\n\nVérifiez que tous les modules sont installés:\npip install -r requirements.txt"
            self.root.after(0, lambda: self.handle_analysis_error(error_msg))
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.handle_analysis_error(error_msg))
        finally:
            if 'driver' in locals():
                driver.quit()
            self.root.after(0, self.analysis_finished)
    
    def handle_cookie_banner(self, driver):
        """Gère la bannière de cookies"""
        try:
            cookie_text = self.cookie_banner_var.get().strip()
            if not cookie_text:
                return
            
            # Chercher le bouton avec le texte spécifié
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            button_xpath = f"""
                //button[
                    contains(text(), '{cookie_text}') or
                    contains(@aria-label, '{cookie_text}') or
                    contains(@title, '{cookie_text}')
                ]
            """
            
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, button_xpath))
            )
            
            self.update_logs(f"Bouton cookie trouvé: {cookie_text}")
            button.click()
            self.update_logs("Clic sur le bouton cookie effectué")
            
            # Attendre que la bannière disparaisse
            import time
            time.sleep(2)
            
        except Exception as e:
            self.update_logs(f"Erreur lors de la gestion de la bannière cookie: {str(e)}")
    
    def process_results(self, results, dom_results=None):
        """Traite et affiche les résultats"""
        self.results_data = results
        
        # Traiter les résultats DOM
        if dom_results:
            self.dom_results = dom_results
            self.display_dom_results(dom_results)
        elif 'dom' in results:
            self.dom_results = results['dom']
            self.display_dom_results(results['dom'])
        
        # Statistiques
        stats = self.calculate_statistics(results)
        self.display_statistics(stats)
        
        # Résultats détaillés
        self.display_detailed_results(results)
        
        # Images
        self.load_images()
        
        # Logs
        self.update_logs("Analyse terminée avec succès")
    
    def calculate_statistics(self, results):
        """Calcule les statistiques des résultats"""
        stats = {
            'total_issues': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'modules_run': len([m for m in self.modules.values() if m['enabled'].get()])
        }
        
        for module_name, module_results in results.items():
            if isinstance(module_results, dict) and 'issues' in module_results:
                issues = module_results['issues']
                stats['total_issues'] += len(issues)
                for issue in issues:
                    severity = issue.get('severity', 'medium')
                    if severity in stats:
                        stats[severity] += 1
        
        return stats
    
    def display_statistics(self, stats):
        """Affiche les statistiques"""
        stats_text = f"""
        Modules exécutés: {stats['modules_run']}
        Total des problèmes: {stats['total_issues']}
        
        Répartition par sévérité:
        - Critique: {stats['critical']}
        - Élevée: {stats['high']}
        - Moyenne: {stats['medium']}
        - Faible: {stats['low']}
        """
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
    
    def display_detailed_results(self, results):
        """Affiche les résultats détaillés dans le treeview"""
        # Effacer les résultats précédents
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Ajouter les nouveaux résultats
        for module_name, module_results in results.items():
            if isinstance(module_results, dict) and 'issues' in module_results:
                issues = module_results['issues']
                for issue in issues:
                    self.results_tree.insert('', tk.END, values=(
                        module_name,
                        issue.get('type', 'N/A'),
                        issue.get('message', 'N/A'),
                        issue.get('severity', 'medium')
                    ))
    
    def display_dom_results(self, dom_results):
        """Affiche les résultats de l'analyse DOM"""
        if not dom_results:
            self.dom_stats_text.delete(1.0, tk.END)
            self.dom_stats_text.insert(1.0, "Aucun résultat d'analyse DOM disponible")
            self.update_logs("Aucun résultat DOM à afficher")
            return
        
        # Vérifier la structure des résultats
        if not isinstance(dom_results, dict):
            self.dom_stats_text.delete(1.0, tk.END)
            self.dom_stats_text.insert(1.0, f"Format de résultats DOM invalide: {type(dom_results)}")
            self.update_logs(f"Format de résultats DOM invalide: {type(dom_results)}")
            return
        
        # Afficher les statistiques
        summary = dom_results.get('summary', {})
        elements = dom_results.get('elements', [])
        issues = dom_results.get('issues', [])
        
        stats_text = f"""
        Éléments totaux: {summary.get('total_elements', 0)}
        Éléments analysés: {summary.get('analyzed_elements', 0)}
        Problèmes détectés: {summary.get('issues_found', 0)}
        """
        self.dom_stats_text.delete(1.0, tk.END)
        self.dom_stats_text.insert(1.0, stats_text)
        
        # Logs pour le débogage
        self.update_logs(f"Résultats DOM: {len(elements)} éléments, {len(issues)} problèmes")
        
        # Charger les données dans le tableau
        if elements:
            self.load_dom_data(elements)
        else:
            self.update_logs("Aucun élément DOM trouvé dans les résultats")
            # Effacer le tableau
            for item in self.dom_tree.get_children():
                self.dom_tree.delete(item)
    
    def get_dom_row_values(self, element):
        """Retourne le tuple de valeurs pour une ligne du tableau DOM, pour toutes les colonnes"""
        tag = element.get('tag', 'N/A')
        element_id = element.get('id', '')
        class_attr = element.get('class', '')
        role = element.get('role', '')
        aria_label = element.get('aria_label', '')
        aria_describedby = element.get('aria_describedby', '')
        aria_hidden = element.get('aria_hidden', '')
        aria_expanded = element.get('aria_expanded', '')
        aria_controls = element.get('aria_controls', '')
        aria_labelledby = element.get('aria_labelledby', '')
        text = element.get('text', '')
        alt = element.get('alt', '')
        title = element.get('title', '')
        href = element.get('href', '')
        src = element.get('src', '')
        type_ = element.get('type', '')
        value = element.get('value', '')
        placeholder = element.get('placeholder', '')
        media_path = element.get('media_path', '')
        media_type = element.get('media_type', '')
        xpath = element.get('xpath', '')
        css_selector = element.get('css_selector', '')
        is_visible = element.get('is_visible', False)
        is_displayed = element.get('is_displayed', False)
        is_enabled = element.get('is_enabled', False)
        is_focusable = element.get('is_focusable', False)
        position = element.get('position', {})
        pos_str = f"x={position.get('x','')}, y={position.get('y','')}, w={position.get('width','')}, h={position.get('height','')}" if position else ''
        computed_style = element.get('computed_style', {})
        style_str = ', '.join([f"{k}={v}" for k,v in computed_style.items()]) if computed_style else ''
        accessible_name = element.get('accessible_name', {})
        acc_name_str = f"name={accessible_name.get('name','')}, source={accessible_name.get('source','')}, priority={accessible_name.get('priority','')}" if accessible_name else ''
        return (
            tag, element_id, class_attr, role, aria_label, aria_describedby, aria_hidden, aria_expanded, aria_controls, aria_labelledby,
            text, alt, title, href, src, type_, value, placeholder,
            media_path, media_type, xpath, css_selector,
            'Oui' if is_visible else 'Non', 'Oui' if is_displayed else 'Non', 'Oui' if is_enabled else 'Non', 'Oui' if is_focusable else 'Non',
            pos_str, style_str, acc_name_str
        )

    def load_dom_data(self, elements):
        """Charge les données DOM dans le tableau"""
        # Effacer les données précédentes
        for item in self.dom_tree.get_children():
            self.dom_tree.delete(item)
        self.dom_data = elements
        self.update_logs(f"Chargement de {len(elements)} éléments DOM dans le tableau")
        for i, element in enumerate(elements):
            try:
                self.dom_tree.insert('', tk.END, values=self.get_dom_row_values(element))
                if (i + 1) % 100 == 0:
                    self.update_logs(f"Éléments DOM chargés: {i + 1}/{len(elements)}")
            except Exception as e:
                self.update_logs(f"Erreur lors du chargement de l'élément {i}: {str(e)}")
                continue
        self.update_logs(f"Chargement terminé: {len(elements)} éléments DOM affichés")
        self.update_dom_filters()
    
    def update_dom_filters(self):
        """Met à jour les options de filtrage basées sur les données disponibles"""
        if not self.dom_data:
            return
        
        # Mettre à jour les tags disponibles
        tags = set()
        for element in self.dom_data:
            tag = element.get('tag', '').lower()
            if tag:
                tags.add(tag)
        
        tag_values = ["Tous"] + sorted(list(tags))
        self.tag_filter_combo['values'] = tag_values
    
    def filter_dom_data(self, event=None):
        """Filtre les données DOM selon les critères sélectionnés"""
        if not self.dom_data:
            return
        # Effacer le tableau
        for item in self.dom_tree.get_children():
            self.dom_tree.delete(item)
        # Appliquer les filtres
        search_term = self.dom_search_var.get().lower()
        tag_filter = self.tag_filter_var.get()
        visibility_filter = self.visibility_filter_var.get()
        filtered_data = []
        for element in self.dom_data:
            # Filtre de recherche
            if search_term:
                searchable_text = f"{element.get('tag', '')} {element.get('id', '')} {element.get('class', '')} {element.get('text', '')} {element.get('alt', '')}".lower()
                if search_term not in searchable_text:
                    continue
            # Filtre par tag
            if tag_filter and tag_filter != "Tous":
                if element.get('tag', '').lower() != tag_filter.lower():
                    continue
            # Filtre par visibilité
            if visibility_filter and visibility_filter != "Tous":
                is_visible = element.get('is_visible', False)
                if visibility_filter == "Visible" and not is_visible:
                    continue
                if visibility_filter == "Masqué" and is_visible:
                    continue
            filtered_data.append(element)
        # Afficher les données filtrées
        for element in filtered_data:
            self.dom_tree.insert('', tk.END, values=self.get_dom_row_values(element))
    
    def reset_dom_filters(self):
        """Réinitialise tous les filtres DOM"""
        self.dom_search_var.set('')
        self.tag_filter_var.set('')
        self.visibility_filter_var.set('Tous')
        self.filter_dom_data()
    
    def sort_dom_tree(self, column):
        """Trie le tableau DOM par colonne"""
        if not self.dom_data:
Affi            return
        # Déterminer la direction de tri
        if self.dom_sort_column == column:
            self.dom_sort_reverse = not self.dom_sort_reverse
        else:
            self.dom_sort_reverse = False
        self.dom_sort_column = column
        # Mapping colonne -> clé JSON
        column_index = {
            'Tag': 'tag',
            'ID': 'id',
            'Classe': 'class',
            'Rôle': 'role',
            'Aria-label': 'aria_label',
            'Aria-describedby': 'aria_describedby',
            'Aria-hidden': 'aria_hidden',
            'Aria-expanded': 'aria_expanded',
            'Aria-controls': 'aria_controls',
            'Aria-labelledby': 'aria_labelledby',
            'Texte': 'text',
            'Alt': 'alt',
            'Title': 'title',
            'Href': 'href',
            'Src': 'src',
            'Type': 'type',
            'Value': 'value',
            'Placeholder': 'placeholder',
            'Media Path': 'media_path',
            'Media Type': 'media_type',
            'XPath': 'xpath',
            'CSS Selector': 'css_selector',
            'Is Visible': 'is_visible',
            'Is Displayed': 'is_displayed',
            'Is Enabled': 'is_enabled',
            'Is Focusable': 'is_focusable',
            'Position': 'position',
            'Computed Style': 'computed_style',
            'Accessible Name': 'accessible_name',
        }.get(column, 'tag')
        # Tri
        sorted_data = sorted(self.dom_data,
            key=lambda x: str(x.get(column_index, '')).lower() if not isinstance(x.get(column_index, ''), dict) else str(x.get(column_index, '')),
            reverse=self.dom_sort_reverse)
        # Recharger le tableau avec toutes les colonnes
        for item in self.dom_tree.get_children():
            self.dom_tree.delete(item)
        for element in sorted_data:
            self.dom_tree.insert('', tk.END, values=self.get_dom_row_values(element))
    
    def export_dom_csv(self):
        """Exporte les résultats DOM en CSV"""
        if not self.dom_results or 'elements' not in self.dom_results:
            messagebox.showwarning("Avertissement", "Aucun résultat DOM à exporter")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")]
        )
        if filename:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # En-tête
                writer.writerow(['Tag', 'ID', 'Classe', 'Rôle', 'Aria-label', 'Aria-describedby', 'Aria-hidden', 'Aria-expanded', 'Aria-controls', 'Aria-labelledby', 'Texte', 'Alt', 'Title', 'Href', 'Src', 'Type', 'Value', 'Placeholder', 'Media Path', 'Media Type', 'XPath', 'CSS Selector', 'Is Visible', 'Is Displayed', 'Is Enabled', 'Is Focusable', 'Position', 'Computed Style'])
                
                # Données
                for element in self.dom_results['elements']:
                    writer.writerow([
                        element.get('tag', ''),
                        element.get('id', ''),
                        element.get('class', ''),
                        element.get('role', ''),
                        element.get('aria_label', ''),
                        element.get('aria_describedby', ''),
                        element.get('aria_hidden', ''),
                        element.get('aria_expanded', ''),
                        element.get('aria_controls', ''),
                        element.get('aria_labelledby', ''),
                        element.get('text', ''),
                        element.get('alt', ''),
                        element.get('title', ''),
                        element.get('href', ''),
                        element.get('src', ''),
                        element.get('type', ''),
                        element.get('value', ''),
                        element.get('placeholder', ''),
                        element.get('media_path', ''),
                        element.get('media_type', ''),
                        element.get('xpath', ''),
                        element.get('css_selector', ''),
                        element.get('is_visible', False),
                        element.get('is_displayed', False),
                        element.get('is_enabled', False),
                        element.get('is_focusable', False),
                        str(element.get('position', {})),
                        str(element.get('computed_style', {}))
                    ])
    
    def export_dom_json(self):
        """Exporte les résultats DOM en JSON"""
        if not self.dom_results:
            messagebox.showwarning("Avertissement", "Aucun résultat DOM à exporter")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.dom_results, f, indent=2, ensure_ascii=False)
    
    def load_images(self):
        """Charge les images capturées"""
        self.current_images = []
        self.current_image_index = 0
        
        # Chercher les images dans le répertoire de sortie
        output_dir = Path(self.output_dir_var.get())
        if output_dir.exists():
            image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
            for ext in image_extensions:
                self.current_images.extend(list(output_dir.glob(f'*{ext}')))
        
        # Chercher dans le dossier reports
        reports_dir = Path('reports')
        if reports_dir.exists():
            for ext in image_extensions:
                self.current_images.extend(list(reports_dir.glob(f'*{ext}')))
        
        if self.current_images:
            self.display_current_image()
        else:
            self.image_info_label.config(text="Aucune image trouvée")
    
    def display_current_image(self):
        """Affiche l'image courante"""
        if not self.current_images:
            return
        
        try:
            # Charger l'image
            image_path = self.current_images[self.current_image_index]
            image = Image.open(image_path)
            
            # Redimensionner si nécessaire
            canvas_width = self.image_canvas.winfo_width()
            canvas_height = self.image_canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                # Calculer le ratio de redimensionnement
                img_width, img_height = image.size
                ratio = min(canvas_width / img_width, canvas_height / img_height)
                
                if ratio < 1:
                    new_width = int(img_width * ratio)
                    new_height = int(img_height * ratio)
                    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convertir pour Tkinter
            photo = ImageTk.PhotoImage(image)
            
            # Afficher sur le canvas
            self.image_canvas.delete("all")
            self.image_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            self.image_canvas.image = photo  # Garder une référence
            
            # Mettre à jour les informations
            self.image_info_label.config(
                text=f"Image {self.current_image_index + 1}/{len(self.current_images)}: {image_path.name}"
            )
            
            # Mettre à jour les boutons
            self.prev_button.config(state=tk.NORMAL if self.current_image_index > 0 else tk.DISABLED)
            self.next_button.config(state=tk.NORMAL if self.current_image_index < len(self.current_images) - 1 else tk.DISABLED)
            
        except Exception as e:
            self.image_info_label.config(text=f"Erreur lors du chargement de l'image: {str(e)}")
    
    def prev_image(self):
        """Image précédente"""
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.display_current_image()
    
    def next_image(self):
        """Image suivante"""
        if self.current_image_index < len(self.current_images) - 1:
            self.current_image_index += 1
            self.display_current_image()
    
    def stop_analysis(self):
        """Arrête l'analyse"""
        self.analysis_running = False
        self.status_var.set("Arrêt demandé...")
    
    def analysis_finished(self):
        """Appelé quand l'analyse est terminée"""
        self.analysis_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("Analyse terminée")
    
    def handle_analysis_error(self, error_msg):
        """Gère les erreurs d'analyse"""
        # Analyser le type d'erreur pour donner des suggestions
        suggestions = ""
        
        if "Chrome" in error_msg or "chromedriver" in error_msg.lower():
            suggestions = "\n\n💡 Suggestions de résolution:\n" \
                         "• Vérifiez que Chrome/Chromium est installé\n" \
                         "• Exécutez: ./install_chrome.sh ou ./install_chromium.sh\n" \
                         "• Ou utilisez l'option --browser auto"
        
        elif "module" in error_msg.lower() or "import" in error_msg.lower():
            suggestions = "\n\n💡 Suggestions de résolution:\n" \
                         "• Activez l'environnement virtuel: source venv/bin/activate\n" \
                         "• Installez les dépendances: pip install -r requirements.txt\n" \
                         "• Ou utilisez: ./activate_venv.ps1 (Windows)"
        
        elif "timeout" in error_msg.lower():
            suggestions = "\n\n💡 Suggestions de résolution:\n" \
                         "• Vérifiez votre connexion internet\n" \
                         "• L'URL est-elle accessible?\n" \
                         "• Essayez avec une URL plus simple"
        
        elif "permission" in error_msg.lower():
            suggestions = "\n\n💡 Suggestions de résolution:\n" \
                         "• Vérifiez les permissions du dossier de sortie\n" \
                         "• Exécutez en tant qu'administrateur si nécessaire"
        
        # Afficher l'erreur avec les suggestions
        full_message = f"Une erreur s'est produite lors de l'analyse:\n\n{error_msg}{suggestions}"
        messagebox.showerror("Erreur d'analyse", full_message)
        
        # Logger l'erreur
        self.update_logs(f"ERREUR: {error_msg}")
        
        # Mettre à jour le statut
        self.status_var.set("Erreur lors de l'analyse")
    
    def clear_results(self):
        """Efface les résultats"""
        self.results_data = {}
        self.stats_text.delete(1.0, tk.END)
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
    
    def clear_logs(self):
        """Efface les logs"""
        self.logs_text.delete(1.0, tk.END)
    
    def update_logs(self, message):
        """Met à jour les logs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.logs_text.insert(tk.END, log_entry)
        self.logs_text.see(tk.END)
    
    def save_logs(self):
        """Sauvegarde les logs"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.logs_text.get(1.0, tk.END))
    
    def export_results_csv(self):
        """Exporte les résultats en CSV"""
        if not self.results_data:
            messagebox.showwarning("Avertissement", "Aucun résultat à exporter")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")]
        )
        if filename:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Module', 'Type', 'Message', 'Sévérité'])
                
                for module_name, module_results in self.results_data.items():
                    if isinstance(module_results, list):
                        for issue in module_results:
                            writer.writerow([
                                module_name,
                                issue.get('type', 'N/A'),
                                issue.get('message', 'N/A'),
                                issue.get('severity', 'medium')
                            ])
    
    def export_results_json(self):
        """Exporte les résultats en JSON"""
        if not self.results_data:
            messagebox.showwarning("Avertissement", "Aucun résultat à exporter")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results_data, f, indent=2, ensure_ascii=False)
    
    def open_results_folder(self):
        """Ouvre le dossier des résultats"""
        output_dir = Path(self.output_dir_var.get())
        if output_dir.exists():
            import platform
            # Détection WSL
            if 'microsoft' in platform.uname().release.lower():
                # Ouvre dans l'explorateur Windows
                try:
                    # Utilise wslpath pour convertir le chemin si disponible
                    import shutil
                    if shutil.which('wslpath'):
                        wsl_path = subprocess.check_output(['wslpath', '-w', str(output_dir.resolve())]).decode().strip()
                        subprocess.run(['explorer.exe', wsl_path])
                    else:
                        subprocess.run(['explorer.exe', str(output_dir.resolve())])
                except Exception as e:
                    messagebox.showinfo("Information", f"Impossible d'ouvrir le dossier dans l'explorateur Windows : {e}")
            elif sys.platform == "win32":
                os.startfile(str(output_dir))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(output_dir)])
            else:
                subprocess.run(["xdg-open", str(output_dir)])
        else:
            messagebox.showinfo("Information", "Le dossier de résultats n'existe pas encore")
    
    def copy_xpath_on_double_click(self, event):
        """Copie le xpath complet dans le presse-papier si double-clic sur la colonne XPath"""
        item_id = self.dom_tree.identify_row(event.y)
        col = self.dom_tree.identify_column(event.x)
        if not item_id or not col:
            return
        col_index = int(col.replace('#','')) - 1
        # Vérifier si c'est la colonne XPath
        if self.dom_tree['columns'][col_index] == 'XPath':
            xpath_value = self.dom_tree.item(item_id, 'values')[col_index]
            self.root.clipboard_clear()
            self.root.clipboard_append(xpath_value)
            self.root.update()  # nécessaire pour le clipboard
            messagebox.showinfo("Copié", "XPath copié dans le presse-papier !")

def main():
    """Fonction principale"""
    root = tk.Tk()
    app = RGAAWebCheckerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 