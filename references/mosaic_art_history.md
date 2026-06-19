# Mosaic Art — From Roman Floors to Voronoi Cells

A mosaic builds an image from discrete pieces — *tesserae* — set into a ground.
Step back and the pieces fuse into a picture; step close and the picture
dissolves into autonomous units of color. This is the same perceptual contract
as halftone and dithering, just at human scale and a few thousand years older.

## A short lineage

### Mesopotamia & Greece (4th–1st c. BCE)
The earliest mosaics used natural pebbles (Greek *opus* pebble floors). The
move to cut stone cubes (tesserae) gave finer control of line and tone.

### Rome (1st c. BCE – 4th c. CE)
- **Opus tessellatum** — regular square tesserae in a grid (the literal
  ancestor of the pixel grid; see `mosaic_tile_average.frag`).
- **Opus vermiculatum** — tiny tesserae laid in flowing "worm-like" rows that
  follow contours, for fine shading. The rows-follow-form idea reappears in
  contour hatching (`line_art_halftone.frag`, mode 2).

### Byzantine (5th–15th c.)
Glass tesserae (*smalti*), often gold-leaf-backed and deliberately set at
slightly irregular angles so they catch and scatter light — the surface
shimmers as you move. Color was applied as flat regions bounded by dark
outlines, conceptually close to posterization + lead lines.

### Stained glass (Gothic, 12th c. onward)
Not mosaic per se, but the same logic: regions of pure colored glass separated
by dark **lead came**. This is exactly the model behind
`voronoi_stained_glass.frag` — flat/gradient cells plus a dark seam and a glow.

### Trencadís (Gaudí, Catalan Modernisme, ~1900)
Antoni Gaudí and Josep Maria Jujol covered surfaces in *trencadís* — mosaic from
broken, irregular ceramic shards. Irregular cells of varying size and color, the
hand-made cousin of a Voronoi tessellation seeded by chance.

## The pointillist bridge

**Georges Seurat** and the Neo-Impressionists (1880s) painted in small dots of
unmixed pigment, trusting the eye to blend them — *optical mixing*. This is
halftone's artistic origin: tone and color built from discrete marks rather than
blended pigment. **Roy Lichtenstein** later inverted the joke, hand-painting
enlarged Ben-Day halftone dots so the *mechanism* of cheap printing became the
subject of fine art.

## Digital mosaics: the geometry

| Tiling | Geometry | Character | In this repo |
|---|---|---|---|
| Square grid | regular lattice | rigid, "pixel" | `mosaic_tile_average.frag` |
| Brick | offset rows | masonry, less rigid | `--brick` / `--shape brick` |
| Hexagonal | honeycomb lattice | isotropic, organic | `hexagonal_pixel_grid.frag` |
| Triangular | split cells | faceted, "low-poly" | `--shape triangle` |
| Voronoi | seed-based cells | stained glass, trencadís | `voronoi_stained_glass.frag` |

### Voronoi & Delaunay
A **Voronoi diagram** partitions the plane into cells, one per seed, where each
cell is the region closer to its seed than to any other. Its dual graph is the
**Delaunay triangulation** (connect seeds whose cells touch). Seeding strategy
controls the look:

- **Random / uniform** — even, abstract.
- **Blue-noise seeds** — natural, even spacing without lattice artifacts.
- **Feature-/edge-weighted** — more seeds where the image has detail, so cell
  boundaries hug edges and the mosaic "respects" the subject. (Approximated in
  the shader by modulating seed jitter with local tone.)

### Why hexagons
A hex lattice is more **isotropic** than a square one: the six nearest neighbours
are all equidistant, so distance/edge rendering is more uniform across
directions. Curves and diagonals look smoother than on a square grid — the same
reason hexagons appear in sampling, image processing, and game maps.

## The throughline

Roman *tessellatum*, Seurat's dots, Ben-Day screens, Bayer matrices, and Voronoi
cells are all answers to one question: *how few discrete pieces, arranged how,
will the eye accept as a continuous image?* This repository is a workshop for
asking it in code.

## See also
- `halftone_theory.md`, `blue_noise_research.md`
- `shaders/voronoi_stained_glass.frag`, `shaders/hexagonal_pixel_grid.frag`,
  `tools/mosaic_tile_generator.py`, `notebooks/voronoi_generator.ipynb`.
