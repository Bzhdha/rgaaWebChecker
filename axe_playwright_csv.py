import asyncio
from playwright.async_api import async_playwright
import requests
import csv
import os
import tempfile

AXE_CDN = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.3/axe.min.js"

async def run_axe_analysis(url):
    # Télécharger le script axe-core
    axe_script = requests.get(AXE_CDN).text
    
    # Créer un fichier temporaire pour axe-core
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as temp_file:
        temp_file.write(axe_script)
        temp_file_path = temp_file.name

    try:
        async with async_playwright() as p:
            # Configuration du navigateur pour ressembler à un navigateur normal
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--window-size=1920,1080'
                ]
            )
            
            # Configuration du contexte avec des en-têtes réalistes
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                locale='fr-FR',
                timezone_id='Europe/Paris',
                geolocation={'latitude': 48.8566, 'longitude': 2.3522},
                permissions=['geolocation']
            )
            
            # Ajout d'en-têtes HTTP supplémentaires
            await context.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            })
            
            page = await context.new_page()
            
            # Attendre que la page soit complètement chargée
            await page.goto(url, wait_until='networkidle')
            
            # Attendre un peu plus pour s'assurer que tout est bien chargé
            await page.wait_for_load_state('domcontentloaded')
            
            # Injecter axe-core via un fichier externe
            await page.add_script_tag(path=temp_file_path)
            
            # Exécuter l'analyse axe
            result = await page.evaluate("""
                async () => {
                    return await axe.run();
                }
            """)
            
            await browser.close()
            return result
            
    finally:
        # Nettoyage du fichier temporaire
        try:
            os.unlink(temp_file_path)
        except:
            pass

def export_violations_to_csv(violations, filename="axe_violations.csv"):
    with open(filename, mode='w', encoding='utf-8-sig', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        # En-tête avec plus d'informations
        writer.writerow([
            "Règle", 
            "Impact", 
            "Résumé", 
            "Aide", 
            "Sélecteur", 
            "Résumé de l'échec",
            "HTML concerné",
            "Tags concernés",
            "Attributs concernés",
            "Recommandations",
            "Critères WCAG concernés"
        ])
        
        for v in violations:
            for node in v['nodes']:
                # Extraction des informations HTML
                html = node.get('html', '')
                tags = []
                attributes = []
                
                # Analyse des attributs et tags
                if 'data' in node:
                    if 'tags' in node['data']:
                        tags = node['data']['tags']
                    if 'attributes' in node['data']:
                        attributes = [f"{k}={v}" for k, v in node['data']['attributes'].items()]
                
                # Extraction des recommandations
                recommendations = []
                if 'any' in node:
                    recommendations.extend([check['message'] for check in node['any']])
                if 'all' in node:
                    recommendations.extend([check['message'] for check in node['all']])
                if 'none' in node:
                    recommendations.extend([check['message'] for check in node['none']])
                
                # Extraction des critères WCAG
                wcag_criteria = []
                if 'tags' in v:
                    wcag_criteria = [tag for tag in v['tags'] if tag.startswith('wcag')]
                
                writer.writerow([
                    v['id'],
                    v['impact'],
                    v['description'],
                    v['helpUrl'],
                    ', '.join(node['target']),
                    node.get('failureSummary', ''),
                    html,
                    ', '.join(tags),
                    ', '.join(attributes),
                    ' | '.join(recommendations),
                    ', '.join(wcag_criteria)
                ])

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage : python axe_playwright_csv.py <URL>")
        sys.exit(1)
    url = sys.argv[1]
    result = asyncio.run(run_axe_analysis(url))
    print(f"Nombre de violations détectées : {len(result['violations'])}")
    export_violations_to_csv(result['violations'])
    print("Export CSV terminé : axe_violations.csv") 