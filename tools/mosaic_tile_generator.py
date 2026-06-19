#!/usr/bin/env python3
"""mosaic_tile_generator.py — turn an image into a mosaic of tiles.

Tile shapes:
  square   - regular grid, each tile = mean color of its region
  brick    - square tiles, every other row offset by half a tile
  hex      - hexagonal lattice (pointy-top), nearest-center assignment
  triangle - each square split into two triangles, each its own mean color
  voronoi  - irregular Voronoi cells from jittered (or random) seed points

Rendering styles: average color (default) or dominant color (mode of a coarse
color histogram). Optionally emits a tile map (PNG where each tile is a flat
integer id encoded in RGB) for interactive "hover to reveal" effects.

Examples
--------
    python mosaic_tile_generator.py in.jpg out.png --shape square --tile 24
    python mosaic_tile_generator.py in.jpg out.png --shape hex --tile 18 --grout 0.08
    python mosaic_tile_generator.py in.jpg out.png --shape voronoi --seeds 1500
    python mosaic_tile_generator.py in.jpg out.png --shape triangle --tile 30 --tilemap map.png
"""
from __future__ import annotations

import argparse

import numpy as np

from halftone_common import load_image, save_image, srgb_to_linear, linear_to_srgb


def _region_mean(img: np.ndarray, labels: np.ndarray, n: int,
                 dominant: bool) -> np.ndarray:
    """Color each pixel by its label's mean (or dominant) color."""
    h, w, c = img.shape
    flat = img.reshape(-1, c)
    lab = labels.reshape(-1)
    out = np.zeros_like(flat)
    if dominant:
        # Dominant = mean of the densest bin in a coarse 3D histogram per label.
        q = np.clip((flat * 4).astype(int), 0, 3)  # 4^3 = 64 bins
        key = (q[:, 0] * 16 + q[:, 1] * 4 + q[:, 2])
        for lbl in range(n):
            m = lab == lbl
            if not m.any():
                continue
            bins = key[m]
            top = np.bincount(bins, minlength=64).argmax()
            sel = m & (key == top)
            out[m] = flat[sel].mean(axis=0)
    else:
        lin = srgb_to_linear(flat)
        for ch in range(c):
            sums = np.bincount(lab, weights=lin[:, ch], minlength=n)
            counts = np.bincount(lab, minlength=n)
            counts[counts == 0] = 1
            means = sums / counts
            out[:, ch] = means[lab]
        out = linear_to_srgb(out)
    return out.reshape(h, w, c)


def square_labels(h: int, w: int, tile: int, brick: bool):
    ys, xs = np.mgrid[0:h, 0:w]
    if brick:
        row = ys // tile
        xs = xs + np.where(row % 2 == 1, tile // 2, 0)
    ty, tx = ys // tile, xs // tile
    cols = (w // tile) + 2
    labels = ty * cols + tx
    return _reindex(labels)


def triangle_labels(h: int, w: int, tile: int):
    ys, xs = np.mgrid[0:h, 0:w]
    ty, tx = ys // tile, xs // tile
    fy, fx = (ys % tile) / tile, (xs % tile) / tile
    upper = (fx + fy) < 1.0  # split each cell along the anti-diagonal
    cols = (w // tile) + 2
    labels = (ty * cols + tx) * 2 + upper.astype(int)
    return _reindex(labels)


def hex_labels(h: int, w: int, size: int):
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float64)
    gx, gy = size * 1.7320508, size * 1.5
    # Two interleaved grids; assign to nearest center.
    ax = (np.floor(xs / gx) + 0.5) * gx
    ay = (np.floor(ys / gy) + 0.5) * gy
    bx = (np.floor((xs - gx / 2) / gx) + 0.5) * gx + gx / 2
    by = (np.floor((ys - gy / 2) / gy) + 0.5) * gy + gy / 2
    da = (xs - ax) ** 2 + (ys - ay) ** 2
    db = (xs - bx) ** 2 + (ys - by) ** 2
    pick_b = db < da
    cx = np.where(pick_b, bx, ax)
    cy = np.where(pick_b, by, ay)
    key = np.round(cx).astype(np.int64) * (h + 1) + np.round(cy).astype(np.int64)
    return _reindex(key)


def voronoi_labels(h: int, w: int, n_seeds: int, rng):
    sx = rng.integers(0, w, n_seeds)
    sy = rng.integers(0, h, n_seeds)
    ys, xs = np.mgrid[0:h, 0:w]
    # Nearest seed via chunked distance to keep memory bounded.
    labels = np.zeros((h, w), dtype=np.int64)
    best = np.full((h, w), np.inf)
    for i in range(n_seeds):
        d = (xs - sx[i]) ** 2 + (ys - sy[i]) ** 2
        closer = d < best
        best = np.where(closer, d, best)
        labels = np.where(closer, i, labels)
    return labels, n_seeds


def _reindex(labels: np.ndarray):
    uniq, inv = np.unique(labels, return_inverse=True)
    return inv.reshape(labels.shape), len(uniq)


def apply_grout(img: np.ndarray, labels: np.ndarray, width: float) -> np.ndarray:
    """Darken pixels on a tile boundary to create grout/lead lines."""
    if width <= 0:
        return img
    edge = np.zeros(labels.shape, dtype=bool)
    edge[:-1, :] |= labels[:-1, :] != labels[1:, :]
    edge[:, :-1] |= labels[:, :-1] != labels[:, 1:]
    if width > 1:
        # Thicken by OR-ing shifted copies.
        thick = edge.copy()
        k = int(width)
        for d in range(1, k):
            thick[d:, :] |= edge[:-d, :]
            thick[:, d:] |= edge[:, :-d]
        edge = thick
    out = img.copy()
    out[edge] = 0.06
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--shape", choices=["square", "brick", "hex", "triangle", "voronoi"],
                   default="square")
    p.add_argument("--tile", type=int, default=24, help="tile size in pixels")
    p.add_argument("--seeds", type=int, default=1200, help="seed count for voronoi")
    p.add_argument("--style", choices=["average", "dominant"], default="average")
    p.add_argument("--grout", type=float, default=0.0, help="grout width in pixels")
    p.add_argument("--tilemap", help="optional path to write a tile-id map PNG")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    img = load_image(args.input)
    h, w = img.shape[:2]
    rng = np.random.default_rng(args.seed)

    if args.shape == "square":
        labels, n = square_labels(h, w, args.tile, brick=False)
    elif args.shape == "brick":
        labels, n = square_labels(h, w, args.tile, brick=True)
    elif args.shape == "triangle":
        labels, n = triangle_labels(h, w, args.tile)
    elif args.shape == "hex":
        labels, n = hex_labels(h, w, args.tile)
    else:
        labels, n = voronoi_labels(h, w, args.seeds, rng)

    out = _region_mean(img, labels, n, dominant=(args.style == "dominant"))
    out = apply_grout(out, labels, args.grout)
    save_image(out, args.output)
    print(f"wrote {args.output}  (shape={args.shape}, tiles={n}, style={args.style})")

    if args.tilemap:
        ids = labels.astype(np.int64)
        rgb = np.stack([ids & 255, (ids >> 8) & 255, (ids >> 16) & 255], axis=-1)
        save_image(rgb / 255.0, args.tilemap)
        print(f"wrote {args.tilemap}  (tile id map)")


if __name__ == "__main__":
    main()
