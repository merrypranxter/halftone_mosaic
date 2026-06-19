# halftone_mosaic

A workshop for the print-based aesthetic of **halftone patterns, mosaic tiling,
and pixel quantization**. Not "retro" or "pixelated" for its own sake — this is
about understanding how the eye and brain construct continuous tone from
discrete dots, and then using that understanding to make images that live at the
threshold of perception.

> The image is made of pieces. The pieces are lies. The lies become truth when
> you step back.

## What's inside

| Folder | What it holds |
|---|---|
| [`shaders/`](shaders/) | GLSL fragment shaders for every effect (ShaderToy / WebGL-compatible) |
| [`tools/`](tools/) | NumPy + Pillow command-line renderers (halftone, dither, mosaic, blue noise) |
| [`notebooks/`](notebooks/) | Jupyter notebooks that explore and compare the techniques |
| [`references/`](references/) | The theory: halftone, dithering, blue noise, mosaic history |
| [`gallery/`](gallery/) | Sample renders (regenerate with `tools/build_gallery.py`) |

## The techniques

- **Classical halftone** — CMYK amplitude-modulated dots at screen angles
  (C 15°, M 75°, Y 0°, K 45°) to minimise moiré.
- **Stochastic / FM halftone** — uniform dots, density follows tone, no moiré.
- **Bayer ordered dither** — fixed threshold matrix, the Game Boy crosshatch.
- **Floyd–Steinberg & Atkinson** — error diffusion, with worms and crisp 1-bit
  contrast respectively.
- **Blue-noise dither** — structureless, film-grain quantization.
- **Mosaic tiling** — square, brick, hexagonal, triangular tiles as the pixel.
- **Voronoi stained glass** — irregular cells with lead lines and glow.
- **Hexagonal pixel grid** — isotropic honeycomb resampling.
- **Quantization / posterization** — banding broken into texture by dither.
- **Line-art halftone** — tone from hatching, cross-hatching, contour lines.

## Quick start (tools)

```bash
pip install -r requirements.txt

# CMYK halftone of a photo
python tools/halftone_renderer.py photo.jpg out.png --mode am --lpi 60 --shape ellipse

# Floyd–Steinberg 1-bit dither (serpentine scan)
python tools/dither_applier.py photo.jpg out.png --algo floyd --serpentine

# Atkinson, in color
python tools/dither_applier.py photo.jpg out.png --algo atkinson --color

# Voronoi stained-glass mosaic
python tools/mosaic_tile_generator.py photo.jpg out.png --shape voronoi --seeds 1500 --grout 2

# Generate a tileable blue-noise texture for the dither shader
python tools/blue_noise_generator.py bn256.png --size 256 --method void-cluster

# Regenerate the whole gallery
python tools/build_gallery.py
```

All tools share [`tools/halftone_common.py`](tools/halftone_common.py) (image
I/O, CMYK conversion, color space helpers).

## Using the shaders

The shaders in [`shaders/`](shaders/) are GLSL ES 1.00, written for
WebGL1 / ShaderToy-style harnesses. They share
[`shaders/common.glsl`](shaders/common.glsl) (`#include` it, or paste it in).
Common uniforms: `u_resolution`, `u_image` (source texture), and effect-specific
ones documented at the top of each file. To port to ShaderToy, map
`u_resolution → iResolution.xy`, `u_time → iTime`, `u_image → iChannel0`, and
move `main()` into `mainImage()`.

**Note on error diffusion shaders:** Floyd–Steinberg and Atkinson are serial
algorithms; the shaders approximate them with a *windowed replay* per fragment.
For pixel-exact output use the CPU tool (`dither_applier.py`).

## Notebooks

Run from the repo root after `pip install -r requirements.txt`:

- `halftone_simulator.ipynb` — CMYK separation, screen angles, moiré, dot gain, AM vs FM.
- `dither_algorithm_explorer.ipynb` — every dither algorithm side by side, with artifact zooms.
- `voronoi_generator.ipynb` — random vs edge-weighted seeds, stained-glass styling.
- `hex_grid_converter.ipynb` — hex vs square resampling, pointy- vs flat-top.

## Color palette

| Name | Hex |
|---|---|
| Halftone black | `#000000` |
| Halftone white | `#FFFFFF` |
| Cyan dot | `#00FFFF` |
| Magenta dot | `#FF00FF` |
| Yellow dot | `#FFFF00` |
| Newsprint beige | `#F5F5DC` |
| Stained glass blue | `#3366CC` |

(Available as `tools.halftone_common.PALETTE`.)

## References

See [`references/`](references/) for the theory behind each technique.
Foundational reading: Robert Ulichney, *Digital Halftoning* (MIT Press); the
pointillism of Georges Seurat; Roy Lichtenstein's Ben-Day dots; Apple's Atkinson
dither; Ulichney's void-and-cluster blue noise; Voronoi/Delaunay computational
geometry; and the mosaic lineage from Roman *tessellatum* to Gaudí's trencadís.

## License

MIT — see [`LICENSE`](LICENSE).
