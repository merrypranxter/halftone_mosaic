# Dithering Algorithms

Dithering is the art of spending spatial noise to buy tonal illusion. When an output device cannot reproduce every possible tone directly, it must fake missing values with patterns. A one-bit printer can place black or leave white; a low-color display can choose only a few palette entries; a shader may deliberately quantize for style. Dithering converts those hard limits into a texture that the eye averages into something smoother than the device can truly render.

## Historical Background

The conceptual roots of dithering go back to analog signal processing, where controlled noise could linearize or decorrelate quantization errors. In other words, adding or shaping noise sometimes produced a perceptually better or statistically cleaner result than leaving quantization error to fall where it may.

That idea moved into image processing in the 1970s. Judice, Lippman, and Jarvis published influential work in 1976 on distributed processing of quantization error, helping establish what became the family of error-diffusion methods. In the same year, Robert Floyd and Louis Steinberg introduced the now-famous Floyd-Steinberg algorithm, a computationally elegant method that became the canonical example of error diffusion. In 1984, Bill Atkinson developed the dither used in the original Apple Macintosh graphics environment, favoring a softer, more diffuse look over strict error conservation.

These methods emerged because early printers and displays were limited, but the problem has never gone away. Even today, dithering matters in printing, texture generation, scientific visualization, palette reduction, retro aesthetics, and stylized rendering.

## The Fundamental Problem

The core problem is straightforward: how do you represent continuous tone with binary or otherwise limited output states? Suppose a pixel wants to be 40% gray, but the device can produce only black or white. If you simply threshold it, the answer becomes brutally wrong: below the threshold it becomes white, above it becomes black. A gradient turns into banding.

Dithering solves this by using neighborhoods rather than isolated pixels. Instead of asking what value one pixel should become in isolation, it asks what pattern of nearby black and white pixels will average to the desired tone. If 40% of the pixels in a region are black and 60% are white, the region may read as 40% gray at normal viewing distance.

## Ordered Dithering

Ordered dithering uses a threshold matrix, or dither matrix, tiled across the image. Each input pixel is compared against the matrix value at its location. Because the thresholds vary spatially, different tone levels turn on different subsets of pixels.

The most famous ordered dither is the Bayer matrix. Bayer matrices are recursively constructed so that each threshold level is distributed as evenly as possible over the tile. One recursive form is:

\[
M_{2n} = \begin{bmatrix}
4M_n + 0 & 4M_n + 2 \\
4M_n + 3 & 4M_n + 1
\end{bmatrix}
\]

Starting from the 2×2 base matrix:

```text
0 2
3 1
```

The 4×4 Bayer matrix becomes:

```text
0  8  2 10
12 4 14  6
3 11  1  9
15 7 13  5
```

The 8×8 Bayer matrix is:

```text
0  32  8 40  2 34 10 42
48 16 56 24 50 18 58 26
12 44  4 36 14 46  6 38
60 28 52 20 62 30 54 22
3  35 11 43  1 33  9 41
51 19 59 27 49 17 57 25
15 47  7 39 13 45  5 37
63 31 55 23 61 29 53 21
```

In implementation, these integer entries are normalized into threshold values. As the input tone increases, more matrix positions cross threshold and become dark. Because the matrix repeats periodically, ordered dithering creates a visible regular texture. In Bayer dithering that texture often appears as a cross-hatch, checker, or diagonal weave. This structured pattern is aesthetically useful in some contexts, but it can be distracting when the goal is photographic naturalism.

Ordered dithering is fast, deterministic, memory-light, and highly parallelizable. That makes it attractive in shaders and real-time systems.

## Error Diffusion: General Framework

Error diffusion takes a different approach. Instead of consulting a prebuilt threshold pattern, it processes pixels sequentially. For each pixel, it:

1. Adds any accumulated error from previously processed neighbors.
2. Quantizes the adjusted value to the nearest allowed output.
3. Computes the quantization error.
4. Distributes that error to nearby pixels that have not yet been processed.

This makes the algorithm locally self-correcting. If a pixel was forced too dark, its neighbors are nudged lighter; if it was forced too light, neighbors are nudged darker. The total average tone is therefore preserved better than with plain thresholding.

## Floyd-Steinberg

Floyd-Steinberg is the classic compact kernel. Scanning left to right, it distributes error as follows:

- right = 7/16
- below-left = 3/16
- below = 5/16
- below-right = 1/16

The sum is 16/16, so the entire error is conserved. This makes the method tonally faithful and efficient. However, because the diffusion is directional and local, the algorithm tends to produce characteristic streaking or "worms" aligned with the scan order. These artifacts are especially visible in flat tones and shallow gradients. The result can be beautiful, gritty, and organic, but it is unmistakably algorithmic.

## Atkinson

The Atkinson algorithm, associated with the Apple Macintosh in 1984, distributes error to six neighbors at 1/8 each. Only 6/8 of the error is passed forward, so some error effectively bleeds away instead of being strictly conserved.

A common Atkinson neighborhood includes the pixels to the right, two to the right, below-left, below, below-right, and two rows below. Because it diffuses less total error than Floyd-Steinberg, the result is lighter, more open, and less aggressively compensated. Visually, Atkinson often appears more diffuse and less structured. It sacrifices some tonal precision for a pleasing, iconic look, which is part of why classic Macintosh graphics feel distinct.

## Jarvis-Judice-Ninke

Jarvis-Judice-Ninke, often abbreviated JJN, uses a larger kernel covering 12 forward neighbors over multiple rows. The larger spread produces smoother gradients and reduces some of the coarse artifacts seen in simpler methods. The cost is increased computation, more memory traffic, and broader error influence that can soften detail if not carefully applied. JJN is often considered a high-quality classical error diffusion algorithm when speed is less critical.

## Sierra Variants

The Sierra family offers alternative kernels that balance quality and cost.

- **Sierra-3** uses a larger, fuller kernel and produces smooth results comparable to JJN.
- **Sierra-2** reduces the footprint and computational effort while preserving much of the quality.
- **Sierra-2-4A** is the lightweight version, sometimes called Sierra Lite, intended for efficient implementations.

These variants are useful because they expose the design space of error diffusion: larger kernels can reduce artifacts but cost more; smaller kernels are faster but more stylized.

## Stevenson-Arce

Stevenson-Arce was designed to minimize structured artifacts by using a wider and less obviously directional diffusion pattern. It is less commonly encountered in everyday tooling than Floyd-Steinberg, but it is important historically because it illustrates that error diffusion need not accept worm-like structure as inevitable. With enough kernel design effort, artifacts can be redistributed into textures that feel less mechanical.

## Blue Noise Dithering

Blue noise dithering occupies a middle ground between ordered and diffused methods. One common version thresholds the image against a blue noise texture: a precomputed array whose spatial frequencies are concentrated at the high end. Unlike Bayer matrices, blue noise textures lack strong low-frequency periodic structure. Unlike sequential error diffusion, they can be applied in parallel and do not depend on scan order.

Why is this attractive? Human vision is highly sensitive to low-frequency structure: bands, grids, stripes, and clumps are immediately visible. High-frequency noise is easier for the visual system to ignore or average. Blue noise therefore produces grain-like texture that looks less synthetic than white noise and less patterned than ordered dithering.

## Serpentine Scanning

A major issue in error diffusion is directional bias. If every row is processed left to right, artifacts tend to lean in that direction. Serpentine scanning reduces this bias by alternating direction on successive rows: left to right on one row, right to left on the next. The kernel is mirrored accordingly. This does not eliminate artifacts, but it prevents the image from developing a single dominant directional texture and generally improves isotropy.

## Comparison Table

| Algorithm | Type | Cost | Noise Character | Typical Artifacts | Notes |
|---|---|---:|---|---|---|
| Threshold only | None | Very low | Harsh contouring | Severe banding | Useful only for hard-edge graphics |
| Bayer 2×2 / 4×4 / 8×8 | Ordered | Low | Periodic, structured | Cross-hatch, checker repetition | Fast, shader-friendly |
| Floyd-Steinberg | Error diffusion | Low-moderate | Organic, locally adaptive | Worms, scan-direction streaks | Canonical general-purpose method |
| Atkinson | Error diffusion | Low-moderate | Open, diffuse | Slight loss of tonal accuracy | Classic Macintosh aesthetic |
| Jarvis-Judice-Ninke | Error diffusion | High | Smooth, spread | Softer detail, broader texture | High quality but expensive |
| Sierra-3 | Error diffusion | High | Smooth | Mild structured drift | Balanced alternative to JJN |
| Sierra-2 | Error diffusion | Moderate | Smooth | Some residual directional pattern | Efficient compromise |
| Sierra-2-4A | Error diffusion | Low | Coarser, lighter | More visible artifacting than larger Sierra | Good for real-time or constrained systems |
| Stevenson-Arce | Error diffusion | High | Less directional | Fewer obvious worms | Designed for reduced structure |
| Blue noise thresholding | Noise-masked | Low after precompute | Fine, grain-like | Minimal low-frequency pattern | Excellent perceptual behavior |

## Why Dithering Remains Relevant

Dithering persists because it is not merely a workaround for obsolete hardware. It is a language of texture. In print, it defines how dots turn into tone. In games, it creates atmosphere, stylization, and efficient transparency tricks. In scientific and artistic imaging, it lets limited channels imply richer continua. And in a halftone or mosaic art repository, dithering is one of the most important ways to decide what kind of lie the image tells: rigid grid, wandering worm, diffuse grain, or something closer to visual silence.
