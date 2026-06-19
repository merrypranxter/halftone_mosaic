# Blue Noise

**Blue noise** is noise whose power spectrum is concentrated at high spatial
frequencies and (nearly) empty at low frequencies — the opposite of the
clumpy, low-frequency "white" noise you get from `rand()`. The name borrows
from light: blue light is high frequency.

Spatially, blue noise samples are *evenly spread but not regular*: every point
keeps its neighbours at arm's length (a soft minimum distance, like a Poisson
disk), yet there is no repeating lattice. That combination — uniform coverage
without structure — is exactly what the eye finds least objectionable.

## Why it matters for dithering

When you dither against a threshold map, the eye sees the *spectrum of the
error*, not the values. With blue-noise thresholds the quantization error is
pushed into high frequencies, above the eye's acuity limit, so it reads as fine,
neutral **film grain** with no pattern. Compare:

- **White-noise threshold**: grainy *and* clumpy — low-frequency blotches.
- **Bayer threshold**: smooth but obvious crosshatch structure.
- **Blue-noise threshold**: smooth *and* structureless. Best of both.

This is why blue noise is the modern default for real-time dithering, stippling,
sample placement (rendering), and stochastic transparency.

## Generation methods

### Void-and-cluster (Ulichney, 1993)

The reference algorithm. It produces a *ranking* of every pixel such that
thresholding the rank at any level yields a blue-noise dot pattern.

1. Start from a small random binary pattern.
2. Repeatedly move the point in the **tightest cluster** to the **largest
   void** (found by Gaussian-filtering the pattern and taking max/min) until
   stable — this gives a maximally uniform "prototype".
3. **Phase I**: remove tightest clusters one by one, assigning descending ranks.
4. **Phase II**: fill largest voids one by one, assigning ascending ranks.

All neighbourhood math wraps toroidally, so the texture **tiles seamlessly**.
Slow (each step filters the whole image) but optimal. Implemented in
`tools/blue_noise_generator.py --method void-cluster`.

### FFT / spectral shaping

Filter white noise toward a blue target spectrum and re-uniformize the histogram
each iteration. Fast, decent quality, not perfectly optimal. Good for large
textures where void-and-cluster is too slow.
(`--method fft`.)

### Poisson-disk / dart throwing

Reject samples that fall within radius *r* of an existing one. Produces blue-
noise *point sets* (for stippling/sampling) rather than per-pixel threshold
textures.

## 3D / temporal blue noise

For animation you want each frame to be blue noise **and** the value at a fixed
pixel to be blue noise *over time*, so error doesn't flicker coherently. This is
"3D blue noise" — generate a decorrelated stack (see `--frames`). Used heavily
in real-time rendering (e.g. spatiotemporal blue-noise masks).

## Tiling and texture sizes

Tileable masks of 64², 128², 256² cover most needs; the shader samples with a
wrapped UV (`fract(fragCoord / size)`). Larger tiles reduce visible repetition
at the cost of memory/cache.

## Key references

- R. Ulichney, *Digital Halftoning*, MIT Press, 1987 — the foundational text.
- R. Ulichney, "The void-and-cluster method for dither array generation," 1993.
- Georgiev & Fajardo, "Blue-noise dithered sampling," 2016.
- Heitz & Belcour, spatiotemporal blue-noise masks, 2019+.
- E. Heitz et al., "A low-discrepancy sampler that distributes Monte Carlo
  errors as blue noise," 2019.

## See also
- `dithering_algorithms.md`, `shaders/blue_noise_dither.frag`,
  `tools/blue_noise_generator.py`.
