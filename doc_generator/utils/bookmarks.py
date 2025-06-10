import os, yaml
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

def load_bookmarks() -> dict[str, str]:
    """
    1) Prefer individual DOC_BM_* variables from .env
    2) Fall back to bookmarks.yaml if present
    """
    bm = {k[8:]: v for k, v in os.environ.items() if k.startswith("DOC_BM_")}
    if bm:
        return bm

    yaml_file = PROJECT_ROOT / "bookmarks.yaml"
    if yaml_file.exists():
        return yaml.safe_load(open(yaml_file))

    raise RuntimeError("No bookmark IDs found in env or bookmarks.yaml")