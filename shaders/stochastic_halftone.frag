#version 300 es
precision mediump float;
precision mediump int;

uniform sampler2D u_texture;
uniform vec2 u_resolution;
uniform float u_dot_size;
uniform float u_seed;

out vec4 fragColor;

float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float luminance(vec3 c) {
    return dot(c, vec3(0.299, 0.587, 0.114));
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec3 src = texture(u_texture, uv).rgb;
    float darkness = 1.0 - luminance(src);

    float cellSize = max(u_dot_size * 1.5, 1.0);
    vec2 cell = floor(gl_FragCoord.xy / cellSize);
    vec2 local = mod(gl_FragCoord.xy, cellSize) - 0.5 * cellSize;

    float rnd = hash21(cell + vec2(u_seed, u_seed * 1.618));
    float occupied = step(rnd, darkness);
    float dotMask = occupied * (1.0 - step(u_dot_size * 0.5, length(local)));

    vec3 result = mix(vec3(1.0), vec3(0.0), dotMask);
    fragColor = vec4(result, 1.0);
}
