# halftone_mosaic

A repository exploring the print-based aesthetic of halftone patterns, mosaic tiling, and pixel quantization. This is not about making things look "retro" or "pixelated" — it's about understanding how the human eye and brain construct continuous tone from discrete dots, and then weaponizing that understanding to create art that exists at the threshold of perception.

## The Aesthetic

- **Classical halftone**: The newspaper/CMYK dot pattern where small dots of varying size create the illusion of continuous tone. The dots are typically at 45°, 75°, 15°, and 0° angles for C, M, Y, K.
- **Stochastic/FM halftone**: Randomly distributed dots of uniform size (instead of regularly spaced dots of varying size). Creates a more natural, grain-like texture.
- **Bayer ordered dither**: A fixed 2×2, 4×4, or 8×8 matrix that determines which pixels to threshold. Creates a visible cross-hatch pattern.
- **Error diffusion dither**: Floyd-Steinberg, Atkinson, Sierra — algorithms that spread the quantization error to neighboring pixels, creating smoother gradients but visible artifact patterns ("worms").
- **Blue noise dither**: Dither patterns that distribute quantization error in a high-frequency, visually pleasing noise. Looks like film grain, not structured pattern.
- **Mosaic tiling**: Breaking the image into tiles (square, hexagonal, triangular) and rendering each tile as a single color or a pattern. The tile itself becomes the pixel.
- **Quantization / posterization**: Reducing the number of color levels, creating banding that is then broken by dithering. The banding becomes texture.
- **Pixelate with style**: Not just "make it blocky" but make each block a meaningful unit — a color average, a pattern, a texture.
- **Stained glass / Voronoi mosaic**: Breaking the image into irregular cells (Voronoi diagram) and rendering each cell as a single color or gradient. The cells follow the image structure.
- **Hexagonal pixel grid**: Hexagonal pixels instead of square, creating a honeycomb image structure. The hex grid changes how edges and diagonals appear.

## Core Concepts

- **Halftone dot shape**: The shape of the dot affects the appearance. Round dots (classic), elliptical dots (less moiré), square dots (sharp), line dots (line art). The dot shape is the "fundamental unit" of the print.
- **Screen frequency / lines per inch (LPI)**: The density of the halftone screen. Newspaper: 85 LPI. Magazine: 133-150 LPI. Art print: 200+ LPI. The LPI determines the maximum detail.
- **Screen angle and moiré**: When multiple screens overlap (CMYK), the angle between them determines moiré patterns. The classic 15°, 45°, 75°, 0° angles minimize moiré.
- **Dot gain**: The physical spreading of ink on paper, causing the printed dots to be larger than the digital dots. This affects the tonal reproduction.
- **Dither matrix**: A threshold matrix (Bayer) or a diffusion kernel (Floyd-Steinberg) that determines how to quantize a pixel based on its neighbors.
- **Error diffusion**: The error from quantizing a pixel is distributed to neighboring pixels that haven't been processed yet. The distribution kernel determines the pattern: Floyd-Steinberg (classic "worms"), Atkinson (more diffuse, used on Macs), Jarvis-Judice-Ninke (smoother, more spread).
- **Blue noise**: A noise pattern with minimal low-frequency energy. When used for dithering, it creates a texture that is visually pleasing and doesn't have visible structure.
- **Voronoi tessellation**: Partitioning the plane into cells based on distance to a set of seed points. Each cell is a region closer to one seed than any other. Used for mosaic, stained glass, and abstract effects.
- **Hexagonal grid**: A grid where each pixel is a hexagon. The hex grid has better isotropic properties (distance is more uniform in all directions) than square pixels.

## Repository Structure

```
├── shaders/
│   ├── classical_halftone.frag
│   ├── stochastic_halftone.frag
│   ├── bayer_ordered_dither.frag
│   ├── floyd_steinberg_dither.frag
│   ├── atkinson_dither.frag
│   ├── blue_noise_dither.frag
│   ├── mosaic_tile_average.frag
│   ├── voronoi_stained_glass.frag
│   ├── hexagonal_pixel_grid.frag
│   ├── quantization_posterization.frag
│   └── line_art_halftone.frag
├── notebooks/
│   ├── halftone_simulator.ipynb
│   ├── dither_algorithm_explorer.ipynb
│   ├── voronoi_generator.ipynb
│   └── hex_grid_converter.ipynb
├── tools/
│   ├── halftone_renderer.py
│   ├── dither_applier.py
│   ├── mosaic_tile_generator.py
│   └── blue_noise_generator.py
├── references/
│   ├── halftone_theory.md
│   ├── dithering_algorithms.md
│   ├── blue_noise_research.md
│   └── mosaic_art_history.md
├── gallery/
│   └── .gitkeep
└── README.md
```

## Design Prompts

- **"Create a halftone shader that renders a portrait as a CMYK dot pattern..."**
- **"Design a Voronoi mosaic shader where seed points are placed according to image edges..."**
- **"Build a dither shader that uses a different dither algorithm for each color channel..."**
- **"Implement a line-art halftone where the line angle follows the image gradient direction..."**
- **"Create a hybrid effect: posterize first, then apply halftone to each posterization band..."**
- **"Build a hex-grid shader where each cell's color is the dominant hue of that area..."**

## Quick Start

```bash
# Render a halftone
python tools/halftone_renderer.py input.png output.png --lpi 133 --dot-shape round

# Apply dithering  
python tools/dither_applier.py input.png output.png --algorithm atkinson --levels 4

# Generate mosaic
python tools/mosaic_tile_generator.py input.png output.png --type hex --size 20

# Generate blue noise texture
python tools/blue_noise_generator.py --method void_cluster --size 128 --output blue_noise.png
```

## References

- Robert Ulichney, "Digital Halftoning" (MIT Press, 1987)
- Georges Seurat, pointillism
- Roy Lichtenstein, pop art halftone paintings
- The Veritas Prep Guide to Printing
- Apple Macintosh System 7 dithering (Atkinson algorithm)
- Game Boy / early computer graphics (Bayer dithering)
- Akira Fujisawa, blue noise research
- Voronoi diagrams and Delaunay triangulation
- Roman mosaic art, Byzantine mosaics, Antoni Gaudí's trencadís

## Color Palette

| Name | Hex |
|------|-----|
| Halftone black | `#000000` |
| Halftone white | `#FFFFFF` |
| Cyan dot | `#00FFFF` |
| Magenta dot | `#FF00FF` |
| Yellow dot | `#FFFF00` |
| Newsprint beige | `#F5F5DC` |
| Stained glass blue | `#3366CC` |

## Mood

> The image is made of pieces. The pieces are lies. The lies become truth when you step back. The dot is a promise, the promise is a pattern, the pattern is a picture. Every pixel is a vote, and the vote is unanimous: this is what you see. The mosaic is a democracy of light.
