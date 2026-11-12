"""Remove the white background connected to the image border and export
square transparent PNG stickers.

usage: remove_bg.py <src_dir> <dst_dir> [size]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

T_BG = 30      # "near white" distance treated as background
T_LO, T_HI = 12, 70  # soft-edge ramp on the outline ring
RING = 2       # px around the background that gets a soft alpha


def process(path: Path, size: int) -> Image.Image:
    rgb = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    dist = 255.0 - rgb.min(axis=2)  # 0 = pure white

    cand = dist < T_BG
    labels, _ = ndimage.label(cand)
    border = np.unique(np.concatenate([
        labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    border = border[border != 0]
    bg = np.isin(labels, border)

    alpha = np.where(bg, 0.0, 1.0)
    ring = ndimage.binary_dilation(bg, iterations=RING) & ~bg
    ramp = np.clip((dist - T_LO) / (T_HI - T_LO), 0, 1)
    alpha[ring] = ramp[ring]
    alpha = ndimage.gaussian_filter(alpha, 0.6) * (~bg | ring)
    alpha[bg & ~ndimage.binary_dilation(~bg, iterations=1)] = 0

    # Un-blend the white halo out of the semi-transparent edge.
    a = np.clip(alpha, 1e-3, 1)[..., None]
    color = np.clip((rgb - (1 - a) * 255) / a, 0, 255)
    rgba = np.dstack([color, alpha * 255]).astype(np.uint8)
    img = Image.fromarray(rgba, "RGBA")

    bbox = img.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    img = img.crop(bbox)
    pad = int(size * 0.04)
    inner = size - 2 * pad
    scale = inner / max(img.size)
    img = img.resize((max(1, round(img.width * scale)),
                      max(1, round(img.height * scale))), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, ((size - img.width) // 2, (size - img.height) // 2), img)
    return out


def main():
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 512
    dst.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in src.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg"})
    for i, p in enumerate(files, 1):
        out = dst / f"{i:02d}.png"
        process(p, size).save(out, optimize=True)
        print(p.name, "->", out.name)


if __name__ == "__main__":
    main()
