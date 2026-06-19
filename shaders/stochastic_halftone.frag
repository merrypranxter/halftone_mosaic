// stochastic_halftone.frag — frequency-modulated (FM) screening.
//
// Every dot is the same size; what changes is how *many* dots land in a
// region. Darker areas get more dots. There are no fixed screen angles, so
// there is no moiré — just a grain-like, modern texture.
//
// Implementation: a jittered point grid (blue-noise-ish via per-cell hash).
// Each cell drops one candidate dot at a hashed position; the dot is "kept"
// (inked) with probability equal to the local ink coverage. This gives a
// proper FM screen where dot *density* follows tone.
//
// Uniforms:
//   u_resolution, u_image
//   u_dot_size  : dot radius in pixels (uniform for all dots)
//   u_density   : cells across the width (higher = finer grain)

#ifdef GL_ES
precision highp float;
#endif

#include "common.glsl"

uniform vec2  u_resolution;
uniform sampler2D u_image;
uniform float u_dot_size;   // e.g. 1.5 px
uniform float u_density;    // e.g. 300.0 cells across width

void main() {
    vec2 fragPx = gl_FragCoord.xy;
    vec2 uv = fragPx / u_resolution;

    float cell = u_resolution.x / max(u_density, 1.0);
    vec2 g = fragPx / cell;

    float ink = 0.0;
    // Inspect the 3x3 neighbourhood so dots near a cell border still cover us.
    for (int j = -1; j <= 1; j++) {
        for (int i = -1; i <= 1; i++) {
            vec2 cellId = floor(g) + vec2(float(i), float(j));
            vec2 jitter = hash22(cellId);                 // dot position in cell
            vec2 dotPx  = (cellId + jitter) * cell;

            // Local tone -> probability of keeping this dot (1 - luminance).
            vec2 sampleUv = dotPx / u_resolution;
            float tone = 1.0 - luma(texture2D(u_image, sampleUv).rgb);
            float keep = step(hash21(cellId + 7.13), tone);

            float d = length(fragPx - dotPx);
            float aa = u_dot_size * 0.5 + 1.0;
            ink = max(ink, keep * (1.0 - smoothstep(u_dot_size, aa, d)));
        }
    }

    vec3 col = mix(vec3(1.0), vec3(0.0), ink); // black dots on white paper
    gl_FragColor = vec4(col, 1.0);
}
