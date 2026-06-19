# Gallery

Sample renders produced by [`tools/build_gallery.py`](../tools/build_gallery.py)
from a synthetic test subject (a soft sphere with a highlight over a tonal
gradient — chosen to exercise smooth gradients, a hard edge, and midtones at
once). Regenerate any time, deterministically:

```bash
python tools/build_gallery.py            # synthetic source
python tools/build_gallery.py photo.jpg  # your own image
```

| File | Effect |
|---|---|
| `00_source.png` | the synthetic source image |
| `10_halftone_am_round.png` | classical CMYK AM halftone, round dots, slight dot gain |
| `11_halftone_am_ellipse.png` | AM halftone with elliptical dots (smoother midtone join) |
| `12_halftone_fm.png` | stochastic / FM screening (no moiré) |
| `20_dither_floyd.png` | Floyd–Steinberg error diffusion (serpentine) |
| `21_dither_atkinson.png` | Atkinson dither (crisp, high contrast) |
| `22_dither_bayer8.png` | Bayer 8×8 ordered dither |
| `23_dither_blue_noise.png` | blue-noise threshold dither (film grain) |
| `30_mosaic_brick.png` | brick-offset square tiles with grout |
| `31_mosaic_hex.png` | hexagonal pixel grid |
| `32_mosaic_voronoi_glass.png` | Voronoi stained-glass mosaic with lead lines |

These are committed so the repo has visible output without needing to run
anything. Drop your own image in to see the effects on real content.
