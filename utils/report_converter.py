import markdown
import pdfkit
import os
from datetime import datetime

class ReportConverter:
    def __init__(self, md_file):
        self.md_file = md_file
        self.output_dir = os.path.dirname(md_file)
        
    def convert_to_html(self):
        """Convertit le rapport Markdown en HTML"""
        try:
            # Lire le contenu Markdown
            with open(self.md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Convertir en HTML avec des extensions supplémentaires
            html_content = markdown.markdown(
                md_content,
                extensions=[
                    'tables',
                    'fenced_code',
                    'nl2br',
                    'sane_lists',
                    'attr_list',
                    'toc'
                ]
            )
            
            # Ajouter du style CSS amélioré
            styled_html = f"""
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Rapport d'Accessibilité</title>
                <style>
                    :root {{
                        --primary-color: #2c3e50;
                        --success-color: #27ae60;
                        --warning-color: #e67e22;
                        --error-color: #c0392b;
                        --border-color: #eee;
                        --background-color: #f9f9f9;
                    }}

                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        max-width: 1200px;
                        margin: 0 auto;
                        padding: 20px;
                        color: var(--primary-color);
                        background-color: var(--background-color);
                    }}

                    h1, h2, h3 {{
                        color: var(--primary-color);
                        margin-top: 1.5em;
                    }}

                    h1 {{
                        font-size: 2.5em;
                        border-bottom: 3px solid var(--border-color);
                        padding-bottom: 0.5em;
                        margin-bottom: 1em;
                    }}

                    h2 {{
                        font-size: 2em;
                        border-bottom: 2px solid var(--border-color);
                        padding-bottom: 0.3em;
                        margin-top: 1.5em;
                    }}

                    h3 {{
                        font-size: 1.5em;
                        margin-top: 1.2em;
                    }}

                    ul {{
                        list-style-type: none;
                        padding-left: 1.5em;
                        margin: 1em 0;
                    }}

                    li {{
                        margin: 0.5em 0;
                        padding: 0.3em 0;
                    }}

                    .element-section {{
                        background: white;
                        border-radius: 8px;
                        padding: 1.5em;
                        margin: 1em 0;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}

                    .info-section {{
                        margin: 1em 0;
                        padding: 1em;
                        background: #f8f9fa;
                        border-radius: 4px;
                    }}

                    .success {{
                        color: var(--success-color);
                        font-weight: bold;
                    }}

                    .warning {{
                        color: var(--warning-color);
                        font-weight: bold;
                    }}

                    .error {{
                        color: var(--error-color);
                        font-weight: bold;
                    }}

                    .attribute-list {{
                        display: grid;
                        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                        gap: 1em;
                        margin: 1em 0;
                    }}

                    .attribute-item {{
                        padding: 0.5em;
                        border: 1px solid var(--border-color);
                        border-radius: 4px;
                        background: white;
                    }}

                    .attribute-name {{
                        font-weight: bold;
                        color: var(--primary-color);
                    }}

                    .attribute-value {{
                        color: #666;
                    }}

                    @media print {{
                        body {{
                            background: white;
                        }}
                        .element-section {{
                            box-shadow: none;
                            border: 1px solid var(--border-color);
                        }}
                    }}

                    @media (max-width: 768px) {{
                        body {{
                            padding: 10px;
                        }}
                        .attribute-list {{
                            grid-template-columns: 1fr;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="content">
                    {html_content}
                </div>
                <script>
                    // Ajouter des classes aux éléments pour le style
                    document.addEventListener('DOMContentLoaded', function() {{
                        // Ajouter la classe element-section aux sections d'éléments
                        document.querySelectorAll('h2').forEach(h2 => {{
                            if (h2.textContent.startsWith('Élément')) {{
                                let section = document.createElement('div');
                                section.className = 'element-section';
                                h2.parentNode.insertBefore(section, h2.nextSibling);
                                while (h2.nextSibling && !h2.nextSibling.matches('h2')) {{
                                    section.appendChild(h2.nextSibling);
                                }}
                            }}
                        }});

                        // Ajouter la classe info-section aux sections d'informations
                        document.querySelectorAll('h3').forEach(h3 => {{
                            if (h3.textContent.includes('Informations') || h3.textContent.includes('Attributs')) {{
                                let section = document.createElement('div');
                                section.className = 'info-section';
                                h3.parentNode.insertBefore(section, h3.nextSibling);
                                while (h3.nextSibling && !h3.nextSibling.matches('h3')) {{
                                    section.appendChild(h3.nextSibling);
                                }}
                            }}
                        }});

                        // Formater les listes d'attributs
                        document.querySelectorAll('ul').forEach(ul => {{
                            if (ul.previousElementSibling && ul.previousElementSibling.matches('h3')) {{
                                ul.className = 'attribute-list';
                                ul.querySelectorAll('li').forEach(li => {{
                                    li.className = 'attribute-item';
                                    let text = li.textContent;
                                    if (text.includes(':')) {{
                                        let [name, value] = text.split(':', 1);
                                        li.innerHTML = `<span class="attribute-name">${{name}}:</span><span class="attribute-value">${{value}}</span>`;
                                    }}
                                }});
                            }}
                        }});
                    }});
                </script>
            </body>
            </html>
            """
            
            # Sauvegarder le fichier HTML
            html_file = self.md_file.replace('.md', '.html')
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(styled_html)
            
            return html_file
            
        except Exception as e:
            print(f"Erreur lors de la conversion en HTML : {str(e)}")
            return None

    def convert_to_pdf(self):
        """Convertit le rapport Markdown en PDF"""
        try:
            # D'abord convertir en HTML
            html_file = self.convert_to_html()
            if not html_file:
                return None
            
            # Options pour la conversion PDF
            options = {
                'page-size': 'A4',
                'margin-top': '20mm',
                'margin-right': '20mm',
                'margin-bottom': '20mm',
                'margin-left': '20mm',
                'encoding': 'UTF-8',
                'no-outline': None,
                'enable-local-file-access': None
            }
            
            # Convertir HTML en PDF
            pdf_file = self.md_file.replace('.md', '.pdf')
            pdfkit.from_file(html_file, pdf_file, options=options)
            
            return pdf_file
            
        except Exception as e:
            print(f"Erreur lors de la conversion en PDF : {str(e)}")
            return None 