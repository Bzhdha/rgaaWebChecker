from selenium.webdriver.common.by import By
from selenium.common.exceptions import JavascriptException
from utils.color_utils import calculate_contrast_ratio

class ContrastChecker:
    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger

    def run(self):
        self.logger.info("\nAnalyse des contrastes WCAG en cours...")
        elements = self.driver.find_elements(By.XPATH, "//*[text() or @alt or @title]")
        contrast_report = []
        for element in elements:
            try:
                color = self.driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).color;", element)
                background = self.driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).backgroundColor;", element)
                ratio = calculate_contrast_ratio(color, background)
                if ratio < 4.5:
                    contrast_report.append(f"Contraste insuffisant: {element.tag_name}, texte: {element.text}, ratio: {ratio:.2f}")
            except JavascriptException:
                continue
        if contrast_report:
            self.logger.warning("\nRapport de contrastes insuffisants:")
            for line in contrast_report:
                self.logger.warning(line)
        else:
            self.logger.info("Aucun contraste insuffisant détecté.")
