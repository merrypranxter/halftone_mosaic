// floyd_steinberg_dither.frag — error diffusion on the GPU (windowed).
//
// True Floyd-Steinberg is inherently serial: each pixel's quantization error
// feeds its not-yet-processed neighbours, so pixel N depends on pixel N-1.
// A fragment shader has no such ordering. Two honest options:
//   (a) a multi-pass / compute approach that marches scanlines (correct), or
//   (b) a *windowed* approximation: for each output pixel, replay the FS
//       recurrence over a small block of rows/cols ending at this pixel.
//
// This file implements (b). It reproduces the characteristic diagonal "worms"
// locally at modest cost. For pixel-exact output use tools/dither_applier.py
// (CPU, full-image serial diffusion).
//
// Floyd-Steinberg kernel (X = current pixel, processed left->right, top->bottom):
//       X   7/16
//   3/16 5/16 1/16
//
// Uniforms:
//   u_resolution, u_image
//   u_levels : output levels per channel (2 = 1-bit)
//   u_window : block size in pixels to replay (e.g. 16)

#ifdef GL_ES
precision highp float;
#endif

#include "common.glsl"

uniform vec2  u_resolution;
uniform sampler2D u_image;
uniform float u_levels;   // e.g. 2.0
uniform int   u_window;   // e.g. 16

const int MAX_W = 24;

float quant(float v, float levels) {
    float L = max(levels - 1.0, 1.0);
    return floor(v * L + 0.5) / L;
}

void main() {
    vec2 fragPx = floor(gl_FragCoord.xy);
    int W = u_window > MAX_W ? MAX_W : u_window;

    // Origin of the replay block (top-left in screen space).
    vec2 origin = floor(fragPx / float(W)) * float(W);

    // Error buffer for the current and next row (ping-pong by copy).
    float curr[MAX_W];
    float next[MAX_W];
    for (int i = 0; i < MAX_W; i++) { curr[i] = 0.0; next[i] = 0.0; }

    float result = 0.0;
    // March rows top (high y) to bottom to match scanline order.
    for (int ry = 0; ry < MAX_W; ry++) {
        if (ry >= W) break;
        float y = origin.y + float(W - 1 - ry);
        for (int i = 0; i < MAX_W; i++) { next[i] = 0.0; }

        for (int rx = 0; rx < MAX_W; rx++) {
            if (rx >= W) break;
            float x = origin.x + float(rx);
            vec2 uv = (vec2(x, y) + 0.5) / u_resolution;
            float old = luma(texture2D(u_image, uv).rgb) + curr[rx];
            float newv = quant(old, u_levels);
            float err = old - newv;

            // Distribute error (right, below-left, below, below-right).
            if (rx + 1 < W) curr[rx + 1] += err * 7.0 / 16.0;
            if (rx - 1 >= 0) next[rx - 1] += err * 3.0 / 16.0;
            next[rx]        += err * 5.0 / 16.0;
            if (rx + 1 < W) next[rx + 1] += err * 1.0 / 16.0;

            if (abs(x - fragPx.x) < 0.5 && abs(y - fragPx.y) < 0.5) {
                result = newv;
            }
        }
        for (int i = 0; i < MAX_W; i++) { curr[i] = next[i]; }
    }

    gl_FragColor = vec4(vec3(result), 1.0);
}
