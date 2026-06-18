#!/usr/bin/env python3
"""Image dithering algorithms built with NumPy and Pillow."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image


ArrayLike = np.ndarray


def _to_float_array(img_array: ArrayLike) -> ArrayLike:
    arr = np.asarray(img_array, dtype=np.float32)
    if arr.max(initial=0.0) > 1.0 or arr.min(initial=0.0) < 0.0:
        arr = arr / 255.0
    return np.clip(arr, 0.0, 1.0)


def _apply_per_channel(img_array: ArrayLike, fn):
    arr = _to_float_array(img_array)
    if arr.ndim == 2:
        return fn(arr)
    if arr.ndim == 3:
        return np.stack([fn(arr[..., c]) for c in range(arr.shape[2])], axis=-1)
    raise ValueError("Expected a 2D grayscale or 3D RGB image array.")


def _quantize_value(value: ArrayLike, levels: int) -> ArrayLike:
    if levels < 2:
        raise ValueError("levels must be at least 2")
    return np.round(np.clip(value, 0.0, 1.0) * (levels - 1)) / float(levels - 1)


def bayer_matrix(n: int) -> ArrayLike:
    """Generate a normalized Bayer matrix of size 2**n x 2**n."""
    if n < 1:
        raise ValueError("n must be >= 1")
    matrix = np.array([[0, 2], [3, 1]], dtype=np.float32)
    for _ in range(2, n + 1):
        matrix = np.block(
            [
                [4 * matrix, 4 * matrix + 2],
                [4 * matrix + 3, 4 * matrix + 1],
            ]
        )
    return matrix / float(4**n)


def apply_bayer(img_array: ArrayLike, levels: int = 2, matrix_size: int = 8) -> ArrayLike:
    """Apply ordered Bayer dithering."""
    if matrix_size < 2 or matrix_size & (matrix_size - 1):
        raise ValueError("matrix_size must be a power of two >= 2")
    n = int(math.log2(matrix_size))
    matrix = bayer_matrix(n)

    def _dither(channel: ArrayLike) -> ArrayLike:
        h, w = channel.shape
        yy, xx = np.indices((h, w))
        threshold = matrix[yy % matrix_size, xx % matrix_size]
        adjusted = np.clip(channel + (threshold - 0.5) / levels, 0.0, 1.0)
        indices = np.floor(adjusted * levels).astype(np.int32)
        indices = np.clip(indices, 0, levels - 1)
        return indices / float(levels - 1)

    return _apply_per_channel(img_array, _dither)


def _error_diffusion(channel: ArrayLike, levels: int, kernel, serpentine: bool = True) -> ArrayLike:
    work = _to_float_array(channel).copy()
    h, w = work.shape

    for y in range(h):
        reverse = serpentine and (y % 2 == 1)
        x_range = range(w - 1, -1, -1) if reverse else range(w)
        for x in x_range:
            old = work[y, x]
            new = _quantize_value(old, levels)
            work[y, x] = new
            err = old - new
            for dx, dy, weight in kernel:
                offset_x = -dx if reverse else dx
                ny = y + dy
                nx = x + offset_x
                if 0 <= ny < h and 0 <= nx < w:
                    work[ny, nx] += err * weight

    return np.clip(work, 0.0, 1.0)


def apply_floyd_steinberg(img_array: ArrayLike, levels: int = 2) -> ArrayLike:
    """Apply Floyd-Steinberg error diffusion with serpentine scanning."""
    kernel = [
        (1, 0, 7 / 16),
        (-1, 1, 3 / 16),
        (0, 1, 5 / 16),
        (1, 1, 1 / 16),
    ]
    return _apply_per_channel(img_array, lambda channel: _error_diffusion(channel, levels, kernel, serpentine=True))


def apply_atkinson(img_array: ArrayLike, levels: int = 2) -> ArrayLike:
    """Apply Atkinson dithering."""
    kernel = [
        (1, 0, 1 / 8),
        (2, 0, 1 / 8),
        (-1, 1, 1 / 8),
        (0, 1, 1 / 8),
        (1, 1, 1 / 8),
        (0, 2, 1 / 8),
    ]
    return _apply_per_channel(img_array, lambda channel: _error_diffusion(channel, levels, kernel, serpentine=True))


def apply_jarvis(img_array: ArrayLike, levels: int = 2) -> ArrayLike:
    """Apply Jarvis-Judice-Ninke dithering."""
    kernel = [
        (1, 0, 7 / 48),
        (2, 0, 5 / 48),
        (-2, 1, 3 / 48),
        (-1, 1, 5 / 48),
        (0, 1, 7 / 48),
        (1, 1, 5 / 48),
        (2, 1, 3 / 48),
        (-2, 2, 1 / 48),
        (-1, 2, 3 / 48),
        (0, 2, 5 / 48),
        (1, 2, 3 / 48),
        (2, 2, 1 / 48),
    ]
    return _apply_per_channel(img_array, lambda channel: _error_diffusion(channel, levels, kernel, serpentine=True))


def apply_sierra(img_array: ArrayLike, levels: int = 2) -> ArrayLike:
    """Apply Sierra-3 dithering."""
    kernel = [
        (1, 0, 5 / 32),
        (2, 0, 3 / 32),
        (-2, 1, 2 / 32),
        (-1, 1, 4 / 32),
        (0, 1, 5 / 32),
        (1, 1, 4 / 32),
        (2, 1, 2 / 32),
        (-1, 2, 2 / 32),
        (0, 2, 3 / 32),
        (1, 2, 2 / 32),
    ]
    return _apply_per_channel(img_array, lambda channel: _error_diffusion(channel, levels, kernel, serpentine=True))


def apply_blue_noise(img_array: ArrayLike, levels: int = 2, noise_texture: ArrayLike | None = None) -> ArrayLike:
    """Apply blue-noise-like threshold dithering."""
    def _dither(channel: ArrayLike) -> ArrayLike:
        h, w = channel.shape
        yy, xx = np.indices((h, w), dtype=np.float32)
        if noise_texture is None:
            noise = np.mod(
                52.9829189
                * np.mod(0.06711056 * xx + 0.00583715 * yy, 1.0),
                1.0,
            )
        else:
            texture = _to_float_array(noise_texture)
            if texture.ndim == 3:
                texture = texture[..., 0]
            th, tw = texture.shape
            noise = texture[yy.astype(np.int32) % th, xx.astype(np.int32) % tw]
        adjusted = np.clip(channel + (noise - 0.5) / levels, 0.0, 1.0)
        indices = np.floor(adjusted * levels).astype(np.int32)
        indices = np.clip(indices, 0, levels - 1)
        return indices / float(levels - 1)

    return _apply_per_channel(img_array, _dither)


def dither_image(
    image_path: str | Path,
    output_path: str | Path,
    algorithm: str = "floyd_steinberg",
    levels: int = 2,
    **kwargs,
) -> None:
    """Load, dither, and save an image."""
    image = Image.open(image_path)
    if image.mode not in {"L", "RGB"}:
        image = image.convert("RGB")
    arr = np.asarray(image, dtype=np.float32) / 255.0

    algorithms = {
        "bayer": apply_bayer,
        "floyd_steinberg": apply_floyd_steinberg,
        "atkinson": apply_atkinson,
        "jarvis": apply_jarvis,
        "sierra": apply_sierra,
        "blue_noise": apply_blue_noise,
    }
    if algorithm not in algorithms:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    result = algorithms[algorithm](arr, levels=levels, **kwargs)
    out = (np.clip(result, 0.0, 1.0) * 255).astype(np.uint8)

    if out.ndim == 2:
        Image.fromarray(out, mode="L").save(output_path)
    else:
        Image.fromarray(out, mode="RGB").save(output_path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply dithering algorithms to images.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", help="Output image path")
    parser.add_argument(
        "--algorithm",
        choices=["bayer", "floyd_steinberg", "atkinson", "jarvis", "sierra", "blue_noise"],
        default="floyd_steinberg",
        help="Dithering algorithm",
    )
    parser.add_argument("--levels", type=int, default=2, help="Number of quantization levels")
    parser.add_argument("--matrix-size", type=int, default=8, help="Bayer matrix size")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    kwargs = {"matrix_size": args.matrix_size} if args.algorithm == "bayer" else {}
    dither_image(
        image_path=args.input,
        output_path=args.output,
        algorithm=args.algorithm,
        levels=args.levels,
        **kwargs,
    )


if __name__ == "__main__":
    main()
