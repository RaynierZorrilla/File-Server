import hashlib
from pathlib import Path
from typing import Tuple
from PIL import Image

STORAGE = Path("storage")
ORIGINALS = STORAGE / "originals"
THUMBS = STORAGE / "thumbs"

ORIGINALS.mkdir(parents=True, exist_ok=True)
THUMBS.mkdir(parents=True, exist_ok=True)


def sha256sum(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def image_size(path: Path) -> Tuple[int, int] | tuple[None, None]:
    try:
        with Image.open(path) as im:
            return im.width, im.height
    except Exception:
        return None, None

def make_thumbnail(src: Path, dst: Path, w: int | None, h: int | None, fit: str = "contain"):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        if not w and not h:
            w = 320
        if fit == "crop" and w and h:
            im = im.copy()
            im.thumbnail((w*2, h*2))
            im_ratio = im.width / im.height
            target_ratio = w / h
            if im_ratio > target_ratio:
                # recort width
                new_w = int(im.height * target_ratio)
                x = (im.width - new_w) // 2
                box = (x, 0, x + new_w, im.height)
                im = im.crop(box)
            else:
                # recort height
                new_h = int(im.width / target_ratio)
                y = (im.height - new_h) // 2
                box = (0, y, im.width, y + new_h)
                im = im.crop(box)
            im = im.resize((w, h))
        else:
            im.thumbnail((w or 99999, h or 99999))
        im.save(dst)