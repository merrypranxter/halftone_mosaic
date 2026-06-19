// quantization_posterization.frag — posterize, then dither the bands.
//
// Reducing the number of levels per channel creates banding (posterization).
// Banding is ugly on its own, but if we add a sub-LSB dither *before*
// quantizing, the hard band edges dissolve into texture and the eye perceives
// far more levels than actually exist. Banding becomes the canvas; dither
// becomes the brush.
//
// Dither source is selectable so this single shader doubles as a comparison
// rig: 0 none (pure banding), 1 Bayer 8x8, 2 interleaved-gradient (blue-ish),
// 3 white noise.
//
// Uniforms:
//   u_resolution, u_image
//   u_levels  : levels per channel (e.g. 4)
//   u_dither  : 0 none / 1 bayer / 2 ign / 3 white
//   u_amount  : dither strength in LSBs (≈1.0 = ±half a band)

#ifdef GL_ES
precision highp float;
#endif

#include "common.glsl"

uniform vec2  u_resolution;
uniform sampler2D u_image;
uniform float u_levels;  // e.g. 4.0
uniform int   u_dither;  // 0..3
uniform float u_amount;  // e.g. 1.0

float bayer8(vec2 p) {
    vec2 ip = mod(floor(p), 8.0);
    float sum = 0.0, div = 1.0, n = 8.0;
    for (int b = 0; b < 3; b++) {
        float bx = mod(ip.x, 2.0);
        float by = mod(ip.y, 2.0);
        float bit = by * 2.0 + mod(bx + by, 2.0);
        sum += bit * div;
        div *= 4.0;
        ip = floor(ip / 2.0);
    }
    return sum / (n * n);
}

float ign(vec2 p) {
    return fract(52.9829189 * fract(dot(p, vec2(0.06711056, 0.00583715))));
}

float ditherValue(vec2 p) {
    if (u_dither == 1) return bayer8(p);
    if (u_dither == 2) return ign(p);
    if (u_dither == 3) return hash21(p);
    return 0.5; // none -> centered, no shift
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec3 rgb = texture2D(u_image, uv).rgb;

    float L = max(u_levels - 1.0, 1.0);
    float d = (ditherValue(gl_FragCoord.xy) - 0.5) * u_amount / L;

    vec3 col = floor((rgb + d) * L + 0.5) / L;
    gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
}
