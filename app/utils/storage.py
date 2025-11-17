from pathlib import Path

STORAGE = Path("storage")
ORIGINALS = STORAGE / "originals"
THUMBS = STORAGE / "thumbs"

ORIGINALS.mkdir(parents=True, exist_ok=True)
THUMBS.mkdir(parents=True, exist_ok=True)

