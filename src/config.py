from pathlib import Path

# Project root folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Data paths
DATA_DIR = BASE_DIR / "data"
PDF_PATH = DATA_DIR / "SLATEFALL_DOSSIER.pdf"
KB_PATH = DATA_DIR / "kb.json"

# Output paths
OUTPUTS_DIR = BASE_DIR / "outputs"