#!/usr/bin/env python3
"""build_gallery.py — render a representative sample of every effect.

Generates a synthetic test image (a portrait-ish radial subject over a tonal
gradient) when no source is given, then runs the halftone, dither, and mosaic
pipelines and writes the results into ../gallery/. Re-run any time to refresh
the gallery; it is fully deterministic given a seed.

    python build_gallery.py                 # synthetic source
    python build_gallery.py photo.jpg       # your own image
"""
from __future__ import annotations

import argparse
import os

import numpy as np

from halftone_common import load_image, save_image
import halftone_renderer as hr
import dither_applier as da
import mosaic_tile_generator as mtg
from blue_noise_generator import generate as gen_bn

GALLERY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gallery"))


def synthetic_source(size: int = 320) -> np.ndarray:
    """A test subject with smooth tone, an edge, and a highlight — exercises
    gradients (dither worms), edges (mosaic cells) and midtones (halftone)."""
    y, x = np.mgrid[0:size, 0:size] / size
    bg = 0.15 + 0.7 * y                                   # vertical tonal ramp
    head = np.exp(-((x - 0.5) ** 2 + (y - 0.45) ** 2) / 0.05)  # soft sphere
    highlight = np.exp(-((x - 0.42) ** 2 + (y - 0.36) ** 2) / 0.004)
    g = np.clip(bg * (1 - head) + (0.55 + 0.45 * highlight) * head, 0, 1)
    r = np.clip(g * 1.05 + 0.05 * head, 0, 1)
    b = np.clip(g * 0.9, 0, 1)
    return np.stack([r, g, b], axis=-1)


class _A:
    pass


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", nargs="?", help="source image (synthetic if omitted)")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    os.makedirs(GALLERY, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    if args.input:
        img = load_image(args.input)
    else:
        img = synthetic_source()
    save_image(img, os.path.join(GALLERY, "00_source.png"))

    gray = da.to_gray(img)
    bn = gen_bn(64, "fft", rng)

    # --- Halftone ---------------------------------------------------------
    a = _A(); a.mode="am"; a.lpi=36; a.shape="round"; a.dot_gain=0.08
    a.dot_size=1.5; a.seed=args.seed
    save_image(hr.render(img, a), os.path.join(GALLERY, "10_halftone_am_round.png"))
    a.shape = "ellipse"
    save_image(hr.render(img, a), os.path.join(GALLERY, "11_halftone_am_ellipse.png"))
    a.mode="fm"; a.lpi=90; a.dot_size=1.4
    save_image(hr.render(img, a), os.path.join(GALLERY, "12_halftone_fm.png"))

    # --- Dither -----------------------------------------------------------
    save_image(da.error_diffusion(gray, 2, da.KERNELS["floyd"], True),
               os.path.join(GALLERY, "20_dither_floyd.png"))
    save_image(da.error_diffusion(gray, 2, da.KERNELS["atkinson"], False),
               os.path.join(GALLERY, "21_dither_atkinson.png"))
    save_image(da.ordered_dither(gray, 2, 8),
               os.path.join(GALLERY, "22_dither_bayer8.png"))
    save_image(da.blue_noise_dither(gray, 2, bn),
               os.path.join(GALLERY, "23_dither_blue_noise.png"))

    # --- Mosaic -----------------------------------------------------------
    h, w = img.shape[:2]
    lab, n = mtg.square_labels(h, w, 14, brick=True)
    out = mtg.apply_grout(mtg._region_mean(img, lab, n, False), lab, 1)
    save_image(out, os.path.join(GALLERY, "30_mosaic_brick.png"))

    lab, n = mtg.hex_labels(h, w, 11)
    save_image(mtg._region_mean(img, lab, n, False),
               os.path.join(GALLERY, "31_mosaic_hex.png"))

    lab, n = mtg.voronoi_labels(h, w, 500, np.random.default_rng(args.seed))
    out = mtg.apply_grout(mtg._region_mean(img, lab, n, False), lab, 2)
    save_image(out, os.path.join(GALLERY, "32_mosaic_voronoi_glass.png"))

    print(f"gallery refreshed -> {GALLERY}")


if __name__ == "__main__":
    main()
