"""Directorio de reportes generados por Book Manager."""

from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parent
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
