// atkinson_dither.frag — Atkinson error diffusion (windowed, GPU).
//
// Bill Atkinson's dither (MacPaint, classic Mac System software) spreads the
// error to SIX neighbours but only diffuses 6/8 of it — the remaining 2/8 is
// thrown away. That deliberate energy loss is why Atkinson images look
// crisper / higher-contrast and less "wormy" than Floyd-Steinberg.
//
// Kernel (each marked cell gets 1/8 of the error):
//        X  1/8 1/8
//   1/8 1/8 1/8
//        1/8
//
// Like floyd_steinberg_dither.frag this uses a windowed replay to approximate
// the serial recurrence inside a tile. See tools/dither_applier.py for exact
// full-image output.
//
// Uniforms: u_resolution, u_image, u_levels, u_window

#ifdef GL_ES
precision highp float;
#endif

#include "common.glsl"

uniform vec2  u_resolution;
uniform sampler2D u_image;
uniform float u_levels;   // e.g. 2.0
uniform int   u_window;   // e.g. 16

const int MAX_W = 24;
const float E = 1.0 / 8.0;

float quant(float v, float levels) {
    float L = max(levels - 1.0, 1.0);
    return floor(v * L + 0.5) / L;
}

void main() {
    vec2 fragPx = floor(gl_FragCoord.xy);
    int W = u_window > MAX_W ? MAX_W : u_window;
    vec2 origin = floor(fragPx / float(W)) * float(W);

    // Three rolling rows of error: current, +1, +2.
    float r0[MAX_W];
    float r1[MAX_W];
    float r2[MAX_W];
    for (int i = 0; i < MAX_W; i++) { r0[i] = 0.0; r1[i] = 0.0; r2[i] = 0.0; }

    float result = 0.0;
    for (int ry = 0; ry < MAX_W; ry++) {
        if (ry >= W) break;
        float y = origin.y + float(W - 1 - ry);

        for (int rx = 0; rx < MAX_W; rx++) {
            if (rx >= W) break;
            float x = origin.x + float(rx);
            vec2 uv = (vec2(x, y) + 0.5) / u_resolution;
            float old = luma(texture2D(u_image, uv).rgb) + r0[rx];
            float newv = quant(old, u_levels);
            float err = (old - newv) * E;

            if (rx + 1 < W) r0[rx + 1] += err;
            if (rx + 2 < W) r0[rx + 2] += err;
            if (rx - 1 >= 0) r1[rx - 1] += err;
            r1[rx]          += err;
            if (rx + 1 < W) r1[rx + 1] += err;
            r2[rx]          += err;

            if (abs(x - fragPx.x) < 0.5 && abs(y - fragPx.y) < 0.5) {
                result = newv;
            }
        }
        // Roll the rows up by one.
        for (int i = 0; i < MAX_W; i++) { r0[i] = r1[i]; r1[i] = r2[i]; r2[i] = 0.0; }
    }

    gl_FragColor = vec4(vec3(result), 1.0);
}
