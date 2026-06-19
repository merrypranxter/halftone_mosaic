// mosaic_tile_average.frag — square (or brick) tiles rendered as a flat color.
//
// The image is divided into a grid of tiles. Each fragment finds its tile,
// samples the image at the tile center (a cheap stand-in for the tile's
// average — exact averaging needs a mip / multi-tap, see u_samples), and
// paints the whole tile that one color. Large tiles abstract the image into
// blocks of pure tone; the tile becomes the pixel.
//
// Optional brick offset shifts every other row by half a tile, breaking the
// rigid grid into a masonry pattern.
//
// Uniforms:
//   u_resolution, u_image
//   u_tile_size : tile edge in pixels (e.g. 24)
//   u_brick     : 0 grid, 1 brick offset
//   u_grout     : 0..0.5 width of dark seam between tiles (fraction of tile)
//   u_samples   : 1 = center sample, >1 = NxN box average for true mean color

#ifdef GL_ES
precision highp float;
#endif

#include "common.glsl"

uniform vec2  u_resolution;
uniform sampler2D u_image;
uniform float u_tile_size; // e.g. 24.0
uniform int   u_brick;     // 0 / 1
uniform float u_grout;     // e.g. 0.06
uniform int   u_samples;   // e.g. 3

const int MAX_S = 6;

void main() {
    vec2 fragPx = gl_FragCoord.xy;
    float ts = max(u_tile_size, 1.0);

    // Determine row to apply brick offset on the X axis.
    float row = floor(fragPx.y / ts);
    float xoff = (u_brick == 1 && mod(row, 2.0) == 1.0) ? ts * 0.5 : 0.0;

    vec2 shifted = vec2(fragPx.x - xoff, fragPx.y);
    vec2 tileId  = floor(shifted / ts);
    vec2 local   = fract(shifted / ts);        // [0,1] within tile
    vec2 center  = (tileId + 0.5) * ts + vec2(xoff, 0.0);

    // Average color over an NxN box centered on the tile (gamma-correct).
    int S = u_samples < 1 ? 1 : (u_samples > MAX_S ? MAX_S : u_samples);
    vec3 acc = vec3(0.0);
    float count = 0.0;
    for (int j = 0; j < MAX_S; j++) {
        if (j >= S) break;
        for (int i = 0; i < MAX_S; i++) {
            if (i >= S) break;
            vec2 off = (vec2(float(i), float(j)) / float(S) - 0.5) * ts;
            vec2 uv = (center + off) / u_resolution;
            acc += srgb2linear(texture2D(u_image, uv).rgb);
            count += 1.0;
        }
    }
    vec3 col = linear2srgb(acc / count);

    // Grout: dark seam near tile edges.
    float edge = min(min(local.x, 1.0 - local.x), min(local.y, 1.0 - local.y));
    float seam = smoothstep(0.0, u_grout, edge);
    col = mix(vec3(0.06), col, seam);

    gl_FragColor = vec4(col, 1.0);
}
