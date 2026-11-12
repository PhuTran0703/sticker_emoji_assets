"""Remove the white background connected to the image border and export
square transparent PNG stickers.

usage: remove_bg.py <src_dir> <dst_dir> [--size 512] [--threshold 6] [--seal 0]

White parts of the art that touch the border without an outline (snow on the
ground, clouds) get eaten with the defaults. For those, pass --seal 12
(px of gap to close in their faint edge); --threshold tunes how faint.
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

T_BG = 30      # "near white" distance treated as background
T_LO, T_HI = 12, 70  # soft-edge ramp on the outline ring
RING = 2       # px around the background that gets a soft alpha


def _border_fill(open_: np.ndarray) -> np.ndarray:
    """The parts of [open_] connected to the image border."""
    labels, _ = ndimage.label(open_)
    border = np.unique(np.concatenate([
        labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    return np.isin(labels, border[border != 0])


def process(path: Path, size: int, t_bg: float = 6, seal: int = 0) -> Image.Image:
    rgb = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    dist = 255.0 - rgb.min(axis=2)  # 0 = pure white

    bg = _border_fill(dist < T_BG)
    if seal:
        # A stricter fill that can't leak through gaps in a faint edge keeps
        # the white areas of the art behind it; grown back by [seal] so the
        # halo along strong outlines still goes.
        strict = ~ndimage.binary_dilation(dist >= t_bg, iterations=seal)
        bg &= ndimage.binary_dilation(_border_fill(strict), iterations=seal)

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
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=Path)
    ap.add_argument("dst", type=Path)
    ap.add_argument("--size", type=int, default=512)
    ap.add_argument("--threshold", type=float, default=6,
                    help="edge strength that stops the --seal fill")
    ap.add_argument("--seal", type=int, default=0)
    ap.add_argument("--only", nargs="*", help="output names to (re)write, e.g. 03.png")
    args = ap.parse_args()
    src, dst = args.src, args.dst
    dst.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in src.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg"})
    for i, p in enumerate(files, 1):
        out = dst / f"{i:02d}.png"
        if args.only and out.name not in args.only:
            continue
        process(p, args.size, args.threshold, args.seal).save(out, optimize=True)
        print(p.name, "->", out.name)


if __name__ == "__main__":
    main()
