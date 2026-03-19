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
from tksheet import Sheet
import pandas as pd
from pandastable import Table
import glob

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
        self.quick_load_var = tk.BooleanVar()
        
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
        self.tabulation_results = {}  # Résultats détaillés de l'analyse tabulaire
        
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
        self.setup_tabulation_tab()  # Nouvel onglet pour l'analyse tabulaire
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
        
        # Mode chargement rapide
        quick_load_cb = ttk.Checkbutton(options_frame, 
                                      text="Charger derniers résultats", 
                                      variable=self.quick_load_var)
        quick_load_cb.grid(row=1, column=5, sticky=tk.W, padx=(20, 0), pady=2)
        
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
                  text="Charger derniers résultats", 
                  command=self.load_last_results).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(buttons_frame, 
                  text="Info fichiers", 
                  command=self.show_results_info).pack(side=tk.LEFT, padx=(0, 10))
        
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
        """Configure l'onglet d'analyse DOM avec tableau PandasTable"""
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
        
        # Frame pour le tableau des éléments DOM avec PandasTable
        dom_table_frame = ttk.LabelFrame(dom_frame, text="Éléments DOM analysés", padding="10")
        dom_table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Canvas pour PandasTable
        self.dom_table_canvas = tk.Frame(dom_table_frame)
        self.dom_table_canvas.pack(fill=tk.BOTH, expand=True)
        self.dom_ptable = None
        self.dom_df = pd.DataFrame()  # DataFrame source
        
        # Boutons d'export pour DOM
        dom_export_frame = ttk.Frame(dom_frame)
        dom_export_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(dom_export_frame, text="Exporter DOM CSV", command=self.export_dom_csv).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(dom_export_frame, text="Exporter DOM JSON", command=self.export_dom_json).pack(side=tk.LEFT)
        
        # Variables pour le tri et les données
        self.dom_data = []  # Données brutes pour le filtrage
        self.filtered_dom_data = []  # Données filtrées affichées
    
    def setup_tabulation_tab(self):
        """Configure l'onglet d'analyse tabulaire"""
        tabulation_frame = ttk.Frame(self.notebook)
        self.notebook.add(tabulation_frame, text="Analyse Tabulaire")
        
        # Frame pour les contrôles de filtrage
        controls_frame = ttk.LabelFrame(tabulation_frame, text="Filtres et recherche", padding="10")
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Barre de recherche
        search_frame = ttk.Frame(controls_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Recherche:").pack(side=tk.LEFT)
        self.tabulation_search_var = tk.StringVar()
        self.tabulation_search_entry = ttk.Entry(search_frame, textvariable=self.tabulation_search_var, width=40)
        self.tabulation_search_entry.pack(side=tk.LEFT, padx=(10, 0))
        self.tabulation_search_entry.bind('<KeyRelease>', self.filter_tabulation_data)
        
        # Filtres par type d'élément
        filter_frame = ttk.Frame(controls_frame)
        filter_frame.pack(fill=tk.X)
        
        ttk.Label(filter_frame, text="Filtrer par:").pack(side=tk.LEFT)
        
        # Filtre par tag
        ttk.Label(filter_frame, text="Tag:").pack(side=tk.LEFT, padx=(10, 0))
        self.tabulation_tag_filter_var = tk.StringVar()
        self.tabulation_tag_filter_combo = ttk.Combobox(filter_frame, textvariable=self.tabulation_tag_filter_var, 
                                                      values=["Tous", "div", "span", "a", "button", "input", "img", "p", "h1", "h2", "h3", "h4", "h5", "h6"],
                                                      state="readonly", width=10)
        self.tabulation_tag_filter_combo.pack(side=tk.LEFT, padx=(5, 0))
        self.tabulation_tag_filter_combo.bind('<<ComboboxSelected>>', self.filter_tabulation_data)
        
        # Filtre par visibilité
        ttk.Label(filter_frame, text="Visibilité:").pack(side=tk.LEFT, padx=(10, 0))
        self.tabulation_visibility_filter_var = tk.StringVar(value="Tous")
        self.tabulation_visibility_filter_combo = ttk.Combobox(filter_frame, textvariable=self.tabulation_visibility_filter_var,
                                                            values=["Tous", "Visible", "Masqué"],
                                                            state="readonly", width=10)
        self.tabulation_visibility_filter_combo.pack(side=tk.LEFT, padx=(5, 0))
        self.tabulation_visibility_filter_combo.bind('<<ComboboxSelected>>', self.filter_tabulation_data)
        
        # Bouton pour réinitialiser les filtres
        ttk.Button(filter_frame, text="Réinitialiser", command=self.reset_tabulation_filters).pack(side=tk.RIGHT)
        
        # Frame pour les statistiques tabulaire
        tabulation_stats_frame = ttk.LabelFrame(tabulation_frame, text="Statistiques Tabulaire", padding="10")
        tabulation_stats_frame.pack(fill=tk.X, padx=10, pady=5)
        self.tabulation_stats_text = tk.Text(tabulation_stats_frame, height=3, wrap=tk.WORD)
        self.tabulation_stats_text.pack(fill=tk.X)
        
        # Frame pour le tableau des éléments tabulaires avec PandasTable
        tabulation_table_frame = ttk.LabelFrame(tabulation_frame, text="Éléments Tabulaires analysés", padding="10")
        tabulation_table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Canvas pour PandasTable
        self.tabulation_table_canvas = tk.Frame(tabulation_table_frame)
        self.tabulation_table_canvas.pack(fill=tk.BOTH, expand=True)
        self.tabulation_ptable = None
        self.tabulation_df = pd.DataFrame()  # DataFrame source
        
        # Boutons d'export pour tabulation
        tabulation_export_frame = ttk.Frame(tabulation_frame)
        tabulation_export_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(tabulation_export_frame, text="Exporter Tabulation CSV", command=self.export_tabulation_csv).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(tabulation_export_frame, text="Exporter Tabulation JSON", command=self.export_tabulation_json).pack(side=tk.LEFT)
        
        # Variables pour le tri et les données
        self.tabulation_data = []  # Données brutes pour le filtrage
        self.filtered_tabulation_data = []  # Données filtrées affichées
    
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
        
        # Vérifier si le mode chargement rapide est activé
        if self.quick_load_var.get():
            self.load_last_results()
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
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            # Driver
            import glob
            driver_dir = os.path.dirname(ChromeDriverManager().install())
            chromedriver_path = None
            for f in glob.glob(os.path.join(driver_dir, "chromedriver*")):
                if os.path.basename(f) == 'chromedriver' and os.path.isfile(f) and os.access(f, os.X_OK):
                    chromedriver_path = f
                    break
            if not chromedriver_path:
                raise FileNotFoundError(f"Aucun binaire chromedriver exécutable trouvé dans {driver_dir}")
            service = Service(chromedriver_path)
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
                tab_navigator = TabNavigator(driver, self.logger, tab_delay=0.0)
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
        
        # Traiter les résultats de tabulation
        if 'tab' in results:
            self.tabulation_results = results['tab']
            self.display_tabulation_results(results['tab'])
        
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
            if self.dom_ptable:
                self.dom_ptable.destroy()
            self.dom_ptable = None
            self.dom_df = pd.DataFrame()
    
    def load_dom_data(self, elements):
        """Charge les données DOM dans le tableau PandasTable"""
        # Conversion en DataFrame
        df = pd.DataFrame([self.get_dom_row_dict(element) for element in elements])
        self.dom_df = df
        self.dom_data = elements
        self.filtered_dom_data = elements
        self.update_logs(f"Chargement de {len(elements)} éléments DOM dans le tableau")
        
        # Affichage dans PandasTable avec options pour éviter le bug atdivider
        self.create_dom_table(self.dom_df)
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
        if self.dom_ptable:
            self.dom_ptable.destroy()
        self.dom_ptable = None
        self.dom_df = pd.DataFrame()
        
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
        
        # Préparer les données filtrées
        df = pd.DataFrame([self.get_dom_row_dict(element) for element in filtered_data])
        self.dom_df = df
        self.filtered_dom_data = filtered_data
        
        # Affichage dans PandasTable
        self.create_dom_table(self.dom_df)
    
    def reset_dom_filters(self):
        """Réinitialise tous les filtres DOM"""
        self.dom_search_var.set('')
        self.tag_filter_var.set('')
        self.visibility_filter_var.set('Tous')
        # Recharger toutes les données
        if self.dom_data:
            self.create_dom_table(self.dom_df)
    
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
        
        # Effacer les résultats DOM
        self.dom_results = {}
        self.dom_data = []
        self.filtered_dom_data = []
        if self.dom_ptable:
            self.dom_ptable.destroy()
        self.dom_ptable = None
        self.dom_df = pd.DataFrame()
        self.dom_stats_text.delete(1.0, tk.END)
        
        # Effacer les résultats de tabulation
        self.tabulation_results = {}
        self.tabulation_data = []
        self.filtered_tabulation_data = []
        if self.tabulation_ptable:
            self.tabulation_ptable.destroy()
        self.tabulation_ptable = None
        self.tabulation_df = pd.DataFrame()
        self.tabulation_stats_text.delete(1.0, tk.END)
    
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
    
    def get_dom_row_dict(self, element):
        """Retourne un dict pour une ligne du tableau DOM (pour DataFrame)"""
        return {
            'Tag': element.get('tag', 'N/A'),
            'ID': element.get('id', ''),
            'Classe': element.get('class', ''),
            'Rôle': element.get('role', ''),
            'Aria-label': element.get('aria_label', ''),
            'Aria-describedby': element.get('aria_describedby', ''),
            'Aria-hidden': element.get('aria_hidden', ''),
            'Aria-expanded': element.get('aria_expanded', ''),
            'Aria-controls': element.get('aria_controls', ''),
            'Aria-labelledby': element.get('aria_labelledby', ''),
            'Texte': element.get('text', ''),
            'Alt': element.get('alt', ''),
            'Title': element.get('title', ''),
            'Href': element.get('href', ''),
            'Src': element.get('src', ''),
            'Type': element.get('type', ''),
            'Value': element.get('value', ''),
            'Placeholder': element.get('placeholder', ''),
            'Media Path': element.get('media_path', ''),
            'Media Type': element.get('media_type', ''),
            'XPath': element.get('xpath', ''),
            'CSS Selector': element.get('css_selector', ''),
            'Is Visible': 'Oui' if element.get('is_visible', False) else 'Non',
            'Is Displayed': 'Oui' if element.get('is_displayed', False) else 'Non',
            'Is Enabled': 'Oui' if element.get('is_enabled', False) else 'Non',
            'Is Focusable': 'Oui' if element.get('is_focusable', False) else 'Non',
            'Position': str(element.get('position', {})),
            'Computed Style': str(element.get('computed_style', {})),
            'Accessible Name': str(element.get('accessible_name', {})),
        }

    def load_last_results(self):
        """Charge les derniers résultats sans refaire l'analyse"""
        try:
            self.update_logs("Chargement des derniers résultats...")
            # Chercher les fichiers de résultats récents
            results_files = self.find_latest_results()
            if not results_files:
                messagebox.showinfo("Information", "Aucun fichier de résultats trouvé.\nExécutez d'abord une analyse.")
                return
            # Charger les résultats DOM
            dom_results = self.load_dom_results(results_files.get('dom_json'))
            # Charger les résultats de tabulation
            tabulation_results = self.load_tabulation_results(results_files.get('tabulation_json'))
            # Charger les autres résultats
            other_results = self.load_other_results(results_files)
            # Combiner les résultats
            combined_results = {}
            if dom_results:
                combined_results['dom'] = dom_results
            if tabulation_results:
                combined_results['tab'] = tabulation_results
            if other_results:
                combined_results.update(other_results)
            # Traiter et afficher les résultats
            if combined_results:
                self.process_results(combined_results, dom_results)
                self.update_logs("Derniers résultats chargés avec succès")
                messagebox.showinfo("Succès", "Derniers résultats chargés avec succès !")
            else:
                messagebox.showwarning("Avertissement", "Aucun résultat valide trouvé")
        except Exception as e:
            error_msg = f"Erreur lors du chargement des derniers résultats: {str(e)}"
            self.update_logs(f"ERREUR: {error_msg}")
            messagebox.showerror("Erreur", error_msg)

    def find_latest_results(self):
        """Trouve les fichiers de résultats les plus récents"""
        results_files = {}
        # Chercher le fichier DOM JSON le plus récent
        dom_json_patterns = [
            "rapport_analyse_dom.json",
            "reports/rapport_analyse_dom.json",
            "*.json"
        ]
        for pattern in dom_json_patterns:
            if pattern.startswith("*"):
                json_files = list(Path(".").glob(pattern))
                json_files = [f for f in json_files if "dom" in f.name.lower() or "result" in f.name.lower()]
            else:
                json_files = list(Path(".").glob(pattern))
            if json_files:
                latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
                results_files['dom_json'] = latest_file
                self.update_logs(f"Fichier DOM trouvé: {latest_file}")
                break
        
        # Chercher le fichier de tabulation JSON le plus récent
        tabulation_json_patterns = [
            "rapport_analyse_tab.json",
            "reports/rapport_analyse_tab.json",
            "*.json"
        ]
        for pattern in tabulation_json_patterns:
            if pattern.startswith("*"):
                json_files = list(Path(".").glob(pattern))
                json_files = [f for f in json_files if "tab" in f.name.lower() and "dom" not in f.name.lower()]
            else:
                json_files = list(Path(".").glob(pattern))
            if json_files:
                latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
                results_files['tabulation_json'] = latest_file
                self.update_logs(f"Fichier tabulation trouvé: {latest_file}")
                break
        
        # Chercher d'autres fichiers de résultats
        csv_files = list(Path(".").glob("*.csv"))
        if csv_files:
            results_files['csv_files'] = csv_files
        return results_files

    def load_dom_results(self, dom_file_path):
        """Charge les résultats DOM depuis un fichier JSON"""
        if not dom_file_path or not dom_file_path.exists():
            return None
        try:
            with open(dom_file_path, 'r', encoding='utf-8') as f:
                dom_results = json.load(f)
            self.update_logs(f"Résultats DOM chargés depuis: {dom_file_path}")
            return dom_results
        except Exception as e:
            self.update_logs(f"Erreur lors du chargement DOM: {str(e)}")
            return None

    def load_tabulation_results(self, tabulation_file_path):
        """Charge les résultats de tabulation depuis un fichier JSON"""
        if not tabulation_file_path or not tabulation_file_path.exists():
            return None
        try:
            with open(tabulation_file_path, 'r', encoding='utf-8') as f:
                tabulation_results = json.load(f)
            self.update_logs(f"Résultats tabulation chargés depuis: {tabulation_file_path}")
            return tabulation_results
        except Exception as e:
            self.update_logs(f"Erreur lors du chargement tabulation: {str(e)}")
            return None

    def load_other_results(self, results_files):
        """Charge les autres types de résultats"""
        other_results = {}
        # Charger les résultats CSV si disponibles
        if 'csv_files' in results_files:
            for csv_file in results_files['csv_files']:
                try:
                    filename = csv_file.name.lower()
                    if 'contrast' in filename:
                        other_results['contrast'] = self.parse_csv_results(csv_file, 'contrast')
                    elif 'image' in filename:
                        other_results['image'] = self.parse_csv_results(csv_file, 'image')
                    elif 'tab' in filename:
                        other_results['tab'] = self.parse_csv_results(csv_file, 'tab')
                    elif 'screen' in filename:
                        other_results['screen'] = self.parse_csv_results(csv_file, 'screen')
                    self.update_logs(f"Résultats chargés depuis: {csv_file}")
                except Exception as e:
                    self.update_logs(f"Erreur lors du chargement de {csv_file}: {str(e)}")
        return other_results

    def parse_csv_results(self, csv_file, module_type):
        """Parse un fichier CSV pour extraire les résultats"""
        try:
            results = {'issues': []}
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    issue = {
                        'type': row.get('Type', 'N/A'),
                        'message': row.get('Message', 'N/A'),
                        'severity': row.get('Sévérité', 'medium')
                    }
                    results['issues'].append(issue)
            return results
        except Exception as e:
            self.update_logs(f"Erreur lors du parsing CSV {csv_file}: {str(e)}")
            return {'issues': []}

    def show_results_info(self):
        """Affiche les informations sur les fichiers de résultats disponibles"""
        try:
            results_files = self.find_latest_results()
            if not results_files:
                messagebox.showinfo("Information", "Aucun fichier de résultats trouvé.")
                return
            info_text = "Fichiers de résultats disponibles:\n\n"
            if 'dom_json' in results_files:
                dom_file = results_files['dom_json']
                mod_time = datetime.fromtimestamp(dom_file.stat().st_mtime)
                info_text += f"📄 DOM JSON: {dom_file.name}\n"
                info_text += f"   Modifié: {mod_time.strftime('%d/%m/%Y %H:%M:%S')}\n\n"
            if 'tabulation_json' in results_files:
                tabulation_file = results_files['tabulation_json']
                mod_time = datetime.fromtimestamp(tabulation_file.stat().st_mtime)
                info_text += f"📄 Tabulation JSON: {tabulation_file.name}\n"
                info_text += f"   Modifié: {mod_time.strftime('%d/%m/%Y %H:%M:%S')}\n\n"
            if 'csv_files' in results_files:
                info_text += "📊 Fichiers CSV:\n"
                for csv_file in results_files['csv_files']:
                    mod_time = datetime.fromtimestamp(csv_file.stat().st_mtime)
                    info_text += f"   • {csv_file.name} ({mod_time.strftime('%d/%m/%Y %H:%M:%S')})\n"
            messagebox.showinfo("Fichiers de résultats", info_text)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la lecture des fichiers: {str(e)}")

    def create_dom_table(self, dataframe):
        """Crée un tableau PandasTable avec des options sécurisées pour éviter le bug atdivider"""
        # Détruire le tableau existant s'il y en a un
        if self.dom_ptable:
            self.dom_ptable.destroy()
        
        # Créer le tableau avec des options qui permettent le tri et le filtrage
        self.dom_ptable = Table(
            self.dom_table_canvas, 
            dataframe=dataframe, 
            showtoolbar=True, 
            showstatusbar=True,
            width=800,
            height=400,
            cellwidth=100,
            cellheight=25,
            thefont=('Arial', 10),
            rowheight=25,
            colselectedcolor='lightblue',
            rowselectedcolor='lightblue',
            selectedcolor='lightblue',
            read_only=True,  # Désactiver l'édition pour éviter les problèmes
            multiple_cell_selection=False,  # Désactiver la sélection multiple
            enable_menus=True,  # Activer les menus pour le tri
            enable_drag_drop=False,  # Désactiver le drag & drop
            enable_undo=False,  # Désactiver l'undo
            enable_clipboard=False,  # Désactiver le presse-papiers
            show_index=False,  # Masquer l'index
            show_vertical_scrollbar=True,
            show_horizontal_scrollbar=True
        )
        
        # Patch pour le bug atdivider - approche plus complète
        self.patch_atdivider_bug()
        
        # Configurer les événements de tri
        self.setup_sorting_events()
        
        self.dom_ptable.show()
        return self.dom_ptable
    
    def patch_atdivider_bug(self):
        """Applique un patch pour éviter le bug atdivider"""
        try:
            # Patch simple : ajouter l'attribut manquant si nécessaire
            if hasattr(self.dom_ptable, 'tableheader'):
                for child in self.dom_ptable.tableheader.winfo_children():
                    if hasattr(child, '__class__') and 'ColumnHeader' in str(child.__class__):
                        if not hasattr(child, 'atdivider'):
                            child.atdivider = 0
                        if not hasattr(child, 'atseparator'):
                            child.atseparator = 0
        except Exception as e:
            self.update_logs(f"Patch atdivider échoué: {e}")
    
    def setup_sorting_events(self):
        """Configure les événements de tri pour les colonnes"""
        try:
            if hasattr(self.dom_ptable, 'tableheader'):
                # Configurer le tri par clic sur l'en-tête
                self.dom_ptable.tableheader.bind('<Button-1>', self.handle_header_click)
                
                # Configurer les événements pour chaque colonne
                for i, child in enumerate(self.dom_ptable.tableheader.winfo_children()):
                    if hasattr(child, 'bind'):
                        child.bind('<Button-1>', lambda e, col=i: self.handle_column_click(e, col))
                        child.bind('<Double-Button-1>', lambda e, col=i: self.handle_column_double_click(e, col))
        except Exception as e:
            self.update_logs(f"Configuration des événements de tri échouée: {e}")
    
    def handle_header_click(self, event):
        """Gestionnaire pour le clic sur l'en-tête du tableau"""
        try:
            # Obtenir la position du clic
            x = event.x
            # Trouver la colonne correspondante
            column_index = self.get_column_from_x_position(x)
            if column_index is not None:
                self.sort_column(column_index)
        except Exception as e:
            self.update_logs(f"Erreur dans handle_header_click: {e}")
    
    def handle_column_click(self, event, column_index):
        """Gestionnaire pour le clic sur une colonne spécifique"""
        try:
            self.sort_column(column_index)
        except Exception as e:
            self.update_logs(f"Erreur dans handle_column_click: {e}")
    
    def handle_column_double_click(self, event, column_index):
        """Gestionnaire pour le double-clic sur une colonne"""
        try:
            # Double-clic pour tri inverse
            self.sort_column(column_index, reverse=True)
        except Exception as e:
            self.update_logs(f"Erreur dans handle_column_double_click: {e}")
    
    def get_column_from_x_position(self, x):
        """Détermine l'index de la colonne à partir de la position X"""
        try:
            if not self.dom_df.empty:
                # Calculer la largeur approximative de chaque colonne
                total_width = 800  # Largeur du tableau
                col_width = total_width / len(self.dom_df.columns)
                column_index = int(x / col_width)
                if 0 <= column_index < len(self.dom_df.columns):
                    return column_index
        except Exception as e:
            self.update_logs(f"Erreur dans get_column_from_x_position: {e}")
        return None
    
    def sort_column(self, column_index, reverse=False):
        """Trie les données par colonne"""
        try:
            if not self.dom_df.empty and 0 <= column_index < len(self.dom_df.columns):
                column_name = self.dom_df.columns[column_index]
                self.update_logs(f"Tri de la colonne: {column_name}")
                
                # Utiliser les données filtrées si elles existent, sinon les données complètes
                data_to_sort = self.filtered_dom_data if self.filtered_dom_data else self.dom_data
                
                if data_to_sort:
                    # Mapping colonne -> clé JSON
                    column_mapping = {
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
                    }
                    
                    column_key = column_mapping.get(column_name, 'tag')
                    
                    # Tri
                    sorted_data = sorted(data_to_sort,
                        key=lambda x: str(x.get(column_key, '')).lower() if not isinstance(x.get(column_key, ''), dict) else str(x.get(column_key, '')),
                        reverse=reverse)
                    
                    # Préparer les données triées
                    df = pd.DataFrame([self.get_dom_row_dict(element) for element in sorted_data])
                    self.dom_df = df
                    self.filtered_dom_data = sorted_data
                    
                    # Recharger le tableau
                    self.create_dom_table(self.dom_df)
        except Exception as e:
            self.update_logs(f"Erreur dans sort_column: {e}")

    def display_tabulation_results(self, tabulation_results):
        """Affiche les résultats de l'analyse tabulaire"""
        if not tabulation_results:
            self.tabulation_stats_text.delete(1.0, tk.END)
            self.tabulation_stats_text.insert(1.0, "Aucun résultat d'analyse tabulaire disponible")
            self.update_logs("Aucun résultat tabulaire à afficher")
            return
        
        # Vérifier la structure des résultats
        if not isinstance(tabulation_results, list):
            self.tabulation_stats_text.delete(1.0, tk.END)
            self.tabulation_stats_text.insert(1.0, f"Format de résultats tabulaire invalide: {type(tabulation_results)}")
            self.update_logs(f"Format de résultats tabulaire invalide: {type(tabulation_results)}")
            return
        
        # Afficher les statistiques
        total_elements = len(tabulation_results)
        elements_with_accessible_names = len([r for r in tabulation_results if r.get('accessible_name', {}).get('name')])
        elements_with_aria = len([r for r in tabulation_results if r.get('aria_attributes')])
        visible_elements = len([r for r in tabulation_results if r.get('is_visible', False)])
        
        stats_text = f"""
        Éléments totaux: {total_elements}
        Éléments avec nom accessible: {elements_with_accessible_names}
        Éléments avec attributs ARIA: {elements_with_aria}
        Éléments visibles: {visible_elements}
        """
        self.tabulation_stats_text.delete(1.0, tk.END)
        self.tabulation_stats_text.insert(1.0, stats_text)
        
        # Logs pour le débogage
        self.update_logs(f"Résultats tabulaire: {total_elements} éléments")
        
        # Charger les données dans le tableau
        if tabulation_results:
            self.load_tabulation_data(tabulation_results)
        else:
            self.update_logs("Aucun élément tabulaire trouvé dans les résultats")
            # Effacer le tableau
            if self.tabulation_ptable:
                self.tabulation_ptable.destroy()
            self.tabulation_ptable = None
            self.tabulation_df = pd.DataFrame()
    
    def load_tabulation_data(self, elements):
        """Charge les données tabulaires dans le tableau PandasTable"""
        # Conversion en DataFrame
        df = pd.DataFrame([self.get_tabulation_row_dict(element) for element in elements])
        self.tabulation_df = df
        self.tabulation_data = elements
        self.filtered_tabulation_data = elements
        self.update_logs(f"Chargement de {len(elements)} éléments tabulaires dans le tableau")
        
        # Affichage dans PandasTable
        self.create_tabulation_table(self.tabulation_df)
        self.update_tabulation_filters()
    
    def update_tabulation_filters(self):
        """Met à jour les options de filtrage basées sur les données disponibles"""
        if not self.tabulation_data:
            return
        
        # Mettre à jour les tags disponibles
        tags = set()
        for element in self.tabulation_data:
            tag = element.get('tag', '').lower()
            if tag:
                tags.add(tag)
        
        tag_values = ["Tous"] + sorted(list(tags))
        self.tabulation_tag_filter_combo['values'] = tag_values
    
    def filter_tabulation_data(self, event=None):
        """Filtre les données tabulaires selon les critères sélectionnés"""
        if not self.tabulation_data:
            return
        
        # Effacer le tableau
        if self.tabulation_ptable:
            self.tabulation_ptable.destroy()
        self.tabulation_ptable = None
        self.tabulation_df = pd.DataFrame()
        
        # Appliquer les filtres
        search_term = self.tabulation_search_var.get().lower()
        tag_filter = self.tabulation_tag_filter_var.get()
        visibility_filter = self.tabulation_visibility_filter_var.get()
        filtered_data = []
        
        for element in self.tabulation_data:
            # Filtre de recherche
            if search_term:
                searchable_text = f"{element.get('tag', '')} {element.get('text', '')} {element.get('xpath', '')} {element.get('accessible_name', {}).get('name', '')}".lower()
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
        
        # Préparer les données filtrées
        df = pd.DataFrame([self.get_tabulation_row_dict(element) for element in filtered_data])
        self.tabulation_df = df
        self.filtered_tabulation_data = filtered_data
        
        # Affichage dans PandasTable
        self.create_tabulation_table(self.tabulation_df)
    
    def reset_tabulation_filters(self):
        """Réinitialise tous les filtres tabulaires"""
        self.tabulation_search_var.set('')
        self.tabulation_tag_filter_var.set('')
        self.tabulation_visibility_filter_var.set('Tous')
        # Recharger toutes les données
        if self.tabulation_data:
            self.load_tabulation_data(self.tabulation_data)
    
    def export_tabulation_csv(self):
        """Exporte les données tabulaires en CSV"""
        if self.tabulation_df.empty:
            messagebox.showwarning("Export", "Aucune donnée tabulaire à exporter")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Exporter les données tabulaires en CSV"
        )
        
        if filename:
            try:
                self.tabulation_df.to_csv(filename, index=False, encoding='utf-8')
                messagebox.showinfo("Export", f"Données tabulaires exportées vers {filename}")
                self.update_logs(f"Export CSV tabulaire: {filename}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'export: {str(e)}")
                self.update_logs(f"Erreur export CSV tabulaire: {str(e)}")
    
    def export_tabulation_json(self):
        """Exporte les données tabulaires en JSON"""
        if not self.tabulation_data:
            messagebox.showwarning("Export", "Aucune donnée tabulaire à exporter")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Exporter les données tabulaires en JSON"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.tabulation_data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Export", f"Données tabulaires exportées vers {filename}")
                self.update_logs(f"Export JSON tabulaire: {filename}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'export: {str(e)}")
                self.update_logs(f"Erreur export JSON tabulaire: {str(e)}")
    
    def get_tabulation_row_dict(self, element):
        """Convertit un élément tabulaire en dictionnaire pour le DataFrame"""
        # Construire le rôle ARIA complet avec les rôles parents si présents
        aria_role = element.get('aria_attributes', {}).get('role', element.get('aria_properties', {}).get('Rôle', ''))
        parent_roles = element.get('parent_aria_roles', '')
        if parent_roles and aria_role and aria_role != 'non défini':
            full_role = f"{aria_role} (parents: {parent_roles})"
        elif parent_roles:
            full_role = f"parents: {parent_roles}"
        else:
            full_role = aria_role if aria_role else ''
        
        return {
            'Index': element.get('tab_index', element.get('focus_order', '')),
            'Tag': element.get('tag', ''),
            'Texte': element.get('text', '')[:50] + '...' if len(element.get('text', '')) > 50 else element.get('text', ''),
            'Alt Image': element.get('image_alt', ''),  # Attribut alt de l'image associée au lien
            'XPath': element.get('xpath', element.get('element_id', '')),
            'Nom Accessible': element.get('accessible_name', {}).get('name', ''),
            'Source Nom': element.get('accessible_name', {}).get('source', ''),
            'Rôle ARIA': full_role,  # Rôle ARIA avec rôles parents si présents
            'Rôles ARIA Parents': parent_roles,  # Rôles ARIA des éléments parents séparément
            'ID': element.get('basic_attributes', {}).get('id', ''),
            'Classe': element.get('basic_attributes', {}).get('class', ''),
            'Visible': 'Oui' if element.get('is_visible', False) else 'Non',
            'Activé': 'Oui' if element.get('is_enabled', False) else 'Non',
            'Position X': element.get('position', {}).get('x', 0),
            'Position Y': element.get('position', {}).get('y', 0),
            'Largeur': element.get('position', {}).get('width', 0),
            'Hauteur': element.get('position', {}).get('height', 0),
            'Capture 1': element.get('screenshots', {}).get('immediate', ''),
            'Capture 2': element.get('screenshots', {}).get('delayed', '')
        }
    
    def create_tabulation_table(self, dataframe):
        """Crée le tableau PandasTable pour les données tabulaires"""
        try:
            # Nettoyer le canvas
            for widget in self.tabulation_table_canvas.winfo_children():
                widget.destroy()
            
            if dataframe.empty:
                # Afficher un message si pas de données
                no_data_label = ttk.Label(self.tabulation_table_canvas, 
                                        text="Aucune donnée tabulaire disponible",
                                        font=('Segoe UI', 12))
                no_data_label.pack(expand=True)
                return
            
            # Créer le tableau PandasTable
            from pandastable import Table
            self.tabulation_ptable = Table(self.tabulation_table_canvas, dataframe=dataframe, showtoolbar=False, showstatusbar=False)
            self.tabulation_ptable.show()
            
            # Appliquer le patch pour éviter le bug atdivider
            self.patch_atdivider_bug()
            
            # Configurer les événements de tri
            self.setup_tabulation_sorting_events()
            
            self.update_logs(f"Tableau tabulaire créé avec {len(dataframe)} lignes")
            
        except Exception as e:
            self.update_logs(f"Erreur lors de la création du tableau tabulaire: {str(e)}")
            # Afficher un message d'erreur
            error_label = ttk.Label(self.tabulation_table_canvas, 
                                  text=f"Erreur lors de la création du tableau: {str(e)}",
                                  font=('Segoe UI', 10),
                                  foreground='red')
            error_label.pack(expand=True)
    
    def setup_tabulation_sorting_events(self):
        """Configure les événements de tri pour le tableau tabulaire"""
        if not self.tabulation_ptable:
            return
        
        # Lier les événements de clic sur les en-têtes
        self.tabulation_ptable.bind('<Button-1>', self.handle_tabulation_header_click)
    
    def handle_tabulation_header_click(self, event):
        """Gère les clics sur les en-têtes du tableau tabulaire"""
        if not self.tabulation_ptable:
            return
        
        # Obtenir la position du clic
        x = event.x
        column_index = self.get_tabulation_column_from_x_position(x)
        
        if column_index is not None:
            # Trier la colonne
            self.sort_tabulation_column(column_index)
    
    def get_tabulation_column_from_x_position(self, x):
        """Détermine la colonne à partir de la position X du clic"""
        if not self.tabulation_ptable or self.tabulation_df.empty:
            return None
        
        # Calculer la largeur approximative des colonnes
        total_width = self.tabulation_table_canvas.winfo_width()
        num_columns = len(self.tabulation_df.columns)
        column_width = total_width / num_columns
        
        # Déterminer la colonne
        column_index = int(x / column_width)
        
        if 0 <= column_index < num_columns:
            return column_index
        
        return None
    
    def sort_tabulation_column(self, column_index, reverse=False):
        """Trie une colonne du tableau tabulaire"""
        if not self.tabulation_ptable or self.tabulation_df.empty:
            return
        
        try:
            # Obtenir le nom de la colonne
            column_name = self.tabulation_df.columns[column_index]
            
            # Trier le DataFrame
            self.tabulation_df = self.tabulation_df.sort_values(by=column_name, ascending=not reverse)
            
            # Mettre à jour le tableau
            self.create_tabulation_table(self.tabulation_df)
            
            self.update_logs(f"Tri de la colonne tabulaire '{column_name}' {'décroissant' if reverse else 'croissant'}")
            
        except Exception as e:
            self.update_logs(f"Erreur lors du tri tabulaire: {str(e)}")

def main():
    """Fonction principale"""
    root = tk.Tk()
    app = RGAAWebCheckerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 