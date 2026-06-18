#version 300 es
precision mediump float;
precision mediump int;

uniform sampler2D u_texture;
uniform vec2 u_resolution;
uniform float u_dot_frequency;
uniform int u_dot_shape; // 0 = round, 1 = square, 2 = ellipse

out vec4 fragColor;

const float PI = 3.14159265358979323846;

mat2 rotation(float angle) {
    float s = sin(angle);
    float c = cos(angle);
    return mat2(c, -s, s, c);
}

vec4 rgbToCmyk(vec3 rgb) {
    float k = 1.0 - max(max(rgb.r, rgb.g), rgb.b);
    if (k >= 0.999) {
        return vec4(0.0, 0.0, 0.0, 1.0);
    }

    float inv = max(1.0 - k, 1e-5);
    float c = (1.0 - rgb.r - k) / inv;
    float m = (1.0 - rgb.g - k) / inv;
    float y = (1.0 - rgb.b - k) / inv;
    return clamp(vec4(c, m, y, k), 0.0, 1.0);
}

float shapeDistance(vec2 p, int shape) {
    vec2 d = abs(p);
    if (shape == 1) {
        return max(d.x, d.y);
    }
    if (shape == 2) {
        return length(p / vec2(1.35, 0.8));
    }
    return length(p);
}

float halftoneMask(vec2 uv, float amount, float angle) {
    float freq = max(u_dot_frequency, 1.0);
    vec2 rotated = rotation(angle) * (uv * freq);
    vec2 local = fract(rotated) - 0.5;
    float radius = 0.5 * sqrt(clamp(amount, 0.0, 1.0));
    float dist = shapeDistance(local, u_dot_shape);
    return 1.0 - step(radius, dist);
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec3 rgb = texture(u_texture, uv).rgb;
    vec4 cmyk = rgbToCmyk(rgb);

    float cyanMask = halftoneMask(uv, cmyk.x, radians(15.0));
    float magentaMask = halftoneMask(uv, cmyk.y, radians(45.0));
    float yellowMask = halftoneMask(uv, cmyk.z, radians(75.0));
    float blackMask = halftoneMask(uv, cmyk.w, radians(0.0));

    vec3 result = vec3(1.0);
    result *= mix(vec3(1.0), vec3(0.0, 1.0, 1.0), cyanMask);
    result *= mix(vec3(1.0), vec3(1.0, 0.0, 1.0), magentaMask);
    result *= mix(vec3(1.0), vec3(1.0, 1.0, 0.0), yellowMask);
    result *= mix(vec3(1.0), vec3(0.0), blackMask);

    fragColor = vec4(clamp(result, 0.0, 1.0), 1.0);
}
