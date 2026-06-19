#!/usr/bin/env python3
"""blue_noise_generator.py — generate tileable blue-noise textures.

Two methods:
  void-and-cluster (Ulichney, 1993) — the reference algorithm. Produces a
      ranking of every pixel such that any threshold gives a well-distributed
      (blue-noise) dot pattern. Slower but highest quality.
  fft — high-pass filtered white noise, iteratively matched toward a blue
      spectrum. Fast, good enough for grain/dither, not perfectly optimal.

Output is an 8-bit grayscale PNG holding the normalized rank (0..255), tileable
by construction (all neighborhood math wraps toroidally).

Examples
--------
    python blue_noise_generator.py bn64.png --size 64 --method void-cluster
    python blue_noise_generator.py bn256.png --size 256 --method fft
    python blue_noise_generator.py bn_anim --size 64 --frames 16   # 3D stack
"""
from __future__ import annotations

import argparse

import numpy as np

from halftone_common import save_image

try:
    from scipy.ndimage import gaussian_filter

    def _blur(a, sigma):
        return gaussian_filter(a, sigma=sigma, mode="wrap")
except Exception:  # pragma: no cover - scipy optional
    def _blur(a, sigma):
        """Toroidal Gaussian blur via FFT (fallback when scipy is absent)."""
        h, w = a.shape
        ys = np.fft.fftfreq(h)[:, None]
        xs = np.fft.fftfreq(w)[None, :]
        g = np.exp(-2 * (np.pi * sigma) ** 2 * (xs ** 2 + ys ** 2))
        return np.real(np.fft.ifft2(np.fft.fft2(a) * g))


def void_and_cluster(size: int, rng) -> np.ndarray:
    """Ulichney void-and-cluster. Returns a rank array (0..size*size-1)."""
    n = size * size
    sigma = 1.5

    # 1) Initial binary pattern (~10% ones), random.
    pattern = np.zeros((size, size), dtype=bool)
    n_init = max(n // 10, 1)
    idx = rng.choice(n, n_init, replace=False)
    pattern.flat[idx] = True

    def tightest_cluster(pat):
        density = _blur(pat.astype(float), sigma)
        density[~pat] = -np.inf
        return np.unravel_index(np.argmax(density), pat.shape)

    def largest_void(pat):
        density = _blur(pat.astype(float), sigma)
        density[pat] = np.inf
        return np.unravel_index(np.argmin(density), pat.shape)

    # 2) Spread the initial points to be maximally uniform.
    while True:
        c = tightest_cluster(pattern)
        pattern[c] = False
        v = largest_void(pattern)
        pattern[v] = True
        if c == v:
            break

    ranks = np.zeros((size, size), dtype=np.int64)
    initial = pattern.copy()

    # 3) Phase I: remove tightest clusters, ranking downward from n_ones-1.
    work = initial.copy()
    ones = int(work.sum())
    for rank in range(ones - 1, -1, -1):
        c = tightest_cluster(work)
        work[c] = False
        ranks[c] = rank

    # 4) Phase II: fill largest voids, ranking upward from n_ones.
    work = initial.copy()
    for rank in range(ones, n):
        v = largest_void(work)
        work[v] = True
        ranks[v] = rank

    return ranks


def fft_blue_noise(size: int, rng, iters: int = 50) -> np.ndarray:
    """High-pass-shaped white noise, ranked to a uniform histogram."""
    ys = np.fft.fftfreq(size)[:, None]
    xs = np.fft.fftfreq(size)[None, :]
    radius = np.sqrt(xs ** 2 + ys ** 2)
    # Target spectrum: rises with frequency, zero at DC (blue).
    target = radius / radius.max()

    noise = rng.standard_normal((size, size))
    for _ in range(iters):
        spec = np.fft.fft2(noise)
        mag = np.abs(spec)
        mag[mag == 0] = 1e-6
        # Impose blue magnitude, keep phase.
        spec = spec / mag * target
        noise = np.real(np.fft.ifft2(spec))
        # Re-uniformize the histogram (preserves perceptual evenness).
        order = noise.argsort(axis=None)
        ranks = np.empty(size * size)
        ranks[order] = np.linspace(0, 1, size * size)
        noise = ranks.reshape(size, size)
    return (noise * (size * size - 1)).astype(np.int64)


def generate(size: int, method: str, rng) -> np.ndarray:
    if method == "void-cluster":
        ranks = void_and_cluster(size, rng)
    else:
        ranks = fft_blue_noise(size, rng)
    return ranks.astype(np.float64) / (size * size - 1)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("output", help="output PNG (or prefix when --frames > 1)")
    p.add_argument("--size", type=int, default=64)
    p.add_argument("--method", choices=["void-cluster", "fft"], default="void-cluster")
    p.add_argument("--frames", type=int, default=1,
                   help="generate a stack of N decorrelated frames (3D blue noise)")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    if args.size > 128 and args.method == "void-cluster":
        print("note: void-cluster at >128 px is slow; consider --method fft")

    rng = np.random.default_rng(args.seed)
    if args.frames > 1:
        prefix = args.output[:-4] if args.output.endswith(".png") else args.output
        for f in range(args.frames):
            tex = generate(args.size, args.method, rng)
            path = f"{prefix}_{f:03d}.png"
            save_image(tex, path)
            print(f"wrote {path}")
    else:
        tex = generate(args.size, args.method, rng)
        save_image(tex, args.output)
        print(f"wrote {args.output}  ({args.size}x{args.size}, {args.method})")


if __name__ == "__main__":
    main()
