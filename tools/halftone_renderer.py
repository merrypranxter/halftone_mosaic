#!/usr/bin/env python3
"""halftone_renderer.py — CMYK halftone rendering (AM and FM screening).

AM (amplitude modulated): a regular dot grid per channel, dot size tracks ink
coverage, each channel rotated to a classic screen angle to minimise moiré.
FM (frequency modulated / stochastic): uniform-size dots whose *density*
tracks coverage, no fixed angle, no moiré.

Optionally simulates dot gain (ink spread on paper). Output is a high-res RGB
image suitable for screen, or a 1-bit-per-channel bitmap feel at high
supersampling.

Examples
--------
    python halftone_renderer.py portrait.jpg out.png --mode am --lpi 60 --scale 3
    python halftone_renderer.py portrait.jpg out.png --mode am --shape ellipse --dot-gain 0.1
    python halftone_renderer.py portrait.jpg out.png --mode fm --dot-size 2 --scale 2
"""
from __future__ import annotations

import argparse

import numpy as np

from halftone_common import load_image, save_image, rgb_to_cmyk

# Classic CMYK screen angles (degrees). Yellow at 0° (eye least sensitive).
ANGLES = {"C": 15.0, "M": 75.0, "Y": 0.0, "K": 45.0}
# Ink colors as RGB multipliers (subtractive).
INK_RGB = {
    "C": np.array([0.0, 1.0, 1.0]),
    "M": np.array([1.0, 0.0, 1.0]),
    "Y": np.array([1.0, 1.0, 0.0]),
    "K": np.array([0.0, 0.0, 0.0]),
}


def _coords(h: int, w: int, angle_deg: float):
    """Pixel coordinates rotated about the image center."""
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float64)
    cx, cy = w / 2.0, h / 2.0
    xs -= cx
    ys -= cy
    a = np.radians(angle_deg)
    ca, sa = np.cos(a), np.sin(a)
    return xs * ca - ys * sa, xs * sa + ys * ca


def am_screen(coverage: np.ndarray, cell: float, angle: float,
              shape: str, dot_gain: float) -> np.ndarray:
    """Amplitude-modulated screen: dot size follows coverage. Returns ink 0..1."""
    h, w = coverage.shape
    rx, ry = _coords(h, w, angle)
    fx = (np.mod(rx, cell) / cell) - 0.5
    fy = (np.mod(ry, cell) / cell) - 0.5

    cov = np.clip(coverage * (1.0 + dot_gain), 0.0, 1.0)
    radius = np.sqrt(cov) * 0.71  # area ~ coverage; reaches cell corners at 1

    if shape == "square":
        d = np.maximum(np.abs(fx), np.abs(fy))
    elif shape == "ellipse":
        d = np.sqrt(fx * fx + (fy * 1.6) ** 2)
    else:  # round
        d = np.sqrt(fx * fx + fy * fy)

    # Soft threshold for light anti-aliasing.
    aa = 0.5 / cell + 1e-3
    return 1.0 - np.clip((d - (radius - aa)) / (2 * aa), 0.0, 1.0)


def fm_screen(coverage: np.ndarray, dot_size: float, density: float,
              rng: np.random.Generator) -> np.ndarray:
    """Frequency-modulated screen: uniform dots, density follows coverage."""
    h, w = coverage.shape
    ink = np.zeros((h, w))
    cell = max(int(round(min(h, w) / max(density, 1.0))), 1)
    r = int(np.ceil(dot_size))
    ys = np.arange(0, h, cell)
    xs = np.arange(0, w, cell)
    yy, xx = np.meshgrid(ys, xs, indexing="ij")
    # Jitter candidate dot positions inside each cell.
    jy = (rng.random(yy.shape) * cell).astype(int)
    jx = (rng.random(xx.shape) * cell).astype(int)
    py = np.clip(yy + jy, 0, h - 1)
    px = np.clip(xx + jx, 0, w - 1)
    keep = rng.random(py.shape) < coverage[py, px]
    py, px = py[keep], px[keep]

    # Stamp small disks.
    yk, xk = np.mgrid[-r:r + 1, -r:r + 1]
    disk = (xk * xk + yk * yk) <= dot_size * dot_size
    for cy, cx in zip(py, px):
        y0, y1 = max(cy - r, 0), min(cy + r + 1, h)
        x0, x1 = max(cx - r, 0), min(cx + r + 1, w)
        dy0, dx0 = y0 - (cy - r), x0 - (cx - r)
        sub = disk[dy0:dy0 + (y1 - y0), dx0:dx0 + (x1 - x0)]
        ink[y0:y1, x0:x1] = np.maximum(ink[y0:y1, x0:x1], sub)
    return ink


def render(img: np.ndarray, args) -> np.ndarray:
    # Supersample for crisp dots, then downsample on save by scaling input up.
    cmyk = rgb_to_cmyk(img)
    h, w = cmyk.shape[:2]
    cell = max(min(h, w) / max(args.lpi, 1.0), 2.0)

    paper = np.ones((h, w, 3))  # white paper
    out = paper.copy()
    rng = np.random.default_rng(args.seed)

    for idx, ch in enumerate("CMYK"):
        coverage = cmyk[..., idx]
        if args.mode == "am":
            ink = am_screen(coverage, cell, ANGLES[ch], args.shape, args.dot_gain)
        else:
            ink = fm_screen(coverage, args.dot_size, args.lpi, rng)
        # Multiply ink color onto the accumulating paper (subtractive).
        ink3 = ink[..., None]
        out = out * (1.0 - ink3 * (1.0 - INK_RGB[ch]))
    return np.clip(out, 0.0, 1.0)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--mode", choices=["am", "fm"], default="am")
    p.add_argument("--lpi", type=float, default=60.0,
                   help="lines per inch analogue: dot cells across the image")
    p.add_argument("--shape", choices=["round", "ellipse", "square"], default="round")
    p.add_argument("--dot-gain", type=float, default=0.0, help="0..1 ink spread")
    p.add_argument("--dot-size", type=float, default=1.5, help="FM dot radius (px)")
    p.add_argument("--scale", type=float, default=1.0, help="upscale input before screening")
    p.add_argument("--seed", type=int, default=0, help="RNG seed for FM screening")
    args = p.parse_args()

    img = load_image(args.input)
    if args.scale != 1.0:
        from PIL import Image
        h, w = img.shape[:2]
        pil = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
        pil = pil.resize((int(w * args.scale), int(h * args.scale)), Image.LANCZOS)
        img = np.asarray(pil, dtype=np.float64) / 255.0

    out = render(img, args)
    save_image(out, args.output)
    print(f"wrote {args.output}  (mode={args.mode}, lpi={args.lpi}, shape={args.shape})")


if __name__ == "__main__":
    main()
