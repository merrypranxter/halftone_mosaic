#!/usr/bin/env python3
"""Mosaic tile generators built with NumPy and Pillow."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image

try:
    from scipy import ndimage as _scipy_ndimage
except Exception:  # pragma: no cover - optional dependency
    _scipy_ndimage = None

try:
    from scipy.spatial import cKDTree as _KDTree
except Exception:  # pragma: no cover - optional dependency
    _KDTree = None


ArrayLike = np.ndarray


def _as_rgb_array(img: Image.Image | ArrayLike) -> ArrayLike:
    if isinstance(img, Image.Image):
        arr = np.asarray(img.convert("RGB"), dtype=np.uint8)
    else:
        arr = np.asarray(img)
        if arr.ndim == 2:
            arr = np.stack([arr] * 3, axis=-1)
        if arr.dtype != np.uint8:
            if arr.max(initial=0) <= 1.0:
                arr = (np.clip(arr, 0.0, 1.0) * 255).astype(np.uint8)
            else:
                arr = np.clip(arr, 0, 255).astype(np.uint8)
    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError("Expected an RGB image.")
    return arr


def _dominant_color(region: ArrayLike) -> ArrayLike:
    flat = region.reshape(-1, region.shape[-1])
    colors, counts = np.unique(flat, axis=0, return_counts=True)
    return colors[np.argmax(counts)]


def _tile_color(region: ArrayLike, method: str) -> ArrayLike:
    if region.size == 0:
        return np.array([0, 0, 0], dtype=np.uint8)
    method = method.lower()
    if method == "average":
        return np.mean(region.reshape(-1, 3), axis=0).astype(np.uint8)
    if method == "dominant":
        return _dominant_color(region).astype(np.uint8)
    if method == "center":
        return region[region.shape[0] // 2, region.shape[1] // 2].astype(np.uint8)
    raise ValueError("method must be one of: average, dominant, center")


def _normalize_color(color):
    if color is None:
        return None
    return np.asarray(color, dtype=np.uint8)


def square_mosaic(
    img: Image.Image | ArrayLike,
    tile_size: int = 16,
    method: str = "average",
    brick_offset: bool = False,
    border_color=None,
    border_width: int = 1,
) -> Image.Image:
    """Create a square-tile mosaic, optionally with brick-style row offsets."""
    arr = _as_rgb_array(img)
    h, w, _ = arr.shape
    out = np.zeros_like(arr)
    border = _normalize_color(border_color)

    row_index = 0
    for y0 in range(0, h, tile_size):
        y1 = min(y0 + tile_size, h)
        offset = tile_size // 2 if brick_offset and (row_index % 2 == 1) else 0
        for x_start in range(-offset, w, tile_size):
            x0 = max(x_start, 0)
            x1 = min(x_start + tile_size, w)
            if x0 >= x1:
                continue
            region = arr[y0:y1, x0:x1]
            color = _tile_color(region, method)
            out[y0:y1, x0:x1] = color
            if border is not None and border_width > 0:
                bw = min(border_width, y1 - y0, x1 - x0)
                out[y0 : y0 + bw, x0:x1] = border
                out[y1 - bw : y1, x0:x1] = border
                out[y0:y1, x0 : x0 + bw] = border
                out[y0:y1, x1 - bw : x1] = border
        row_index += 1

    return Image.fromarray(out, mode="RGB")


def _round_hex(q: ArrayLike, r: ArrayLike) -> tuple[ArrayLike, ArrayLike]:
    x = q
    z = r
    y = -x - z

    rx = np.round(x)
    ry = np.round(y)
    rz = np.round(z)

    x_diff = np.abs(rx - x)
    y_diff = np.abs(ry - y)
    z_diff = np.abs(rz - z)

    fix_x = (x_diff > y_diff) & (x_diff > z_diff)
    fix_y = ~fix_x & (y_diff > z_diff)
    fix_z = ~(fix_x | fix_y)

    rx[fix_x] = -ry[fix_x] - rz[fix_x]
    ry[fix_y] = -rx[fix_y] - rz[fix_y]
    rz[fix_z] = -rx[fix_z] - ry[fix_z]
    return rx.astype(np.int32), rz.astype(np.int32)


def hex_mosaic(
    img: Image.Image | ArrayLike,
    hex_size: int = 20,
    pointy_top: bool = True,
    border_color=None,
) -> Image.Image:
    """Create a hexagonal mosaic using axial-coordinate rounding."""
    arr = _as_rgb_array(img)
    h, w, _ = arr.shape
    yy, xx = np.indices((h, w), dtype=np.float32)
    size = float(hex_size)

    if pointy_top:
        q = (math.sqrt(3) / 3.0 * xx - 1.0 / 3.0 * yy) / size
        r = (2.0 / 3.0 * yy) / size
        rq, rr = _round_hex(q, r)
        cx = size * math.sqrt(3) * (rq + rr / 2.0)
        cy = size * 1.5 * rr
    else:
        q = (2.0 / 3.0 * xx) / size
        r = (-1.0 / 3.0 * xx + math.sqrt(3) / 3.0 * yy) / size
        rq, rr = _round_hex(q, r)
        cx = size * 1.5 * rq
        cy = size * math.sqrt(3) * (rr + rq / 2.0)

    sx = np.clip(np.rint(cx).astype(np.int32), 0, w - 1)
    sy = np.clip(np.rint(cy).astype(np.int32), 0, h - 1)
    out = arr[sy, sx]

    border = _normalize_color(border_color)
    if border is not None:
        border_mask = np.zeros((h, w), dtype=bool)
        border_mask[:, 1:] |= (rq[:, 1:] != rq[:, :-1]) | (rr[:, 1:] != rr[:, :-1])
        border_mask[1:, :] |= (rq[1:, :] != rq[:-1, :]) | (rr[1:, :] != rr[:-1, :])
        out = out.copy()
        out[border_mask] = border

    return Image.fromarray(out.astype(np.uint8), mode="RGB")


def _edge_weighted_seed_indices(gray: ArrayLike, n_seeds: int, rng: np.random.Generator) -> ArrayLike:
    gy, gx = np.gradient(gray)
    grad = np.sqrt(gx * gx + gy * gy)
    weights = grad.reshape(-1)
    weights = weights + 1e-6
    weights = weights / weights.sum()
    return rng.choice(gray.size, size=n_seeds, replace=False, p=weights)


def _manual_voronoi_labels(seed_points: ArrayLike, h: int, w: int) -> ArrayLike:
    labels = np.empty((h, w), dtype=np.int32)
    xs = np.arange(w, dtype=np.float32)
    for y0 in range(h):
        points = np.column_stack([np.full(w, y0, dtype=np.float32), xs])
        dist2 = np.sum((points[:, None, :] - seed_points[None, :, :]) ** 2, axis=2)
        labels[y0] = np.argmin(dist2, axis=1)
    return labels


def voronoi_mosaic(
    img: Image.Image | ArrayLike,
    n_seeds: int = 200,
    seed_distribution: str = "random",
    border_color=None,
    border_width: int = 1,
) -> Image.Image:
    """Create a Voronoi mosaic from random or edge-weighted seeds."""
    arr = _as_rgb_array(img)
    h, w, _ = arr.shape
    rng = np.random.default_rng(0)
    gray = np.dot(arr[..., :3].astype(np.float32), [0.299, 0.587, 0.114])

    n_seeds = max(1, min(n_seeds, h * w))
    if seed_distribution == "edge_weighted":
        chosen = _edge_weighted_seed_indices(gray, n_seeds, rng)
    elif seed_distribution == "random":
        chosen = rng.choice(h * w, size=n_seeds, replace=False)
    else:
        raise ValueError("seed_distribution must be 'random' or 'edge_weighted'")

    seed_y = chosen // w
    seed_x = chosen % w
    seed_points = np.column_stack([seed_y.astype(np.float32), seed_x.astype(np.float32)])
    seed_colors = arr[seed_y, seed_x]

    if _KDTree is not None:
        tree = _KDTree(seed_points)
        grid_y, grid_x = np.indices((h, w))
        _, labels = tree.query(np.column_stack([grid_y.ravel(), grid_x.ravel()]), k=1)
        labels = labels.reshape(h, w)
    else:
        labels = _manual_voronoi_labels(seed_points, h, w)

    out = seed_colors[labels]
    border = _normalize_color(border_color)
    if border is not None and border_width > 0:
        edges = np.zeros((h, w), dtype=bool)
        edges[:, 1:] |= labels[:, 1:] != labels[:, :-1]
        edges[1:, :] |= labels[1:, :] != labels[:-1, :]
        if border_width > 1 and _scipy_ndimage is not None:
            edges = _scipy_ndimage.binary_dilation(edges, iterations=border_width - 1)
        elif border_width > 1:
            expanded = edges.copy()
            for _ in range(border_width - 1):
                grown = expanded.copy()
                grown[:, 1:] |= expanded[:, :-1]
                grown[:, :-1] |= expanded[:, 1:]
                grown[1:, :] |= expanded[:-1, :]
                grown[:-1, :] |= expanded[1:, :]
                expanded = grown
            edges = expanded
        out = out.copy()
        out[edges] = border

    return Image.fromarray(out.astype(np.uint8), mode="RGB")


def triangle_mosaic(
    img: Image.Image | ArrayLike,
    tile_size: int = 32,
    border_color=None,
) -> Image.Image:
    """Create a triangular mosaic using a regular square grid split by diagonals."""
    arr = _as_rgb_array(img)
    h, w, _ = arr.shape
    out = np.zeros_like(arr)
    border = _normalize_color(border_color)

    for y0 in range(0, h, tile_size):
        for x0 in range(0, w, tile_size):
            y1 = min(y0 + tile_size, h)
            x1 = min(x0 + tile_size, w)
            region = arr[y0:y1, x0:x1]
            rh, rw = region.shape[:2]
            yy, xx = np.indices((rh, rw), dtype=np.float32)
            diag = (yy + 0.5) / rh >= (xx + 0.5) / rw
            tri_a = region[diag]
            tri_b = region[~diag]
            color_a = tri_a.mean(axis=0).astype(np.uint8) if tri_a.size else region[0, 0]
            color_b = tri_b.mean(axis=0).astype(np.uint8) if tri_b.size else region[-1, -1]
            out[y0:y1, x0:x1][diag] = color_a
            out[y0:y1, x0:x1][~diag] = color_b
            if border is not None:
                out[y0, x0:x1] = border
                out[y0:y1, x0] = border
                diagonal_mask = np.abs((yy + 0.5) / rh - (xx + 0.5) / rw) <= (1.0 / max(rh, rw))
                out[y0:y1, x0:x1][diagonal_mask] = border

    return Image.fromarray(out.astype(np.uint8), mode="RGB")


def generate_tile_map(mosaic_img: Image.Image | ArrayLike, tile_size: int) -> dict[tuple[int, int], tuple[int, int, int]]:
    """Return a grid-to-color mapping sampled from a mosaic image."""
    arr = _as_rgb_array(mosaic_img)
    h, w, _ = arr.shape
    tile_map: dict[tuple[int, int], tuple[int, int, int]] = {}
    for row, y0 in enumerate(range(0, h, tile_size)):
        for col, x0 in enumerate(range(0, w, tile_size)):
            region = arr[y0 : min(y0 + tile_size, h), x0 : min(x0 + tile_size, w)]
            color = np.mean(region.reshape(-1, 3), axis=0).astype(np.uint8)
            tile_map[(row, col)] = tuple(int(v) for v in color)
    return tile_map


def _parse_color(value: str | None):
    if value is None:
        return None
    value = value.strip()
    if value.startswith("#") and len(value) == 7:
        return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))
    parts = [int(p.strip()) for p in value.split(",")]
    if len(parts) != 3:
        raise ValueError("Color must be '#RRGGBB' or 'R,G,B'")
    return tuple(parts)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate square, hex, triangle, or Voronoi mosaics.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", help="Output image path")
    parser.add_argument("--type", choices=["square", "hex", "voronoi", "triangle"], default="square")
    parser.add_argument("--size", type=int, default=20, help="Tile or hex size")
    parser.add_argument("--method", choices=["average", "dominant", "center"], default="average")
    parser.add_argument("--brick-offset", action="store_true", help="Offset alternate rows for square mosaics")
    parser.add_argument("--border-color", type=str, default=None, help="Border color as '#RRGGBB' or 'R,G,B'")
    parser.add_argument("--border-width", type=int, default=1, help="Border width")
    parser.add_argument("--pointy-top", action="store_true", help="Use pointy-top hexagons")
    parser.add_argument("--flat-top", action="store_true", help="Use flat-top hexagons")
    parser.add_argument("--seeds", type=int, default=200, help="Seed count for Voronoi mosaics")
    parser.add_argument(
        "--seed-distribution",
        choices=["random", "edge_weighted"],
        default="random",
        help="Voronoi seed placement strategy",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    image = Image.open(args.input).convert("RGB")
    border_color = _parse_color(args.border_color)

    if args.type == "square":
        result = square_mosaic(
            image,
            tile_size=args.size,
            method=args.method,
            brick_offset=args.brick_offset,
            border_color=border_color,
            border_width=args.border_width,
        )
    elif args.type == "hex":
        pointy_top = True if not args.flat_top else False
        if args.pointy_top:
            pointy_top = True
        result = hex_mosaic(image, hex_size=args.size, pointy_top=pointy_top, border_color=border_color)
    elif args.type == "voronoi":
        result = voronoi_mosaic(
            image,
            n_seeds=args.seeds,
            seed_distribution=args.seed_distribution,
            border_color=border_color,
            border_width=args.border_width,
        )
    else:
        result = triangle_mosaic(image, tile_size=args.size, border_color=border_color)

    result.save(args.output)


if __name__ == "__main__":
    main()
