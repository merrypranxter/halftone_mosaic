# Dithering Algorithms

Dithering quantizes an image to few levels while using *spatial* arrangement of
those levels to preserve the appearance of intermediate tones. Two broad
families: **ordered** (compare each pixel to a fixed threshold map) and **error
diffusion** (push each pixel's quantization error into not-yet-processed
neighbours).

## Ordered dithering (Bayer)

A Bayer matrix is a recursively defined threshold map. The order-2 seed:

```
0 2
3 1   (divide by 4)
```

Each level up quadruples the matrix:

```
M_{2n} = [ 4M+0  4M+2 ]
         [ 4M+3  4M+1 ]   (divide by (2n)^2)
```

The values are a *dispersed-dot* permutation: thresholds that are numerically
close are placed far apart spatially, so turning up brightness lights pixels in
a maximally spread order. The result is the familiar regular crosshatch — cheap,
stable under animation, totally parallel (perfect for GPUs), but with obvious
structure. The Game Boy / early-PC look.

- Pros: O(1) per pixel, no neighbour dependency, temporally stable.
- Cons: visible repeating pattern; the structure fights the image.

`shaders/bayer_ordered_dither.frag`, `tools/dither_applier.py --algo bayer`.

## Error diffusion

Process pixels in scan order; quantize each; spread the residual error to
neighbours by a kernel. Different kernels = different artifacts.

### Floyd–Steinberg (1976)

```
      X   7/16
3/16 5/16 1/16
```

The classic. Smooth gradients, but accumulates error into diagonal **"worms"** —
faint serpentine trails, most visible in flat midtones.

### Atkinson (Apple, MacPaint)

```
     X  1/8 1/8
1/8 1/8 1/8
     1/8
```

Spreads to 6 neighbours but only diffuses **6/8** of the error — the other 2/8
is discarded. That energy loss raises local contrast and suppresses worms,
giving the crisp, slightly blown-out 1-bit Mac look. Great for line-y content,
loses detail in extreme highlights/shadows.

### Jarvis–Judice–Ninke (1976)

```
       X   7/48 5/48
3/48 5/48 7/48 5/48 3/48
1/48 3/48 5/48 3/48 1/48
```

Spreads error over 12 neighbours across 3 rows → smoother, fewer worms than FS,
but softer and slower.

### Sierra (and Sierra-Lite, Two-Row Sierra)

A family tuned to approximate JJN's smoothness with less computation. Three-row
Sierra divides by 32. Good middle ground.

### Stevenson–Arce

A 12-tap kernel (÷200) designed for hexagonal-ish dot placement and very smooth
tone; the heaviest and smoothest of the set.

## Serpentine scanning

Alternating the scan direction every row (left→right, then right→left) prevents
error from always biasing the same direction, which breaks up the diagonal worm
structure of FS. `--serpentine` enables this in `dither_applier.py`.

## Why error diffusion resists the GPU

Pixel N's input depends on the error left by pixel N−1, so the recurrence is
serial along the scan path. A fragment shader computes pixels independently and
out of order. Options:

1. **CPU** (this repo's `dither_applier.py`) — exact, reference quality.
2. **Multi-pass / compute marching** — march scanlines in a compute shader.
3. **Windowed replay** — each fragment re-runs the recurrence over a small block
   ending at itself. Approximate but parallel; what
   `floyd_steinberg_dither.frag` and `atkinson_dither.frag` do.

## Choosing an algorithm

| Goal | Pick |
|---|---|
| Cheap, animatable, retro pattern | Bayer |
| Smooth photographic gradient | Floyd–Steinberg / JJN |
| Crisp 1-bit, high contrast | Atkinson |
| No visible structure, film grain | blue noise (see `blue_noise_research.md`) |

## See also
- `blue_noise_research.md`, `halftone_theory.md`
- `tools/dither_applier.py`, `notebooks/dither_algorithm_explorer.ipynb`
