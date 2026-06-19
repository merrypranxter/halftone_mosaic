// hexagonal_pixel_grid.frag — resample the image onto a hexagonal lattice.
//
// Square pixels privilege the horizontal/vertical axes; a hex lattice is more
// isotropic, so diagonals and curves read more smoothly. Each fragment is
// snapped to its nearest hexagon center and painted with the image sampled
// there — every hexagon is one "pixel".
//
// We use the standard trick: overlay two offset rectangular grids, compute the
// candidate center in each, and keep whichever is closer. Works for pointy-top
// hexes; flip the axes for flat-top.
//
// Uniforms:
//   u_resolution, u_image
//   u_hex_size : center-to-center spacing in pixels (e.g. 18)
//   u_edge     : 0..0.1 darken hex borders to expose the honeycomb (0 = off)

#ifdef GL_ES
precision highp float;
#endif

#include "common.glsl"

uniform vec2  u_resolution;
uniform sampler2D u_image;
uniform float u_hex_size; // e.g. 18.0
uniform float u_edge;     // e.g. 0.0

// Returns the nearest hex center (in pixels) and the distance to it in .z-ish
// via out param. Pointy-top hexagons.
vec2 hexCenter(vec2 p, float s, out float dist) {
    // Spacing of the two interleaved rectangular grids.
    vec2 grid = vec2(s * 1.7320508, s * 1.5); // (sqrt(3)*s, 1.5*s)

    // Candidate A: even rows.
    vec2 a = (floor(p / grid) + 0.5) * grid;
    // Candidate B: rows offset by half in x and half-step in y.
    vec2 b = (floor((p - grid * 0.5) / grid) + 0.5) * grid + grid * 0.5;

    float da = length(p - a);
    float db = length(p - b);
    if (da < db) { dist = da; return a; }
    dist = db; return b;
}

void main() {
    vec2 fragPx = gl_FragCoord.xy;
    float s = max(u_hex_size, 2.0);

    float dist;
    vec2 center = hexCenter(fragPx, s, dist);
    vec3 col = texture2D(u_image, center / u_resolution).rgb;

    if (u_edge > 0.0) {
        float e = smoothstep(s * (1.0 - u_edge), s, dist);
        col = mix(col, vec3(0.05), e);
    }

    gl_FragColor = vec4(col, 1.0);
}
