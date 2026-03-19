from playwright.sync_api import sync_playwright


class PlaywrightDriverAdapter:
    """Adaptateur minimal pour exposer une API proche du driver existant."""

    def __init__(self, page):
        self.page = page

    def execute_script(self, script, *args):
        # Mapping direct vers evaluate Playwright.
        if args:
            # Le module titles n'utilise pas encore d'arguments JS; on garde ce garde-fou explicite.
            raise NotImplementedError("execute_script avec args n'est pas encore supporté par l'adaptateur Playwright.")
        return self.page.evaluate(script)

    @property
    def current_url(self):
        return self.page.url

    def save_screenshot(self, path):
        self.page.screenshot(path=path, full_page=False)
        return True


class PlaywrightCrawler:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

    def run(self):
        enabled = set(self.config.get_enabled_modules())
        if enabled != {"titles"}:
            raise ValueError(
                "Le moteur Playwright est actuellement implémenté pour le module 'titles' uniquement. "
                "Utilisez '--modules titles' ou '--engine selenium' en attendant la migration complète."
            )

        from modules.titles_analyzer import TitlesAnalyzer

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                locale="fr-FR",
                timezone_id="Europe/Paris",
            )
            page = context.new_page()
            page.goto(self.config.base_url, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")

            adapter = PlaywrightDriverAdapter(page)
            analyzer = TitlesAnalyzer(adapter, self.logger)
            result = analyzer.run()

            context.close()
            browser.close()
            return result
