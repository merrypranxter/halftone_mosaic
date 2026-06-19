// line_art_halftone.frag — tone built from lines (engraving / woodcut look).
//
// Instead of dots, tone is rendered as parallel lines whose coverage tracks
// darkness: dark areas -> thick/dense lines, light areas -> thin/absent lines.
// A second hatching layer at a different angle kicks in for the darkest tones
// (cross-hatching), exactly as an engraver builds shadow.
//
// Modes:
//   0 hatching        : one set of parallel lines
//   1 cross-hatching  : two sets, the second only in shadows
//   2 contour         : lines bend along image gradient (flow lines)
//
// Uniforms:
//   u_resolution, u_image
//   u_freq  : lines across the width (e.g. 120)
//   u_angle : primary hatch angle in degrees
//   u_mode  : 0 / 1 / 2

#ifdef GL_ES
precision highp float;
#endif

#include "common.glsl"

uniform vec2  u_resolution;
uniform sampler2D u_image;
uniform float u_freq;   // e.g. 120.0
uniform float u_angle;  // e.g. 45.0
uniform int   u_mode;   // 0 / 1 / 2

// Coverage of a line screen at `angleDeg`, given target ink `t` (0..1).
// Lines are produced by thresholding a triangle wave; `t` sets line width.
float lines(vec2 fragPx, float angleDeg, float t) {
    vec2 c = (fragPx - 0.5 * u_resolution);
    c = rot(angleDeg * DEG2RAD) * c;
    float period = u_resolution.x / max(u_freq, 1.0);
    float tri = abs(fract(c.y / period) - 0.5) * 2.0; // 0..1 triangle
    float aa = fwidth(tri) + 1e-4;
    // Ink where triangle is below the target width (t).
    return 1.0 - smoothstep(t - aa, t + aa, tri);
}

// Estimate the local image gradient direction (for contour mode).
float gradientAngle(vec2 uv) {
    vec2 px = 1.0 / u_resolution;
    float l = luma(texture2D(u_image, uv - vec2(px.x, 0.0)).rgb);
    float r = luma(texture2D(u_image, uv + vec2(px.x, 0.0)).rgb);
    float d = luma(texture2D(u_image, uv - vec2(0.0, px.y)).rgb);
    float u = luma(texture2D(u_image, uv + vec2(0.0, px.y)).rgb);
    vec2 grad = vec2(r - l, u - d);
    // Hatch perpendicular to the gradient (along iso-tone contours).
    return atan(grad.x, grad.y) / DEG2RAD + 90.0;
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    float tone = 1.0 - luma(texture2D(u_image, uv).rgb); // ink amount 0..1

    float ink;
    if (u_mode == 2) {
        float a = gradientAngle(uv);
        ink = lines(gl_FragCoord.xy, a, tone);
    } else {
        ink = lines(gl_FragCoord.xy, u_angle, tone);
        if (u_mode == 1) {
            // Cross-hatch: add a perpendicular set only in the darker half.
            float shadow = smoothstep(0.5, 0.9, tone);
            float ink2 = lines(gl_FragCoord.xy, u_angle + 90.0, tone) * shadow;
            ink = max(ink, ink2);
        }
    }

    vec3 col = mix(vec3(1.0), vec3(0.0), ink); // black ink, white paper
    gl_FragColor = vec4(col, 1.0);
}
