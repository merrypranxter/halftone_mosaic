#version 300 es
precision mediump float;
precision mediump int;

uniform sampler2D u_texture;
uniform vec2 u_resolution;
uniform int u_levels;
uniform int u_matrix_size;

out vec4 fragColor;

const float BAYER2[4] = float[](
    0.0, 2.0,
    3.0, 1.0
);

const float BAYER4[16] = float[](
     0.0,  8.0,  2.0, 10.0,
    12.0,  4.0, 14.0,  6.0,
     3.0, 11.0,  1.0,  9.0,
    15.0,  7.0, 13.0,  5.0
);

const float BAYER8[64] = float[](
     0.0, 32.0,  8.0, 40.0,  2.0, 34.0, 10.0, 42.0,
    48.0, 16.0, 56.0, 24.0, 50.0, 18.0, 58.0, 26.0,
    12.0, 44.0,  4.0, 36.0, 14.0, 46.0,  6.0, 38.0,
    60.0, 28.0, 52.0, 20.0, 62.0, 30.0, 54.0, 22.0,
     3.0, 35.0, 11.0, 43.0,  1.0, 33.0,  9.0, 41.0,
    51.0, 19.0, 59.0, 27.0, 49.0, 17.0, 57.0, 25.0,
    15.0, 47.0,  7.0, 39.0, 13.0, 45.0,  5.0, 37.0,
    63.0, 31.0, 55.0, 23.0, 61.0, 29.0, 53.0, 21.0
);

float bayerThreshold(ivec2 p) {
    if (u_matrix_size == 2) {
        ivec2 q = ivec2(p.x % 2, p.y % 2);
        return (BAYER2[q.y * 2 + q.x] + 0.5) / 4.0;
    }
    if (u_matrix_size == 4) {
        ivec2 q = ivec2(p.x % 4, p.y % 4);
        return (BAYER4[q.y * 4 + q.x] + 0.5) / 16.0;
    }
    ivec2 q = ivec2(p.x % 8, p.y % 8);
    return (BAYER8[q.y * 8 + q.x] + 0.5) / 64.0;
}

float ditherChannel(float v, float threshold) {
    float levels = float(max(u_levels, 2) - 1);
    float scaled = clamp(v, 0.0, 1.0) * levels;
    float base = floor(scaled);
    float fracPart = fract(scaled);
    return (base + step(threshold, fracPart)) / levels;
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec3 src = texture(u_texture, uv).rgb;
    float threshold = bayerThreshold(ivec2(gl_FragCoord.xy));

    vec3 result = vec3(
        ditherChannel(src.r, threshold),
        ditherChannel(src.g, threshold),
        ditherChannel(src.b, threshold)
    );

    fragColor = vec4(clamp(result, 0.0, 1.0), 1.0);
}
