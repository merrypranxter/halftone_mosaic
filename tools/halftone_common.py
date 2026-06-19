"""Shared helpers for the halftone_mosaic Python tools.

Pure NumPy + Pillow. Images are handled as float arrays in [0, 1]. We keep a
clear distinction between *gamma* (sRGB) space, which is where dithering and
halftoning live perceptually, and *linear* space, which is where averaging /
blurring is physically correct.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

# Palette from the repo seed (handy defaults for tools/notebooks).
PALETTE = {
    "halftone_black": "#000000",
    "halftone_white": "#FFFFFF",
    "cyan": "#00FFFF",
    "magenta": "#FF00FF",
    "yellow": "#FFFF00",
    "newsprint_beige": "#F5F5DC",
    "stained_glass_blue": "#3366CC",
}


def load_image(path: str, mode: str = "RGB") -> np.ndarray:
    """Load an image as a float array in [0, 1] with shape (H, W, C)."""
    img = Image.open(path).convert(mode)
    arr = np.asarray(img, dtype=np.float64) / 255.0
    if arr.ndim == 2:
        arr = arr[..., None]
    return arr


def save_image(arr: np.ndarray, path: str) -> None:
    """Save a float array in [0, 1] (or a 2D gray array) to disk as 8-bit."""
    a = np.clip(arr, 0.0, 1.0)
    a = (a * 255.0 + 0.5).astype(np.uint8)
    if a.ndim == 3 and a.shape[2] == 1:
        a = a[..., 0]
    Image.fromarray(a).save(path)


def to_gray(rgb: np.ndarray) -> np.ndarray:
    """Rec. 709 luminance, shape (H, W)."""
    if rgb.ndim == 2:
        return rgb
    if rgb.shape[2] == 1:
        return rgb[..., 0]
    return rgb[..., :3] @ np.array([0.2126, 0.7152, 0.0722])


def srgb_to_linear(c: np.ndarray) -> np.ndarray:
    """Approximate sRGB -> linear (gamma 2.2)."""
    return np.power(np.clip(c, 0.0, 1.0), 2.2)


def linear_to_srgb(c: np.ndarray) -> np.ndarray:
    """Approximate linear -> sRGB (gamma 1/2.2)."""
    return np.power(np.clip(c, 0.0, 1.0), 1.0 / 2.2)


def rgb_to_cmyk(rgb: np.ndarray) -> np.ndarray:
    """Naive RGB->CMYK separation (no GCR/UCR). Returns (H, W, 4)."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    k = 1.0 - np.maximum.reduce([r, g, b])
    denom = np.clip(1.0 - k, 1e-6, 1.0)
    c = (1.0 - r - k) / denom
    m = (1.0 - g - k) / denom
    y = (1.0 - b - k) / denom
    return np.clip(np.stack([c, m, y, k], axis=-1), 0.0, 1.0)


def cmyk_to_rgb(cmyk: np.ndarray) -> np.ndarray:
    """CMYK -> RGB (inverse of rgb_to_cmyk)."""
    c, m, y, k = cmyk[..., 0], cmyk[..., 1], cmyk[..., 2], cmyk[..., 3]
    r = (1.0 - c) * (1.0 - k)
    g = (1.0 - m) * (1.0 - k)
    b = (1.0 - y) * (1.0 - k)
    return np.clip(np.stack([r, g, b], axis=-1), 0.0, 1.0)


def hex_to_rgb01(h: str) -> np.ndarray:
    """'#RRGGBB' -> float array [r, g, b] in [0, 1]."""
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64) / 255.0
