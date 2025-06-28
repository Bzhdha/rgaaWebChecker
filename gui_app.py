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
            
            # Crawler
            crawler = AccessibilityCrawler(self.config, self.logger)
            crawler.set_driver(driver)
            
            # Exécuter l'analyse
            crawler.crawl()
            # Après l'analyse, générer un rapport ou afficher un message
            self.root.after(0, lambda: self.update_logs("Analyse terminée. Rapport généré dans les logs ou le dossier de sortie."))
            # Optionnel : appeler self.process_results({}) pour vider/mettre à jour l'affichage
            self.root.after(0, lambda: self.process_results({}))
            
        except ImportError as e:
            # Erreur d'import de module
            error_msg = f"Module manquant: {str(e)}\n\nVérifiez que tous les modules sont installés:\npip install -r requirements.txt"
            self.root.after(0, lambda: self.handle_analysis_error(error_msg))
        except Exception as e:
            # Capturer l'erreur dans une variable locale pour éviter le problème de scope
            error_msg = str(e)
            self.root.after(0, lambda: self.handle_analysis_error(error_msg))
        finally:
            self.root.after(0, self.analysis_finished)
    
    def process_results(self, results):
        """Traite et affiche les résultats"""
        self.results_data = results
        
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
        
        for module_results in results.values():
            if isinstance(module_results, list):
                stats['total_issues'] += len(module_results)
                for issue in module_results:
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
            if isinstance(module_results, list):
                for issue in module_results:
                    self.results_tree.insert('', tk.END, values=(
                        module_name,
                        issue.get('type', 'N/A'),
                        issue.get('message', 'N/A'),
                        issue.get('severity', 'medium')
                    ))
    
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

def main():
    """Fonction principale"""
    root = tk.Tk()
    app = RGAAWebCheckerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 