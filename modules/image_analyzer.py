import os
import requests
from urllib.parse import urljoin, urlparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import hashlib
from pathlib import Path
import urllib3
import warnings
import logging
import csv
import codecs
from utils.log_utils import log_with_step

# Désactiver les avertissements SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ImageAnalyzer:
    def __init__(self, driver, logger, base_url, output_dir="site_images"):
        self.driver = driver
        self.logger = logger
        self.base_url = base_url
        self.output_dir = output_dir
        self.image_info_list = []
        self.detected_images = []
        
        # Créer le répertoire de sortie s'il n'existe pas
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def run(self):
        log_with_step(self.logger, logging.INFO, "IMAGES", "\nAnalyse des images du site...")
        
        try:
            # Vérifier que le driver est toujours valide
            if not self.driver:
                raise Exception("Le driver n'est pas initialisé")
            
            # Attendre que la page soit complètement chargée
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
            except Exception as e:
                log_with_step(self.logger, logging.WARNING, "IMAGES", f"Erreur lors de l'attente du chargement de la page: {str(e)}")
            
            # Récupérer toutes les images
            self.detected_images = self._get_all_images()
            total_images = len(self.detected_images)
            log_with_step(self.logger, logging.INFO, "IMAGES", f"Nombre total d'images détectées : {total_images}")
            
            if total_images == 0:
                log_with_step(self.logger, logging.WARNING, "IMAGES", "Aucune image n'a été détectée sur la page")
                return []
            
            # Analyser chaque image
            for index, image in enumerate(self.detected_images, 1):
                try:
                    # Vérifier si l'image est toujours valide
                    if not self._is_element_stale(image):
                        image_info = self._analyze_image(image)
                        if image_info:
                            self.image_info_list.append(image_info)
                            if image_info['src']:
                                self._save_image(image_info)
                        
                        # Afficher la progression
                        progress = (index / total_images) * 100
                        log_with_step(self.logger, logging.INFO, "IMAGES", f"Progression : {progress:.1f}% ({index}/{total_images})")
                    
                except Exception as e:
                    log_with_step(self.logger, logging.WARNING, "IMAGES", f"Erreur lors de l'analyse d'une image : {str(e)}")
                    continue
            
            # Sauvegarder le rapport d'analyse
            try:
                self._save_report()
            except Exception as e:
                log_with_step(self.logger, logging.ERROR, "IMAGES", f"Erreur lors de la sauvegarde du rapport : {str(e)}")
            
            # Afficher un résumé
            try:
                self._display_summary()
            except Exception as e:
                log_with_step(self.logger, logging.ERROR, "IMAGES", f"Erreur lors de l'affichage du résumé : {str(e)}")
            
            return self.image_info_list
            
        except Exception as e:
            log_with_step(self.logger, logging.ERROR, "IMAGES", f"Erreur lors de l'analyse des images : {str(e)}")
            return []

    def _is_element_stale(self, element):
        """Vérifie si l'élément est toujours valide"""
        try:
            element.tag_name
            return False
        except:
            return True

    def _get_all_images(self):
        """Récupère toutes les images de la page, y compris celles dans les balises picture, svg, etc."""
        images = []
        
        # Images standard
        images.extend(self.driver.find_elements(By.TAG_NAME, "img"))
        
        # Images dans les balises picture
        picture_elements = self.driver.find_elements(By.TAG_NAME, "picture")
        for picture in picture_elements:
            images.extend(picture.find_elements(By.TAG_NAME, "img"))
        
        # Images dans les SVG
        svg_elements = self.driver.find_elements(By.TAG_NAME, "svg")
        for svg in svg_elements:
            images.extend(svg.find_elements(By.TAG_NAME, "image"))
        
        # Images dans les canvas (si elles sont visibles)
        canvas_elements = self.driver.find_elements(By.TAG_NAME, "canvas")
        for canvas in canvas_elements:
            if canvas.is_displayed():
                images.append(canvas)
        
        # Images en arrière-plan (via CSS)
        elements_with_bg = self.driver.find_elements(By.CSS_SELECTOR, "[style*='background-image']")
        for element in elements_with_bg:
            if element.is_displayed():
                images.append(element)
        
        # Filtrer les doublons et les images invalides
        unique_images = []
        seen_srcs = set()
        
        for img in images:
            try:
                if not self._is_element_stale(img):
                    src = img.get_attribute('src')
                    if src and src not in seen_srcs:
                        seen_srcs.add(src)
                        unique_images.append(img)
            except:
                continue
        
        return unique_images

    def _analyze_image(self, image):
        """Analyse une image et retourne ses informations"""
        try:
            # Récupérer les informations de base
            image_info = {
                'tag': image.tag_name,
                'src': image.get_attribute('src'),
                'alt': image.get_attribute('alt'),
                'title': image.get_attribute('title'),
                'aria_label': image.get_attribute('aria-label'),
                'aria_describedby': image.get_attribute('aria-describedby'),
                'aria_hidden': image.get_attribute('aria-hidden'),
                'role': image.get_attribute('role'),
                'width': image.get_attribute('width'),
                'height': image.get_attribute('height'),
                'loading': image.get_attribute('loading'),
                'srcset': image.get_attribute('srcset'),
                'sizes': image.get_attribute('sizes'),
                'class': image.get_attribute('class'),
                'id': image.get_attribute('id'),
                'style': image.get_attribute('style'),
                'position': self._get_element_position(image),
                'is_background': self._is_background_image(image),
                'local_path': '',  # Sera rempli lors de la sauvegarde
                'status': 'pending',  # Statut de l'analyse
                'is_visible': False,  # État de visibilité
                'visibility_reason': ''  # Raison de la non-visibilité
            }
            
            # Vérifier la visibilité
            try:
                if image.is_displayed():
                    image_info['is_visible'] = True
                else:
                    image_info['visibility_reason'] = 'Non affichée (display: none ou visibility: hidden)'
            except:
                image_info['visibility_reason'] = 'Erreur lors de la vérification de la visibilité'
            
            # Vérifier les dimensions
            try:
                size = image.size
                if size['width'] == 0 or size['height'] == 0:
                    image_info['visibility_reason'] = 'Dimensions nulles'
            except:
                image_info['visibility_reason'] = 'Erreur lors de la vérification des dimensions'
            
            # Vérifier l'opacité
            try:
                opacity = image.value_of_css_property('opacity')
                if opacity == '0':
                    image_info['visibility_reason'] = 'Opacité à 0'
            except:
                pass
            
            # Vérifier si l'image est dans le viewport
            try:
                if image_info['is_visible']:
                    viewport_height = self.driver.execute_script('return window.innerHeight')
                    viewport_width = self.driver.execute_script('return window.innerWidth')
                    location = image.location
                    size = image.size
                    
                    if (location['x'] + size['width'] < 0 or 
                        location['y'] + size['height'] < 0 or
                        location['x'] > viewport_width or
                        location['y'] > viewport_height):
                        image_info['visibility_reason'] = 'Hors du viewport'
            except:
                pass
            
            return image_info
            
        except Exception as e:
            log_with_step(self.logger, logging.WARNING, "IMAGES", f"Erreur lors de l'analyse d'une image : {str(e)}")
            # Retourner une valeur par défaut au lieu de None
            return {
                'tag': 'img',
                'src': '',
                'alt': '',
                'title': '',
                'aria_label': '',
                'aria_describedby': '',
                'aria_hidden': '',
                'role': '',
                'width': '',
                'height': '',
                'loading': '',
                'srcset': '',
                'sizes': '',
                'class': '',
                'id': '',
                'style': '',
                'position': {'x': 0, 'y': 0, 'width': 0, 'height': 0},
                'is_background': False,
                'local_path': '',
                'status': 'error',
                'is_visible': False,
                'visibility_reason': 'Erreur lors de l\'analyse'
            }

    def _get_element_position(self, element):
        """Récupère la position de l'élément dans la page"""
        try:
            location = element.location
            size = element.size
            return {
                'x': location['x'],
                'y': location['y'],
                'width': size['width'],
                'height': size['height']
            }
        except:
            # Retourner une valeur par défaut au lieu de None
            return {'x': 0, 'y': 0, 'width': 0, 'height': 0}

    def _is_background_image(self, element):
        """Vérifie si l'image est utilisée comme arrière-plan"""
        try:
            style = element.get_attribute('style')
            return 'background-image' in style if style else False
        except:
            return False

    def _save_image(self, image_info):
        """Sauvegarde l'image localement"""
        if not image_info['src']:
            image_info['status'] = 'no_source'
            return
            
        try:
            # Construire l'URL complète
            image_url = urljoin(self.base_url, image_info['src'])
            
            # Générer un nom de fichier unique
            file_hash = hashlib.md5(image_url.encode()).hexdigest()
            file_extension = os.path.splitext(urlparse(image_url).path)[1] or '.jpg'
            filename = f"{file_hash}{file_extension}"
            local_path = os.path.join(self.output_dir, filename)
            
            # Télécharger l'image en désactivant la vérification SSL
            session = requests.Session()
            session.verify = False
            response = session.get(image_url, stream=True, timeout=10)
            
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                image_info['local_path'] = local_path
                image_info['status'] = 'success'
            else:
                image_info['status'] = f'error_http_{response.status_code}'
                
        except requests.exceptions.Timeout:
            image_info['status'] = 'error_timeout'
        except requests.exceptions.RequestException as e:
            image_info['status'] = f'error_request_{str(e)}'
        except Exception as e:
            image_info['status'] = f'error_unknown_{str(e)}'

    def _save_report(self):
        """Sauvegarde le rapport d'analyse dans un fichier CSV"""
        report_path = os.path.join(self.output_dir, 'image_analysis_report.csv')
        
        # Définir les en-têtes du CSV
        headers = [
            'Index',
            'URL Source',
            'Chemin Local',
            'Balise',
            'Alt',
            'Title',
            'Aria Label',
            'Aria Describedby',
            'Aria Hidden',
            'Role',
            'Largeur',
            'Hauteur',
            'Loading',
            'Srcset',
            'Sizes',
            'Classe',
            'ID',
            'Style',
            'Position X',
            'Position Y',
            'Largeur Affichée',
            'Hauteur Affichée',
            'Est Arrière-plan',
            'Statut'
        ]
        
        try:
            # Ouvrir le fichier en mode écriture avec l'encodage ANSI
            with codecs.open(report_path, 'w', encoding='cp1252', errors='replace') as f:
                writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_ALL)
                
                # Écrire les en-têtes
                writer.writerow(headers)
                
                # Écrire les données pour chaque image
                for index, info in enumerate(self.image_info_list, 1):
                    row = [
                        index,
                        info.get('src', ''),
                        info.get('local_path', ''),
                        info.get('tag', ''),
                        info.get('alt', ''),
                        info.get('title', ''),
                        info.get('aria_label', ''),
                        info.get('aria_describedby', ''),
                        info.get('aria_hidden', ''),
                        info.get('role', ''),
                        info.get('width', ''),
                        info.get('height', ''),
                        info.get('loading', ''),
                        info.get('srcset', ''),
                        info.get('sizes', ''),
                        info.get('class', ''),
                        info.get('id', ''),
                        info.get('style', ''),
                    ]
                    
                    # Ajouter les informations de position
                    position = info.get('position', {})
                    row.extend([
                        position.get('x', '') if position else '',
                        position.get('y', '') if position else '',
                        position.get('width', '') if position else '',
                        position.get('height', '') if position else ''
                    ])
                    
                    # Ajouter les informations supplémentaires
                    row.extend([
                        'Oui' if info.get('is_background') else 'Non',
                        info.get('status', '')
                    ])
                    
                    writer.writerow(row)
                
            log_with_step(self.logger, logging.INFO, "IMAGES", f"Rapport d'analyse sauvegardé dans : {report_path}")
            
        except Exception as e:
            log_with_step(self.logger, logging.ERROR, "IMAGES", f"Erreur lors de la sauvegarde du rapport CSV : {str(e)}")
            
            # En cas d'erreur, sauvegarder un rapport texte simple
            txt_report_path = os.path.join(self.output_dir, 'image_analysis_report.txt')
            with open(txt_report_path, 'w', encoding='utf-8') as f:
                f.write("=== Rapport d'analyse des images ===\n\n")
                for index, info in enumerate(self.image_info_list, 1):
                    f.write(f"Image {index}:\n")
                    for key, value in info.items():
                        if value:
                            f.write(f"  {key}: {value}\n")
                    f.write("\n")
            log_with_step(self.logger, logging.INFO, "IMAGES", f"Rapport texte de secours sauvegardé dans : {txt_report_path}")

    def _display_summary(self):
        """Affiche un résumé de l'analyse"""
        total_detected = len(self.detected_images)
        total_analyzed = len(self.image_info_list)
        downloaded = sum(1 for img in self.image_info_list if img['status'] == 'success')
        failed = sum(1 for img in self.image_info_list if img['status'] != 'success')
        visible = sum(1 for img in self.image_info_list if img['is_visible'])
        
        log_with_step(self.logger, logging.INFO, "IMAGES", "\nRésumé de l'analyse des images :")
        log_with_step(self.logger, logging.INFO, "IMAGES", f"Images détectées : {total_detected}")
        log_with_step(self.logger, logging.INFO, "IMAGES", f"Images analysées : {total_analyzed}")
        log_with_step(self.logger, logging.INFO, "IMAGES", f"Images visibles : {visible}")
        log_with_step(self.logger, logging.INFO, "IMAGES", f"Images téléchargées avec succès : {downloaded}")
        log_with_step(self.logger, logging.INFO, "IMAGES", f"Images en échec : {failed}")
        
        # Afficher les détails des échecs
        if failed > 0:
            log_with_step(self.logger, logging.INFO, "IMAGES", "\nDétails des échecs :")
            for img in self.image_info_list:
                if img['status'] != 'success':
                    log_with_step(self.logger, logging.INFO, "IMAGES", f"- {img['src']}: {img['status']}")
        
        # Afficher les images non analysées avec leur raison
        if total_detected > total_analyzed:
            log_with_step(self.logger, logging.INFO, "IMAGES", "\nImages non analysées :")
            analyzed_srcs = {img['src'] for img in self.image_info_list if img['src']}
            for img in self.detected_images:
                try:
                    src = img.get_attribute('src')
                    if src and src not in analyzed_srcs:
                        log_with_step(self.logger, logging.INFO, "IMAGES", f"- {src}")
                except:
                    continue
        
        # Afficher les détails de visibilité
        if total_analyzed > visible:
            log_with_step(self.logger, logging.INFO, "IMAGES", "\nDétails de visibilité des images :")
            for img in self.image_info_list:
                if not img['is_visible']:
                    log_with_step(self.logger, logging.INFO, "IMAGES", f"- {img['src']}: {img['visibility_reason']}") 