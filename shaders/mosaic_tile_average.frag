#version 300 es
precision mediump float;
precision mediump int;

uniform sampler2D u_texture;
uniform vec2 u_resolution;
uniform float u_tile_size;
uniform bool u_show_border;
uniform bool u_brick_offset;

out vec4 fragColor;

void main() {
    float tile = max(u_tile_size, 1.0);
    vec2 pixel = gl_FragCoord.xy;

    float row = floor(pixel.y / tile);
    float shift = (u_brick_offset && mod(row, 2.0) > 0.5) ? 0.5 * tile : 0.0;

    float shiftedX = pixel.x - shift;
    float col = floor(shiftedX / tile);
    vec2 local = vec2(shiftedX - col * tile, pixel.y - row * tile);

    vec2 tileCenter = vec2((col + 0.5) * tile + shift, (row + 0.5) * tile);
    vec2 sampleUV = clamp(tileCenter / u_resolution, vec2(0.0), vec2(1.0));
    vec3 color = texture(u_texture, sampleUV).rgb;

    if (u_show_border) {
        float edgeDist = min(min(local.x, tile - local.x), min(local.y, tile - local.y));
        float borderMask = smoothstep(0.0, 1.0, edgeDist);
        color = mix(vec3(0.0), color, borderMask);
    }

    fragColor = vec4(color, 1.0);
}
