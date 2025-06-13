
import unittest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from modules.contrast_checker import ContrastChecker
from modules.color_simulator import ColorSimulator
from modules.tab_navigator import TabNavigator
from utils.log_utils import setup_logger

class TestAccessibilityCrawlerModules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        service = Service('/usr/local/bin/chromedriver')
        cls.driver = webdriver.Chrome(service=service, options=chrome_options)
        cls.driver.get('https://www.example.com')
        cls.logger = setup_logger()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_contrast_checker(self):
        checker = ContrastChecker(self.driver, self.logger)
        checker.run()

    def test_color_simulator(self):
        simulator = ColorSimulator(self.driver, self.logger)
        simulator.run()

    def test_tab_navigator(self):
        navigator = TabNavigator(self.driver, self.logger)
        elements = navigator.run()
        self.assertIsInstance(elements, list)
        self.assertGreater(len(elements), 0)

if __name__ == '__main__':
    unittest.main()
