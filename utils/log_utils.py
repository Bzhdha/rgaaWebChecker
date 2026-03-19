import logging
import os
import re
import sys
from datetime import datetime

# Titres markdown ATX (# à ###### suivi d'un espace), pas les lignes type "#1 · …"
_MARKDOWN_ATX = re.compile(r"^#{1,6}\s")


def _is_markdown_heading(text: str) -> bool:
    s = text.strip()
    return bool(_MARKDOWN_ATX.match(s))


class StructuredConsoleFormatter(logging.Formatter):
    """
    Console : une ligne par événement (heure | niveau | module | message).
    Les titres markdown (# …) et séparateurs (===, ---) restent en blocs multi-lignes.
    """

    _SHORT = {
        logging.DEBUG: "DBG",
        logging.INFO: "INF",
        logging.WARNING: "WRN",
        logging.ERROR: "ERR",
        logging.CRITICAL: "CRT",
    }

    def formatTime(self, record, datefmt=None):
        return datetime.fromtimestamp(record.created).strftime(datefmt or "%H:%M:%S")

    def format(self, record):
        msg = record.getMessage()
        stripped = msg.strip()
        if not stripped:
            return ""

        # Titres / séparateurs : une seule ligne (le handler ajoute déjà un saut de ligne)
        if _is_markdown_heading(stripped) or stripped == "---" or (
            len(stripped) >= 8 and set(stripped) == {"="}
        ):
            return stripped

        tag = getattr(record, "step_tag", None) or "RUN"
        tag = (str(tag)[:12]).ljust(12)
        lvl = self._SHORT.get(record.levelno, record.levelname[:3].upper())
        ts = self.formatTime(record)
        single_line = " ".join(stripped.split())
        # Séparateurs ASCII (compat. console Windows cp1252)
        return f"{ts} | {lvl} | {tag} | {single_line}"


class FileFormatter(logging.Formatter):
    """Rapport fichier .md : préserve les titres et met en forme avertissements / erreurs."""

    def format(self, record):
        msg = record.getMessage()
        prefix = f"[{record.step_tag}] " if getattr(record, "step_tag", None) else ""
        full = prefix + msg
        s = full.strip()

        if record.levelno == logging.INFO:
            if _is_markdown_heading(s) or s == "---" or (len(s) >= 8 and set(s) == {"="}):
                return f"\n{s}\n"
            if s.startswith("✓"):
                return f"- {s}"
            if s.startswith("✗") or s.startswith("❌"):
                return f"- ⚠️ {s}"
            return s
        if record.levelno == logging.WARNING:
            return f"\n⚠️ **Attention**: {s}\n"
        if record.levelno == logging.ERROR:
            return f"\n❌ **Erreur**: {s}\n"
        if record.levelno == logging.DEBUG:
            return f"    [DBG] {s}\n"
        return super().format(record)


def setup_logger(debug=False, encoding='utf-8'):
    logger = logging.getLogger('AccessibilityCrawler')
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    os.makedirs('reports', exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'reports/rapport_accessibilite_{timestamp}.md'

    file_handler = logging.FileHandler(log_file, encoding=encoding)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(FileFormatter())
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_handler.setFormatter(StructuredConsoleFormatter())
    logger.addHandler(console_handler)

    logger.info('=' * 50)
    logger.info('Démarrage de l\'analyse d\'accessibilité')
    logger.info('=' * 50)

    return logger


def log_with_step(logger, level, step_tag, message):
    """
    Enregistre un message avec un tag module (colonne « module » en console, préfixe en fichier).
    """
    if not logger.isEnabledFor(level):
        return
    logger.log(level, message, extra={"step_tag": step_tag})
