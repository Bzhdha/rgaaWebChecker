import os
from utils.image_utils import simulate_daltonism
from utils.log_utils import log_with_step
import logging

class ColorSimulator:
    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger

    def run(self):
        log_with_step(self.logger, logging.INFO, "DALTONISME", "\nSimulation de daltonisme en cours...")
        screenshot = self.driver.get_screenshot_as_png()
        for mode in ['protanopia', 'deuteranopia', 'tritanopia']:
            simulated = simulate_daltonism(screenshot, mode)
            file_path = f"reports/simulation_{mode}.png"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb') as f:
                f.write(simulated)
            log_with_step(self.logger, logging.INFO, "DALTONISME", f"Simulation {mode} sauvegardée: {file_path}")
        
        # Retourner une liste vide pour éviter les erreurs d'itération
        return []
