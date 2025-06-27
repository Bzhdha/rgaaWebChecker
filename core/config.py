class Config:
    # Constantes pour les modules (puissances de 2)
    MODULE_CONTRAST = 1      # 2^0
    MODULE_DOM = 2          # 2^1
    MODULE_DALTONISM = 4    # 2^2
    MODULE_TAB = 8         # 2^3
    MODULE_SCREEN = 16     # 2^4
    MODULE_IMAGE = 32      # 2^5

    def __init__(self):
        self.driver_path = None
        self.enabled_modules = []  # Liste vide par défaut
        self.report_format = 'markdown'
        self.base_url = None
        self.output_dir = 'site_images'

    def set_driver_path(self, path):
        self.driver_path = path

    def get_enabled_modules(self):
        return self.enabled_modules

    def get_report_format(self):
        return self.report_format

    def set_base_url(self, url):
        self.base_url = url

    def set_output_dir(self, dir):
        self.output_dir = dir

    def set_modules(self, module_flags):
        """
        Active les modules en fonction des flags binaires
        :param module_flags: Entier représentant les modules à activer
        """
        self.enabled_modules = []
        
        if module_flags & self.MODULE_CONTRAST:
            self.enabled_modules.append('contrast')
        if module_flags & self.MODULE_DOM:
            self.enabled_modules.append('dom_analyzer')
        if module_flags & self.MODULE_DALTONISM:
            self.enabled_modules.append('daltonism')
        if module_flags & self.MODULE_TAB:
            self.enabled_modules.append('tab_navigation')
        if module_flags & self.MODULE_SCREEN:
            self.enabled_modules.append('screen_reader')
        if module_flags & self.MODULE_IMAGE:
            self.enabled_modules.append('image_analyzer')

    @staticmethod
    def get_module_names():
        """
        Retourne un dictionnaire des modules disponibles avec leurs valeurs
        """
        return {
            'contrast': Config.MODULE_CONTRAST,
            'dom': Config.MODULE_DOM,
            'daltonism': Config.MODULE_DALTONISM,
            'tab': Config.MODULE_TAB,
            'screen': Config.MODULE_SCREEN,
            'image': Config.MODULE_IMAGE
        }
