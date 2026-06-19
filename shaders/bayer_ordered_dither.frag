// bayer_ordered_dither.frag — ordered dithering with a Bayer threshold matrix.
//
// A Bayer matrix is a fixed, recursive threshold map. We compare each pixel's
// value against the matrix entry for its position; above -> white, below ->
// black (per channel, or on luma). The pattern is regular and crosshatched —
// the Game Boy / early-PC look.
//
// The 8x8 matrix is generated procedurally from the bit-reversal / interleave
// definition so we don't need a lookup texture.
//
// Uniforms:
//   u_resolution, u_image
//   u_levels  : output levels per channel (2 = pure 1-bit, >2 = posterized)
//   u_matrix  : 2, 4, or 8 (matrix order)
//   u_time    : optional; animate the threshold for a shimmer (set 0 to freeze)
//   u_color   : 0 = dither on luma (mono), 1 = dither each RGB channel

#ifdef GL_ES
precision highp float;
#endif

#include "common.glsl"

uniform vec2  u_resolution;
uniform sampler2D u_image;
uniform float u_levels;   // e.g. 2.0
uniform int   u_matrix;   // 2 / 4 / 8
uniform float u_time;
uniform int   u_color;    // 0 mono, 1 rgb

// Bayer value in [0,1) for integer pixel position p, matrix order n (power of 2).
// Built by interleaving the bits of x and y (the classic recursive definition).
float bayer(vec2 p, int n) {
    float sum = 0.0;
    float divisor = 1.0;
    vec2 ip = mod(floor(p), float(n));
    // Up to 3 bit-planes covers n = 8.
    for (int b = 0; b < 3; b++) {
        if (float(n) <= exp2(float(b))) break;
        float bx = mod(ip.x, 2.0);
        float by = mod(ip.y, 2.0);
        // Dispersed-dot ordering: combine the two bits then bit-reverse.
        float bit = by * 2.0 + mod(bx + by, 2.0);
        sum += bit * divisor;
        divisor *= 4.0;
        ip = floor(ip / 2.0);
    }
    return sum / (float(n) * float(n));
}

float quantize(float v, float t, float levels) {
    // Add the (centered) threshold, then snap to the nearest level.
    float L = max(levels - 1.0, 1.0);
    return floor(v * L + (t - 0.5) + 0.5) / L;
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec3 rgb = texture2D(u_image, uv).rgb;

    int n = u_matrix == 2 ? 2 : (u_matrix == 4 ? 4 : 8);
    vec2 p = gl_FragCoord.xy + vec2(u_time * 13.0); // shimmer if u_time != 0
    float t = bayer(p, n);

    vec3 col;
    if (u_color == 1) {
        col = vec3(
            quantize(rgb.r, t, u_levels),
            quantize(rgb.g, t, u_levels),
            quantize(rgb.b, t, u_levels)
        );
    } else {
        float v = quantize(luma(rgb), t, u_levels);
        col = vec3(v);
    }
    gl_FragColor = vec4(col, 1.0);
}
