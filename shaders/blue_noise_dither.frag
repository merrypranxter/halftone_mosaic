// blue_noise_dither.frag — threshold dithering against a blue-noise texture.
//
// Blue noise has (almost) no low-frequency energy: the values are decorrelated
// at short range but evenly spread at large range. Used as a per-pixel
// threshold it produces dithering with NO visible structure — it reads as fine
// film grain, the most "organic" of all dither types.
//
// Best results use a precomputed void-and-cluster tile (see
// tools/blue_noise_generator.py) bound to u_noise. If you don't have one,
// set u_procedural = 1 to use an interleaved-gradient-noise approximation
// (cheaper, not true blue noise, but structureless enough for many uses).
//
// Uniforms:
//   u_resolution, u_image
//   u_noise      : blue-noise texture (tileable, e.g. 256x256, R channel)
//   u_noise_size : size of the noise texture in pixels (for 1:1 tiling)
//   u_levels     : output levels per channel
//   u_procedural : 0 use u_noise, 1 use IGN approximation
//   u_color      : 0 mono, 1 rgb

#ifdef GL_ES
precision highp float;
#endif

#include "common.glsl"

uniform vec2  u_resolution;
uniform sampler2D u_image;
uniform sampler2D u_noise;
uniform float u_noise_size; // e.g. 256.0
uniform float u_levels;     // e.g. 2.0
uniform int   u_procedural; // 0 / 1
uniform int   u_color;      // 0 / 1

// Jimenez "interleaved gradient noise" — a low-cost blue-ish noise.
float ign(vec2 p) {
    return fract(52.9829189 * fract(dot(p, vec2(0.06711056, 0.00583715))));
}

float threshold(vec2 fragPx) {
    if (u_procedural == 1) return ign(fragPx);
    vec2 nuv = fract(fragPx / max(u_noise_size, 1.0));
    return texture2D(u_noise, nuv).r;
}

float quantize(float v, float t, float levels) {
    float L = max(levels - 1.0, 1.0);
    return floor(v * L + (t - 0.5) + 0.5) / L;
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec3 rgb = texture2D(u_image, uv).rgb;
    float t = threshold(gl_FragCoord.xy);

    vec3 col;
    if (u_color == 1) {
        col = vec3(
            quantize(rgb.r, t, u_levels),
            quantize(rgb.g, t, u_levels),
            quantize(rgb.b, t, u_levels)
        );
    } else {
        col = vec3(quantize(luma(rgb), t, u_levels));
    }
    gl_FragColor = vec4(col, 1.0);
}
