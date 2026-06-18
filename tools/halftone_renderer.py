#!/usr/bin/env python3
"""Halftone rendering tools built with NumPy and Pillow."""

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


ArrayLike = np.ndarray


def _as_float_channel(channel: ArrayLike) -> ArrayLike:
    channel = np.asarray(channel, dtype=np.float32)
    if channel.ndim != 2:
        raise ValueError("Expected a 2D grayscale channel.")
    if channel.max(initial=0.0) > 1.0 or channel.min(initial=0.0) < 0.0:
        channel = channel / 255.0
    return np.clip(channel, 0.0, 1.0)


def RGBtoCMYK(img: Image.Image) -> tuple[ArrayLike, ArrayLike, ArrayLike, ArrayLike]:
    """Convert an RGB PIL image to CMYK float arrays in the range [0, 1]."""
    rgb = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    r = rgb[..., 0]
    g = rgb[..., 1]
    b = rgb[..., 2]

    c = 1.0 - r
    m = 1.0 - g
    y = 1.0 - b
    k = np.minimum(np.minimum(c, m), y)

    denom = 1.0 - k
    safe = denom > 1e-8

    c_out = np.zeros_like(c)
    m_out = np.zeros_like(m)
    y_out = np.zeros_like(y)

    c_out[safe] = (c[safe] - k[safe]) / denom[safe]
    m_out[safe] = (m[safe] - k[safe]) / denom[safe]
    y_out[safe] = (y[safe] - k[safe]) / denom[safe]

    return (
        np.clip(c_out, 0.0, 1.0),
        np.clip(m_out, 0.0, 1.0),
        np.clip(y_out, 0.0, 1.0),
        np.clip(k, 0.0, 1.0),
    )


def apply_dot_gain(channel: ArrayLike, gain: float = 0.2) -> ArrayLike:
    """Simulate dot gain / ink spread with a smooth nonlinear curve."""
    channel = _as_float_channel(channel)
    out = channel + gain * channel * (1.0 - channel)
    return np.clip(out, 0.0, 1.0)


def halftone_screen_am(
    channel: ArrayLike,
    lpi: float = 133,
    angle_deg: float = 45.0,
    dot_shape: str = "round",
    paper_size_inches: tuple[float, float] = (8.5, 11),
    dpi: int = 300,
) -> ArrayLike:
    """Generate an AM halftone screen as a binary NumPy array."""
    del paper_size_inches  # Shape follows the input channel resolution.
    channel = _as_float_channel(channel)
    if lpi <= 0:
        raise ValueError("lpi must be positive.")

    h, w = channel.shape
    y, x = np.indices((h, w), dtype=np.float32)

    theta = math.radians(angle_deg)
    rotated_x = x * math.cos(theta) + y * math.sin(theta)
    rotated_y = -x * math.sin(theta) + y * math.cos(theta)

    cell_size = float(dpi) / float(lpi)
    cell_x = np.mod(rotated_x, cell_size) / cell_size - 0.5
    cell_y = np.mod(rotated_y, cell_size) / cell_size - 0.5

    tone = np.clip(channel, 0.0, 1.0)
    dot_shape = dot_shape.lower()
    size_term = np.sqrt(tone)

    if dot_shape == "round":
        dot_radius = 0.5 * size_term
        mask = (cell_x * cell_x + cell_y * cell_y) < (dot_radius * dot_radius)
    elif dot_shape == "square":
        half_extent = 0.5 * size_term
        mask = (np.abs(cell_x) < half_extent) & (np.abs(cell_y) < half_extent)
    elif dot_shape == "elliptical":
        semi_major = 0.5 * size_term
        semi_minor = np.maximum(semi_major / 2.0, 1e-6)
        mask = ((cell_x / np.maximum(semi_major, 1e-6)) ** 2 + (cell_y / semi_minor) ** 2) < 1.0
    else:
        raise ValueError("dot_shape must be one of: round, square, elliptical")

    return mask.astype(np.uint8)


def _manual_binary_dilation(binary: ArrayLike, dot_size: int) -> ArrayLike:
    radius = max(0, int(dot_size) // 2)
    if radius == 0:
        return binary.astype(bool)

    h, w = binary.shape
    padded = np.pad(binary.astype(bool), radius, mode="constant")
    out = np.zeros((h, w), dtype=bool)
    rr, cc = np.indices((2 * radius + 1, 2 * radius + 1))
    disk = (rr - radius) ** 2 + (cc - radius) ** 2 <= radius * radius

    for dy in range(2 * radius + 1):
        for dx in range(2 * radius + 1):
            if not disk[dy, dx]:
                continue
            out |= padded[dy : dy + h, dx : dx + w]
    return out


def halftone_screen_fm(channel: ArrayLike, dot_size: int = 3, density_seed: int = 0) -> ArrayLike:
    """Generate an FM / stochastic halftone screen."""
    tone = _as_float_channel(channel)
    rng = np.random.default_rng(density_seed)
    binary = rng.random(tone.shape, dtype=np.float32) < tone

    if dot_size > 1:
        if _scipy_ndimage is not None:
            radius = max(0, int(dot_size) // 2)
            rr, cc = np.indices((2 * radius + 1, 2 * radius + 1))
            structure = (rr - radius) ** 2 + (cc - radius) ** 2 <= radius * radius
            binary = _scipy_ndimage.binary_dilation(binary, structure=structure)
        else:
            binary = _manual_binary_dilation(binary, dot_size)

    return binary.astype(np.uint8)


def _save_binary_as_grayscale(binary: ArrayLike, output_path: str | Path) -> None:
    image = Image.fromarray((1 - np.asarray(binary, dtype=np.uint8)) * 255, mode="L")
    image.save(output_path)


def render_cmyk_halftone(
    image_path: str | Path,
    output_path: str | Path,
    lpi: float = 133,
    dot_shape: str = "round",
    dot_gain: float = 0.15,
) -> None:
    """Render a CMYK halftone composite from an input image."""
    img = Image.open(image_path).convert("RGB")
    c, m, y, k = RGBtoCMYK(img)

    channels = {
        "C": apply_dot_gain(c, dot_gain),
        "M": apply_dot_gain(m, dot_gain),
        "Y": apply_dot_gain(y, dot_gain),
        "K": apply_dot_gain(k, dot_gain),
    }
    angles = {"C": 15.0, "M": 75.0, "Y": 0.0, "K": 45.0}

    screens = {
        name: halftone_screen_am(channel, lpi=lpi, angle_deg=angles[name], dot_shape=dot_shape)
        for name, channel in channels.items()
    }

    c_ink = screens["C"].astype(np.float32)
    m_ink = screens["M"].astype(np.float32)
    y_ink = screens["Y"].astype(np.float32)
    k_ink = screens["K"].astype(np.float32)

    r = (1.0 - c_ink) * (1.0 - k_ink)
    g = (1.0 - m_ink) * (1.0 - k_ink)
    b = (1.0 - y_ink) * (1.0 - k_ink)

    rgb = np.clip(np.stack([r, g, b], axis=-1), 0.0, 1.0)
    Image.fromarray((rgb * 255).astype(np.uint8), mode="RGB").save(output_path)


def render_grayscale_halftone(
    image_path: str | Path,
    output_path: str | Path,
    lpi: float = 133,
    angle_deg: float = 45.0,
    dot_shape: str = "round",
) -> None:
    """Render a grayscale halftone image."""
    img = Image.open(image_path).convert("L")
    gray = np.asarray(img, dtype=np.float32) / 255.0
    ink = 1.0 - gray
    screen = halftone_screen_am(ink, lpi=lpi, angle_deg=angle_deg, dot_shape=dot_shape)
    _save_binary_as_grayscale(screen, output_path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render grayscale or CMYK halftones.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", help="Output image path")
    parser.add_argument("--lpi", type=float, default=133, help="Lines per inch")
    parser.add_argument("--angle-deg", type=float, default=45.0, help="Screen angle for grayscale mode")
    parser.add_argument(
        "--dot-shape",
        choices=["round", "square", "elliptical"],
        default="round",
        help="Halftone dot shape",
    )
    parser.add_argument("--dot-gain", type=float, default=0.15, help="Dot gain for CMYK mode")
    parser.add_argument(
        "--mode",
        choices=["grayscale", "cmyk"],
        default="grayscale",
        help="Rendering mode",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    if args.mode == "cmyk":
        render_cmyk_halftone(
            image_path=args.input,
            output_path=args.output,
            lpi=args.lpi,
            dot_shape=args.dot_shape,
            dot_gain=args.dot_gain,
        )
    else:
        render_grayscale_halftone(
            image_path=args.input,
            output_path=args.output,
            lpi=args.lpi,
            angle_deg=args.angle_deg,
            dot_shape=args.dot_shape,
        )


if __name__ == "__main__":
    main()
