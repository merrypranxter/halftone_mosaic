// voronoi_stained_glass.frag — Voronoi cell mosaic / stained glass.
//
// Seed points are placed on a jittered grid (one seed per cell). For each
// fragment we find the nearest seed (F1) and the second nearest (F2); the
// fragment is colored by sampling the image at the nearest seed, and the
// boundary between cells is drawn where F2 - F1 is small (the leaded seam of
// stained glass). A soft glow along the seam sells the "cathedral window"
// feel.
//
// To make seams follow image structure, jitter strength can be modulated by
// local contrast — flat areas get larger, calmer cells; busy areas fracture
// into smaller ones. Here we approximate that with luma-driven jitter.
//
// Uniforms:
//   u_resolution, u_image
//   u_cell_size : approx cell spacing in pixels (e.g. 40)
//   u_seam      : seam thickness 0..0.1
//   u_glow      : seam glow color (e.g. stained-glass blue)
//   u_gradient  : 0 flat cells, 1 subtle radial gradient per cell

#ifdef GL_ES
precision highp float;
#endif

#include "common.glsl"

uniform vec2  u_resolution;
uniform sampler2D u_image;
uniform float u_cell_size; // e.g. 40.0
uniform float u_seam;      // e.g. 0.04
uniform vec3  u_glow;      // e.g. vec3(0.2,0.4,0.8)
uniform int   u_gradient;  // 0 / 1

void main() {
    vec2 fragPx = gl_FragCoord.xy;
    float cs = max(u_cell_size, 4.0);
    vec2 g = fragPx / cs;
    vec2 baseCell = floor(g);
    vec2 f = fract(g);

    float f1 = 8.0, f2 = 8.0;       // nearest / second-nearest distances
    vec2 nearestSeed = vec2(0.0);

    for (int j = -1; j <= 1; j++) {
        for (int i = -1; i <= 1; i++) {
            vec2 cellId = baseCell + vec2(float(i), float(j));
            vec2 seed = hash22(cellId);
            // Bias seeds toward image detail: sample tone at a tentative seed.
            vec2 tentative = (cellId + seed) * cs / u_resolution;
            float tone = luma(texture2D(u_image, tentative).rgb);
            seed = mix(vec2(0.5), seed, 0.5 + 0.5 * abs(tone - 0.5) * 2.0);

            vec2 r = vec2(float(i), float(j)) + seed - f;
            float d = dot(r, r);
            if (d < f1) {
                f2 = f1; f1 = d;
                nearestSeed = (cellId + seed) * cs;
            } else if (d < f2) {
                f2 = d;
            }
        }
    }

    vec2 seedUv = nearestSeed / u_resolution;
    vec3 col = texture2D(u_image, seedUv).rgb;

    if (u_gradient == 1) {
        // Slight darkening toward the cell edge -> bevelled glass.
        float edge = clamp(sqrt(f1) / 0.7, 0.0, 1.0);
        col *= mix(1.08, 0.85, edge);
    }

    // Seam: where the two nearest seeds are nearly equidistant.
    float border = sqrt(f2) - sqrt(f1);
    float seam = smoothstep(u_seam + 0.02, u_seam, border);
    float glow = smoothstep(u_seam * 3.0, u_seam, border) - seam;
    col = mix(col, vec3(0.02), seam);     // dark lead came
    col += u_glow * glow * 0.6;           // colored glow beside the seam

    gl_FragColor = vec4(col, 1.0);
}
