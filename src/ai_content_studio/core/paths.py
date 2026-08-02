"""Project path constants.

All paths are derived from ROOT. No directories are created here.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

# Source and documentation
SRC = ROOT / "src"
DOCS = ROOT / "docs"
BRANDS = ROOT / "brands"

# Runtime data directories (created elsewhere when needed)
DATA = ROOT / "data"
CACHE = DATA / "cache"
ASSETS = DATA / "assets"
PROJECTS = DATA / "projects"
RENDERS = DATA / "renders"
OUTPUT = DATA / "output"
TEMP = DATA / "temp"
