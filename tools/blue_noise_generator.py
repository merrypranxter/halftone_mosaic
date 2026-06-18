#!/usr/bin/env python3
"""Blue-noise texture generation built with NumPy and Pillow."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


ArrayLike = np.ndarray


def _normalize(array: ArrayLike) -> ArrayLike:
    array = np.asarray(array, dtype=np.float32)
    amin = float(array.min(initial=0.0))
    amax = float(array.max(initial=1.0))
    if amax - amin < 1e-8:
        return np.zeros_like(array, dtype=np.float32)
    return (array - amin) / (amax - amin)


def _gaussian_kernel(width: int, height: int, sigma: float = 1.5) -> ArrayLike:
    yy = np.minimum(np.arange(height), height - np.arange(height)).astype(np.float32)
    xx = np.minimum(np.arange(width), width - np.arange(width)).astype(np.float32)
    dy2 = yy[:, None] ** 2
    dx2 = xx[None, :] ** 2
    kernel = np.exp(-(dx2 + dy2) / (2.0 * sigma * sigma)).astype(np.float32)
    return kernel


def _periodic_energy(pattern: ArrayLike, kernel_fft: ArrayLike) -> ArrayLike:
    return np.fft.ifft2(np.fft.fft2(pattern.astype(np.float32)) * kernel_fft).real.astype(np.float32)


def generate_blue_noise_void_cluster(width: int = 64, height: int = 64, seed: int = 0) -> ArrayLike:
    """Generate a tileable blue-noise ranking with a void-and-cluster style process."""
    rng = np.random.default_rng(seed)
    total = width * height
    initial_ones = max(1, int(total * 0.1))

    pattern = np.zeros((height, width), dtype=np.uint8)
    chosen = rng.choice(total, size=initial_ones, replace=False)
    pattern.flat[chosen] = 1

    kernel_fft = np.fft.fft2(_gaussian_kernel(width, height, sigma=1.5))
    ranks = np.empty((height, width), dtype=np.int32)

    active = pattern.copy()
    remaining = int(active.sum())
    while remaining > 0:
        energy = _periodic_energy(active, kernel_fft)
        masked = np.where(active == 1, energy, -np.inf)
        idx = int(np.argmax(masked))
        y, x = divmod(idx, width)
        ranks[y, x] = remaining - 1
        active[y, x] = 0
        remaining -= 1

    active.fill(0)
    for rank in range(initial_ones, total):
        energy = _periodic_energy(active, kernel_fft)
        masked = np.where(active == 0, energy, np.inf)
        idx = int(np.argmin(masked))
        y, x = divmod(idx, width)
        ranks[y, x] = rank
        active[y, x] = 1

    return ranks.astype(np.float32) / float(max(total - 1, 1))


def generate_blue_noise_fft(width: int = 64, height: int = 64, seed: int = 0) -> ArrayLike:
    """Generate blue-noise-like texture using a high-pass FFT filter."""
    rng = np.random.default_rng(seed)
    white = rng.normal(size=(height, width)).astype(np.float32)
    spectrum = np.fft.fft2(white)

    fy = np.fft.fftfreq(height)[:, None]
    fx = np.fft.fftfreq(width)[None, :]
    radius = np.sqrt(fx * fx + fy * fy)
    cutoff = 0.08
    spectrum[radius < cutoff] = 0

    filtered = np.fft.ifft2(spectrum).real.astype(np.float32)
    return _normalize(filtered)


def generate_tileable_blue_noise(width: int = 64, height: int = 64, seed: int = 0) -> ArrayLike:
    """Generate tileable blue noise using toroidal void-and-cluster energy."""
    return generate_blue_noise_void_cluster(width=width, height=height, seed=seed)


def generate_animated_blue_noise(width: int = 64, height: int = 64, frames: int = 16) -> ArrayLike:
    """Generate a 3D blue-noise volume where XY and frame-Z are high-pass filtered."""
    rng = np.random.default_rng(0)
    volume = rng.normal(size=(frames, height, width)).astype(np.float32)
    spectrum = np.fft.fftn(volume)

    fz = np.fft.fftfreq(frames)[:, None, None]
    fy = np.fft.fftfreq(height)[None, :, None]
    fx = np.fft.fftfreq(width)[None, None, :]
    radius = np.sqrt(fx * fx + fy * fy + fz * fz)
    cutoff = 0.08
    spectrum[radius < cutoff] = 0

    filtered = np.fft.ifftn(spectrum).real.astype(np.float32)
    return _normalize(filtered)


def save_blue_noise(array: ArrayLike, output_path: str | Path) -> None:
    """Save a normalized 2D blue-noise array as a grayscale PNG."""
    arr = _normalize(array)
    img = Image.fromarray((arr * 255).astype(np.uint8), mode="L")
    img.save(output_path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate blue-noise textures.")
    parser.add_argument("--method", choices=["void_cluster", "fft", "tileable", "animated"], default="void_cluster")
    parser.add_argument("--size", type=int, default=128, help="Square texture size")
    parser.add_argument("--width", type=int, default=None, help="Texture width")
    parser.add_argument("--height", type=int, default=None, help="Texture height")
    parser.add_argument("--seed", type=int, default=0, help="Random seed")
    parser.add_argument("--frames", type=int, default=16, help="Frame count for animated output")
    parser.add_argument("--output", required=True, help="Output image path")
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    width = args.width or args.size
    height = args.height or args.size

    if args.method == "void_cluster":
        arr = generate_blue_noise_void_cluster(width=width, height=height, seed=args.seed)
        save_blue_noise(arr, args.output)
    elif args.method == "fft":
        arr = generate_blue_noise_fft(width=width, height=height, seed=args.seed)
        save_blue_noise(arr, args.output)
    elif args.method == "tileable":
        arr = generate_tileable_blue_noise(width=width, height=height, seed=args.seed)
        save_blue_noise(arr, args.output)
    else:
        arr = generate_animated_blue_noise(width=width, height=height, frames=args.frames)
        frames = [Image.fromarray((frame * 255).astype(np.uint8), mode="L") for frame in arr]
        if args.output.lower().endswith(".gif"):
            frames[0].save(args.output, save_all=True, append_images=frames[1:], duration=80, loop=0)
        else:
            frames[0].save(args.output)


if __name__ == "__main__":
    main()
