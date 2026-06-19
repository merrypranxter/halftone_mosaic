// classical_halftone.frag — CMYK amplitude-modulated (AM) halftone.
//
// The image is separated into C, M, Y, K. Each channel is screened with a
// rotated dot grid whose dot *size* tracks the channel value (more ink ->
// bigger dot). Classic screen angles minimise the moiré between channels:
//     C: 15°   M: 75°   Y: 0°   K: 45°
// (Yellow at 0° because the eye is least sensitive to its pattern.)
//
// Uniforms:
//   u_resolution   : viewport size in pixels
//   u_image        : source image
//   u_dot_frequency: dots across the screen width (analogous to LPI)
//   u_dot_shape    : 0 = round, 1 = elliptical, 2 = square
//   u_dot_gain     : 0..1, simulates ink spread (grows every dot a little)
//   u_paper        : paper tint (e.g. newsprint beige)

#ifdef GL_ES
precision highp float;
#endif

#include "common.glsl"

uniform vec2  u_resolution;
uniform sampler2D u_image;
uniform float u_dot_frequency;  // e.g. 80.0
uniform int   u_dot_shape;      // 0 round, 1 ellipse, 2 square
uniform float u_dot_gain;       // e.g. 0.08
uniform vec3  u_paper;          // e.g. vec3(1.0)

// RGB -> CMYK (simple GCR-free separation).
vec4 rgb2cmyk(vec3 rgb) {
    float k = 1.0 - max(max(rgb.r, rgb.g), rgb.b);
    vec3 cmy = (1.0 - rgb - k) / max(1.0 - k, 1e-4);
    return vec4(cmy, k);
}

// One screen: returns ink coverage 0..1 for a channel `value` sampled on a
// grid rotated by `angleDeg`, in screen-space pixels.
float screen(vec2 fragPx, float value, float angleDeg) {
    // Rotate pixel coords about the image center, then tile into cells.
    vec2 c = (fragPx - 0.5 * u_resolution);
    c = rot(angleDeg * DEG2RAD) * c;
    float cell = u_resolution.x / max(u_dot_frequency, 1.0);
    vec2 g = c / cell;
    vec2 f = fract(g) - 0.5;        // local coord within a cell, [-0.5,0.5]

    // Dot radius from coverage. value in [0,1]; +dot gain expands it.
    float cov = clamp(value + u_dot_gain * value, 0.0, 1.0);
    // Map coverage to a radius so area ~ coverage (max radius reaches corners).
    float r = sqrt(cov) * 0.71;

    float d;
    if (u_dot_shape == 2) {
        d = max(abs(f.x), abs(f.y));            // square dot
    } else if (u_dot_shape == 1) {
        d = length(f * vec2(1.0, 1.6));          // elliptical dot
    } else {
        d = length(f);                           // round dot
    }
    // Anti-aliased coverage of this dot (1 = inked).
    float aa = fwidth(d) + 1e-4;
    return 1.0 - smoothstep(r - aa, r + aa, d);
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec3 rgb = texture2D(u_image, uv).rgb;
    vec4 cmyk = rgb2cmyk(rgb);

    float c = screen(gl_FragCoord.xy, cmyk.x, 15.0);
    float m = screen(gl_FragCoord.xy, cmyk.y, 75.0);
    float y = screen(gl_FragCoord.xy, cmyk.z, 0.0);
    float k = screen(gl_FragCoord.xy, cmyk.w, 45.0);

    // Subtractive ink mixing on paper. Each ink absorbs its complement.
    vec3 col = u_paper;
    col *= mix(vec3(1.0), vec3(0.0, 1.0, 1.0), c); // cyan absorbs red
    col *= mix(vec3(1.0), vec3(1.0, 0.0, 1.0), m); // magenta absorbs green
    col *= mix(vec3(1.0), vec3(1.0, 1.0, 0.0), y); // yellow absorbs blue
    col *= mix(vec3(1.0), vec3(0.0),           k); // black absorbs all

    gl_FragColor = vec4(col, 1.0);
}
