# Halftone Theory — Print Industry Practice

Halftoning is the art of fooling the eye into seeing continuous tone where only
two inks exist: paper and ink. A printing press can lay down ink or not lay
down ink — there is no "50% gray" ink on a newspaper. Gray is a *spatial*
average of black dots and white paper, integrated by the optics of your eye.

## AM vs FM screening

| | AM (amplitude modulated) | FM (frequency modulated / stochastic) |
|---|---|---|
| What varies | dot **size** | dot **density** |
| Dot grid | regular, at a fixed angle | irregular / random |
| Moiré risk | yes (needs screen angles) | none |
| Look | classic "comic / newsprint" | grain, photographic |
| Press friendly | very (predictable dot gain) | demanding (tiny dots) |

Classical halftone is AM: a regular grid of dots whose diameter grows with ink
coverage. Stochastic (FM) screening keeps dots a fixed tiny size and varies how
*many* land in a region.

## Screen frequency (LPI)

Lines per inch is the dot grid density. Higher LPI = finer detail but demands
better paper and press.

| Stock | Typical LPI |
|---|---|
| Newspaper | 65–85 |
| Magazine (coated) | 133–150 |
| High-end art print | 175–300 |

LPI is independent of DPI (device dots): you need ~16 device dots per halftone
cell to render 256 gray levels (a 16×16 cell), so a 2400 dpi imagesetter gives
2400/16 = 150 LPI at full tonal range.

## Screen angles and moiré

When two regular grids overlap at a small angle they beat against each other and
produce a low-frequency **moiré** pattern. CMYK printing overlays four screens,
so the angles are chosen 30° apart to push the beat frequency out of view:

| Ink | Angle |
|---|---|
| Cyan | 15° |
| Magenta | 75° |
| Yellow | 0° |
| Black (K) | 45° |

Black sits at 45° because that is the least conspicuous angle to the eye, and it
carries the most visual weight. Yellow sits at 0° because the eye is least
sensitive to yellow's pattern, so its small angular separation from the others
is tolerable. The remaining 30° gaps minimise visible moiré. (This is the
convention `classical_halftone.frag` and `halftone_renderer.py` use.)

## Dot gain

Ink physically spreads when it touches paper, so a 50% digital dot may print as
a 65% dot. This darkens midtones. Presses are characterised by a **dot gain
curve** (often quoted as the gain at 50%, e.g. "18% dot gain"). Prepress applies
the inverse curve so the printed result matches intent.

- Uncoated / newsprint: high gain (20–30%).
- Coated gloss: low gain (10–15%).

In the tools, `--dot-gain` expands every dot's radius slightly before
thresholding to emulate this spread.

## Dot shape

The shape of the dot changes tonal transitions and moiré:

- **Round** — classic, but at ~70% coverage adjacent dots touch abruptly,
  causing a visible tonal jump ("dot join").
- **Elliptical** — dots join along one axis before the other, smoothing the
  midtone transition; the default for quality photographic work.
- **Square / diamond** — sharp, graphic; joins cleanly at 50%.
- **Line** — not a dot at all; tone from line width (see line-art halftone).

## The perceptual contract

The whole system rests on the eye's low-pass filter. Below the acuity limit
(~1 arcminute) the eye cannot resolve individual dots and integrates them into
tone. Step closer than the design viewing distance and the lie is revealed — the
picture dissolves back into pieces. This is the central tension the whole
repository plays with.

## See also

- `dithering_algorithms.md` — the screen-less, per-pixel cousins of halftoning.
- `blue_noise_research.md` — why structureless dot distributions look best.
- `shaders/classical_halftone.frag`, `tools/halftone_renderer.py`.
