#!/usr/bin/env python3
"""dither_applier.py — apply classic dithering algorithms to an image.

Supports ordered (Bayer) and error-diffusion kernels (Floyd-Steinberg,
Atkinson, Jarvis-Judice-Ninke, Sierra, Stevenson-Arce) plus blue-noise
threshold dithering. Works on grayscale or per-channel RGB and quantizes to an
arbitrary number of levels.

Unlike the GPU shaders (which approximate error diffusion in a local window),
this tool runs the *true* serial recurrence over the whole image, so output is
pixel-exact and reference-quality.

Examples
--------
    python dither_applier.py in.png out.png --algo floyd --levels 2
    python dither_applier.py in.png out.png --algo atkinson --color
    python dither_applier.py in.png out.png --algo bayer --matrix 8 --levels 4
    python dither_applier.py in.png out.png --algo blue-noise --noise bn256.png
"""
from __future__ import annotations

import argparse

import numpy as np

from halftone_common import load_image, save_image, to_gray

# Error-diffusion kernels: list of (dx, dy, weight). Weights sum to 1 except
# Atkinson, which deliberately discards 2/8 of the error.
KERNELS = {
    "floyd": [(1, 0, 7 / 16), (-1, 1, 3 / 16), (0, 1, 5 / 16), (1, 1, 1 / 16)],
    "atkinson": [
        (1, 0, 1 / 8), (2, 0, 1 / 8),
        (-1, 1, 1 / 8), (0, 1, 1 / 8), (1, 1, 1 / 8),
        (0, 2, 1 / 8),
    ],
    "jjn": [
        (1, 0, 7 / 48), (2, 0, 5 / 48),
        (-2, 1, 3 / 48), (-1, 1, 5 / 48), (0, 1, 7 / 48), (1, 1, 5 / 48), (2, 1, 3 / 48),
        (-2, 2, 1 / 48), (-1, 2, 3 / 48), (0, 2, 5 / 48), (1, 2, 3 / 48), (2, 2, 1 / 48),
    ],
    "sierra": [
        (1, 0, 5 / 32), (2, 0, 3 / 32),
        (-2, 1, 2 / 32), (-1, 1, 4 / 32), (0, 1, 5 / 32), (1, 1, 4 / 32), (2, 1, 2 / 32),
        (-1, 2, 2 / 32), (0, 2, 3 / 32), (1, 2, 2 / 32),
    ],
    "stevenson-arce": [
        (2, 0, 32 / 200),
        (-3, 1, 12 / 200), (-1, 1, 26 / 200), (1, 1, 30 / 200), (3, 1, 16 / 200),
        (-2, 2, 12 / 200), (0, 2, 26 / 200), (2, 2, 12 / 200),
        (-3, 3, 5 / 200), (-1, 3, 12 / 200), (1, 3, 12 / 200), (3, 3, 5 / 200),
    ],
}


def bayer_matrix(n: int) -> np.ndarray:
    """Normalized Bayer threshold matrix of order n (2, 4, 8...), values [0,1)."""
    if n < 2:
        return np.array([[0.0]])
    base = np.array([[0, 2], [3, 1]], dtype=np.float64)
    m = base
    size = 2
    while size < n:
        m = np.block([
            [4 * m + 0, 4 * m + 2],
            [4 * m + 3, 4 * m + 1],
        ])
        size *= 2
    return m / (n * n)


def quantize(v: np.ndarray, levels: int) -> np.ndarray:
    L = max(levels - 1, 1)
    return np.round(np.clip(v, 0.0, 1.0) * L) / L


def ordered_dither(chan: np.ndarray, levels: int, matrix: int) -> np.ndarray:
    m = bayer_matrix(matrix)
    h, w = chan.shape
    tiled = np.tile(m, (h // matrix + 1, w // matrix + 1))[:h, :w]
    L = max(levels - 1, 1)
    return np.floor(chan * L + (tiled - 0.5) + 0.5) / L


def blue_noise_dither(chan: np.ndarray, levels: int, noise: np.ndarray) -> np.ndarray:
    h, w = chan.shape
    nh, nw = noise.shape
    tiled = np.tile(noise, (h // nh + 1, w // nw + 1))[:h, :w]
    L = max(levels - 1, 1)
    return np.floor(chan * L + (tiled - 0.5) + 0.5) / L


def error_diffusion(chan: np.ndarray, levels: int, kernel, serpentine: bool) -> np.ndarray:
    """True serial error diffusion. `chan` is a 2D float array in [0,1]."""
    out = chan.astype(np.float64).copy()
    h, w = out.shape
    for y in range(h):
        xs = range(w)
        flip = serpentine and (y % 2 == 1)
        if flip:
            xs = range(w - 1, -1, -1)
        for x in xs:
            old = out[y, x]
            new = quantize(np.array(old), levels).item()
            err = old - new
            out[y, x] = new
            for dx, dy, wgt in kernel:
                sx = x - dx if flip else x + dx
                sy = y + dy
                if 0 <= sx < w and 0 <= sy < h:
                    out[sy, sx] += err * wgt
    return np.clip(out, 0.0, 1.0)


def apply_dither(img: np.ndarray, args) -> np.ndarray:
    noise = None
    if args.algo == "blue-noise":
        if not args.noise:
            raise SystemExit("--noise PATH is required for --algo blue-noise")
        noise = to_gray(load_image(args.noise))

    def per_channel(c: np.ndarray) -> np.ndarray:
        if args.algo == "bayer":
            return ordered_dither(c, args.levels, args.matrix)
        if args.algo == "blue-noise":
            return blue_noise_dither(c, args.levels, noise)
        return error_diffusion(c, args.levels, KERNELS[args.algo], args.serpentine)

    if args.color and img.shape[-1] >= 3:
        chans = [per_channel(img[..., i]) for i in range(3)]
        return np.stack(chans, axis=-1)
    gray = to_gray(img)
    return per_channel(gray)


def main() -> None:
    algos = ["bayer", "blue-noise", *KERNELS.keys()]
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--algo", choices=algos, default="floyd")
    p.add_argument("--levels", type=int, default=2, help="output levels per channel")
    p.add_argument("--matrix", type=int, default=8, help="Bayer matrix order (2/4/8/16)")
    p.add_argument("--color", action="store_true", help="dither RGB channels (else grayscale)")
    p.add_argument("--noise", help="blue-noise texture PNG (for --algo blue-noise)")
    p.add_argument("--serpentine", action="store_true",
                   help="alternate scan direction each row (reduces directional worms)")
    args = p.parse_args()

    img = load_image(args.input)
    out = apply_dither(img, args)
    save_image(out, args.output)
    print(f"wrote {args.output}  ({args.algo}, levels={args.levels}, "
          f"{'color' if args.color else 'gray'})")


if __name__ == "__main__":
    main()
