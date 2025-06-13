import markdown
import pdfkit
import os

class ReportGenerator:
    def __init__(self, scenario, output_dir='reports'):
        self.scenario = scenario
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_markdown(self):
        md_content = f"""# Rapport d'Analyse d'Accessibilité

## Informations générales
- **URL analysée**: {self.scenario.get('base_url', '-')}
- **Date d'analyse**: {self.scenario.get('start_time', '-')}

## Statistiques
- **Pages visitées**: {len(self.scenario.get('pages_visited', []))}
- **Liens accessibles via tabulation**: {len(self.scenario.get('tab_accessible_urls', []))}
- **Images analysées**: {self.scenario.get('images_info', '').count('|') - 1}

## Résultats détaillés
{self.scenario.get('accessibility_info', '')}
{self.scenario.get('tab_order_info', '')}
{self.scenario.get('images_info', '')}
"""
        md_path = os.path.join(self.output_dir, 'rapport_accessibilite.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        return md_path

    def convert_to_pdf(self, md_path):
        try:
            # Lecture du fichier avec gestion des erreurs d'encodage
            with open(md_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            html = markdown.markdown(content)
            html_path = md_path.replace('.md', '.html')
            
            # Ajout de la déclaration d'encodage dans le HTML
            html = f'<!DOCTYPE html>\n<html>\n<head>\n<meta charset="UTF-8">\n</head>\n<body>\n{html}\n</body>\n</html>'
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)
                
            pdf_path = md_path.replace('.md', '.pdf')
            pdfkit.from_file(html_path, pdf_path)
            return pdf_path
        except Exception as e:
            print(f"Erreur lors de la conversion : {str(e)}")
            raise
