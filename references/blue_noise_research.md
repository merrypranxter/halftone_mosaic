# Blue Noise Research

Blue noise is one of the most important ideas in modern image synthesis because it answers a perceptual question with spectral engineering: if an image must contain error, where in the frequency domain should that error live so the eye objects as little as possible? The preferred answer, in many cases, is at high spatial frequencies. Blue noise is therefore not just a texture style. It is a carefully shaped distribution of variation whose spectrum suppresses low-frequency structure and pushes energy upward, producing noise that reads as fine grain rather than blotches, bands, or repeated motifs.

## Ulichney's Foundational Work

Robert Ulichney is the central figure in blue-noise dithering literature. His 1988 paper, **"Dithering with Blue Noise,"** established the perceptual and mathematical case for using blue-noise masks instead of more visibly structured threshold arrays. Ulichney showed that dithering quality depends not only on average tone accuracy, but also on the spatial frequency content of the quantization pattern. Patterns with strong low-frequency components are easy to see; patterns whose energy is shifted into high frequencies are far less objectionable.

In 1993, Ulichney followed with **"The Void-and-Cluster Method for Dither Array Generation,"** which provided a practical way to generate threshold arrays exhibiting blue-noise characteristics. This was a major step because it connected the abstract spectral idea to an actual construction algorithm suitable for digital halftoning.

## What "Blue Noise" Means

The term comes from analogy with the visible spectrum. Blue light has shorter wavelength and higher frequency than red light. Likewise, blue noise has power concentrated at high spatial frequencies. It is not literally blue in color; the name refers to its spectral distribution.

This is easiest to understand by contrast:

- **White noise** has a flat spectrum. All spatial frequencies are represented equally on average.
- **Pink noise** has a 1/f spectrum, meaning energy increases toward low frequencies. It is coarse, clumpy, and structurally obvious.
- **Blue noise** suppresses low frequencies and emphasizes high ones. It appears fine-grained and evenly dispersed.

For halftoning and sample distribution, this matters enormously. The eye is sensitive to broad bands, repeated grids, and soft clumps, all of which live in low frequencies. High-frequency error is easier to ignore, especially when the image itself contains meaningful structure.

## Why Blue Noise Looks Better

Human vision is not uniformly sensitive across spatial frequencies. We are especially good at spotting structure, repetition, and smooth low-frequency variation. A Bayer pattern is efficient, but its periodicity produces visible cross-hatch and checker artifacts. White noise avoids periodic repetition, but it still allows clumping and large voids, creating grain that can look dirty or unstable. Blue noise improves the situation by discouraging both large empty regions and large clusters.

In a good blue-noise mask, active samples repel one another enough to maintain even coverage, yet they do not settle into a visible lattice. The result is a texture that feels random without looking sloppy, and uniform without looking synthetic. This combination is why blue noise is prized in both printing and rendering.

## The Void-and-Cluster Method

Ulichney's void-and-cluster method is the canonical way to generate a blue-noise dither array. The central idea is to iteratively rearrange sample points so that dense groups are broken up and sparse regions are filled.

The method can be described in conceptual stages:

1. **Initialize a binary pattern** with a set of on-pixels.
2. **Define an energy function** so that nearby on-pixels contribute more strongly than distant ones. This energy is often based on a Gaussian-like falloff, although many implementations use efficient approximations.
3. **Find the tightest cluster**: identify an on-pixel sitting in the region of highest local density.
4. **Find the largest void**: identify an off-pixel located in the emptiest region, meaning the position with the lowest surrounding energy.
5. **Move the sample** from the cluster to the void.
6. Repeat until the pattern reaches an equilibrium with minimal visible low-frequency structure.

Once a good binary pattern exists, threshold ranks can be assigned. The process of rank assignment repeatedly removes the most clustered point and records its order, then rebuilds from the sparsest configuration upward. The final ranked array can be thresholded at any fill percentage, producing progressive point sets with blue-noise characteristics across many tone levels.

This is why the method is so powerful for dithering: it does not merely optimize one density. It creates an ordered threshold map that behaves well over the full tonal range.

## FFT-Based Blue Noise Generation

Another route to blue noise uses the frequency domain directly. A simple FFT-based approach begins by generating white noise, transforming it with a fast Fourier transform, applying a high-pass or band-pass filter to attenuate low frequencies, and then transforming the result back to the spatial domain. The resulting texture has more high-frequency content than the original white noise.

This method is intuitive because it directly manipulates the power spectrum. However, it is not automatically equivalent to a high-quality void-and-cluster mask. Spectral filtering can shape frequency content, but it does not always guarantee ideal point distribution, threshold ordering, or progressive properties. Still, FFT methods are useful for procedural texture generation, approximate masks, and experiments where a continuous-valued blue-noise field is acceptable.

## Tileable Blue Noise

A practical blue-noise texture is often tiled across a larger image or screen. If the mask is not constructed with periodic boundaries, seams appear where the tile repeats. To prevent this, many algorithms use **toroidal distance** in their energy computation. That means the texture wraps around both horizontally and vertically as if it lived on the surface of a torus.

Using periodic distance ensures that points near the left edge interact correctly with points near the right edge, and likewise for top and bottom. The resulting pattern can repeat seamlessly, which is essential for games, shaders, and print experiments where a finite texture is reused across large surfaces.

## Spatiotemporal Blue Noise

Blue noise is not limited to 2D images. In animation and rendering, it can be extended into three dimensions where X and Y are screen coordinates and Z is time or frame index. **Georgiev and Fajardo (2016)** popularized spatiotemporal blue-noise sampling strategies in which each individual frame exhibits blue-noise structure in the image plane and the sequence of frames exhibits favorable distribution over time as well.

This matters because naïvely changing noise every frame can cause distracting flicker, while keeping the exact same noise each frame can cause static grain. Spatiotemporal blue noise balances both requirements: good spatial appearance and good temporal behavior. It is especially useful in stochastic rendering, denoising pipelines, and temporal accumulation methods.

## Blue Noise in Rendering

Modern rendering uses blue noise for more than dithering. In path tracing, sample positions distributed with blue-noise-like characteristics often produce less objectionable variance than purely random samples at equal count. In real-time ambient occlusion, such as RTAO, blue-noise rotations or sample offsets reduce banding and structured aliasing. In temporal anti-aliasing, noise with favorable spatial and temporal spectra helps jitter patterns disappear into stable reconstruction rather than turning into shimmer.

The broader principle is always the same: if undersampling or stochastic estimation must create error, shape the error so it lands where perception is least offended.

## Screen-Space Blue Noise in Games

Game engines frequently use small tileable blue-noise textures in screen space. Unreal Engine, Frostbite, and related real-time pipelines use them for dithering, ray-marching offsets, ambient occlusion sampling, soft shadow variation, stochastic transparency, and volumetric effects. A compact 64×64 or 128×128 blue-noise tile can dramatically improve the perceived quality of limited-sample effects without major cost.

These textures are especially attractive because they are deterministic, GPU-friendly, cacheable, and easy to integrate. Instead of expensive random-number generation with poor spatial properties, a shader can index a precomputed mask.

## Interleaved Gradient Noise

A widely used cheap approximation is **Interleaved Gradient Noise (IGN)**, often written as:

```text
fract(52.9829189 * fract(0.06711056 * x + 0.00583715 * y))
```

This compact formula generates a reproducible pseudo-random scalar from integer pixel coordinates. It is not a perfect substitute for carefully optimized blue-noise textures, but it offers useful screen-space decorrelation at almost no memory cost. For many game-engine tasks, IGN is a practical compromise between quality and simplicity.

## Comparison to White Noise, Pink Noise, and Bayer

Blue noise can be summarized most clearly by comparison:

- **White noise** is easy to generate but allows clumps and voids. It looks noisy in an undisciplined way.
- **Pink noise** emphasizes low frequencies and is therefore usually undesirable for dithering because the structure becomes obvious.
- **Bayer patterns** are deterministic and efficient but strongly periodic, producing cross-hatch and moiré-prone structure.
- **Blue noise** avoids large-scale patterning while maintaining even local distribution, producing a grain-like texture that the eye tolerates extremely well.

## Why Blue Noise Matters for This Repository

For halftone and mosaic art, blue noise offers a vital alternative to both rigid classical screens and directionally streaked error diffusion. It can break posterization bands without revealing a grid, add texture without shouting its own mechanism, and support sampling decisions in shaders that must look intentional rather than merely random. In other words, blue noise is the rare technical device that feels almost invisible. It lets the image keep its lie organized at the threshold of perception, where the viewer senses texture but cannot easily see the machinery that made it.
