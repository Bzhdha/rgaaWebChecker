import logging
import os
import sys
from datetime import datetime
from .report_converter import ReportConverter
from .progress_display import ProgressDisplay

class ConsoleFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        self.progress = ProgressDisplay()
        self.last_message = ""
        self.is_header = False

    def format(self, record):
        if hasattr(record, 'step_tag'):
            record.msg = f"[{record.step_tag}] {record.msg}"
        if record.levelno == logging.INFO:
            if record.msg.startswith('=') or record.msg.startswith('#'):
                self.progress.clear()
                self.is_header = True
                return f"\n{record.msg}\n"
            else:
                # Éviter la duplication des messages
                if record.msg != self.last_message:
                    if not self.is_header:
                        # Mettre à jour l'affichage de progression
                        self.progress.update(f"Progression : {record.msg}")
                    self.last_message = record.msg
                    self.is_header = False
                    # Afficher les messages importants
                    if "initialisé" in record.msg.lower() or "assigné" in record.msg.lower() or "visité" in record.msg.lower():
                        return f"\n{record.msg}\n"
                return ""  # Ne rien afficher pour les autres messages
        elif record.levelno in (logging.WARNING, logging.ERROR):
            self.progress.clear()
            self.is_header = True
            return f"\n{record.msg}\n"
        return ""

class FileFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, 'step_tag'):
            record.msg = f"[{record.step_tag}] {record.msg}"
        if record.levelno == logging.INFO:
            if record.msg.startswith('=') or record.msg.startswith('#'):
                return f"\n{record.msg}\n"
            elif record.msg.startswith('✓'):
                return f"- {record.msg}"
            elif record.msg.startswith('✗'):
                return f"- ⚠️ {record.msg}"
            else:
                return record.msg
        elif record.levelno == logging.WARNING:
            return f"\n⚠️ **Attention**: {record.msg}\n"
        elif record.levelno == logging.ERROR:
            return f"\n❌ **Erreur**: {record.msg}\n"
        return super().format(record)

def setup_logger(debug=False, encoding='utf-8'):
    logger = logging.getLogger('AccessibilityCrawler')
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    logger.handlers = []

    os.makedirs('reports', exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'reports/rapport_accessibilite_{timestamp}.md'

    file_handler = logging.FileHandler(log_file, encoding=encoding)
    file_handler.setFormatter(FileFormatter())
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_handler.setFormatter(ConsoleFormatter())
    logger.addHandler(console_handler)

    logger.info('=' * 50)
    logger.info('Démarrage de l\'analyse d\'accessibilité')
    logger.info('=' * 50)

    return logger

def log_with_step(logger, level, step_tag, message):
    """
    Log un message avec un tag d'étape d'analyse
    
    Args:
        logger: Le logger à utiliser
        level: Le niveau de log (INFO, WARNING, ERROR, DEBUG)
        step_tag: Le tag de l'étape d'analyse
        message: Le message à logger
    """
    # Créer un record avec le tag d'étape
    record = logger.makeRecord(
        logger.name, level, "", 0, message, (), None
    )
    record.step_tag = step_tag
    
    # Logger le message
    logger.handle(record)
