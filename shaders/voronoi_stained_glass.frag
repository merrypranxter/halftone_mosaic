#version 300 es
precision mediump float;
precision mediump int;

uniform sampler2D u_texture;
uniform vec2 u_resolution;
uniform int u_num_seeds;
uniform float u_border_width;
uniform vec3 u_border_color;

out vec4 fragColor;

vec2 hash2(vec2 p) {
    return fract(sin(vec2(
        dot(p, vec2(127.1, 311.7)),
        dot(p, vec2(269.5, 183.3))
    )) * 43758.5453123);
}

vec2 seedPoint(int index, int total) {
    int grid = int(ceil(sqrt(float(max(total, 1)))));
    int gx = index % grid;
    int gy = index / grid;

    vec2 cell = (vec2(float(gx), float(gy)) + 0.5) / float(grid);
    vec2 jitter = (hash2(vec2(float(index), float(total))) - 0.5) * (0.9 / float(grid));
    return clamp(cell + jitter, vec2(0.0), vec2(1.0));
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    int seedCount = clamp(u_num_seeds, 1, 64);

    float nearest = 1e9;
    float secondNearest = 1e9;
    vec2 nearestSeed = vec2(0.5);

    for (int i = 0; i < 64; ++i) {
        if (i >= seedCount) {
            break;
        }

        vec2 seed = seedPoint(i, seedCount);
        float d = distance(uv, seed);

        if (d < nearest) {
            secondNearest = nearest;
            nearest = d;
            nearestSeed = seed;
        } else if (d < secondNearest) {
            secondNearest = d;
        }
    }

    vec3 cellColor = texture(u_texture, nearestSeed).rgb;
    float borderBlend = smoothstep(0.0, max(u_border_width, 1e-5), secondNearest - nearest);
    vec3 result = mix(u_border_color, cellColor, borderBlend);

    fragColor = vec4(clamp(result, 0.0, 1.0), 1.0);
}
