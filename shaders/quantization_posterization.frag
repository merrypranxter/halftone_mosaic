#version 300 es
precision mediump float;
precision mediump int;

uniform sampler2D u_texture;
uniform vec2 u_resolution;
uniform int u_levels;
uniform float u_dither_amount;

out vec4 fragColor;

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

float luminance(vec3 c) {
    return dot(c, vec3(0.299, 0.587, 0.114));
}

float bayerThreshold() {
    ivec2 p = ivec2(gl_FragCoord.xy) % 8;
    return (BAYER8[p.y * 8 + p.x] + 0.5) / 64.0;
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec3 src = texture(u_texture, uv).rgb;
    float lum = luminance(src);

    float levels = float(max(u_levels, 2));
    float scaled = clamp(lum, 0.0, 1.0) * levels;
    float base = floor(scaled);
    float fracPart = fract(scaled);

    float threshold = mix(0.5, bayerThreshold(), clamp(u_dither_amount, 0.0, 1.0));
    float posterizedLum = clamp((base + step(threshold, fracPart)) / levels, 0.0, 1.0);
    vec3 result = (lum > 1e-4) ? src * (posterizedLum / lum) : vec3(posterizedLum);

    fragColor = vec4(clamp(result, 0.0, 1.0), 1.0);
}
