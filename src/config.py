from pathlib import Path

# Anchor to this config file's directory (src/)
_SRC_DIR = Path(__file__).resolve().parent

# Define global path constants for the project
PROJECT_ROOT = _SRC_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"