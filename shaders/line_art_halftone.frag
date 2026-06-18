#version 300 es
precision mediump float;
precision mediump int;

uniform sampler2D u_texture;
uniform vec2 u_resolution;
uniform float u_line_frequency;
uniform float u_line_angle;
uniform int u_line_type; // 0 = parallel, 1 = crosshatch, 2 = contour

out vec4 fragColor;

mat2 rotation(float angle) {
    float s = sin(angle);
    float c = cos(angle);
    return mat2(c, -s, s, c);
}

float luminance(vec3 c) {
    return dot(c, vec3(0.299, 0.587, 0.114));
}

float lineMask(vec2 p, float darkness) {
    float coord = fract(p.y * max(u_line_frequency, 1.0)) - 0.5;
    float halfThickness = mix(0.02, 0.48, clamp(darkness, 0.0, 1.0));
    return 1.0 - step(halfThickness, abs(coord));
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec3 src = texture(u_texture, uv).rgb;
    float lum = luminance(src);
    float darkness = 1.0 - lum;

    vec2 centered = uv - 0.5;
    float angle = radians(u_line_angle);
    vec2 rotated = rotation(angle) * centered;

    float ink = lineMask(rotated, darkness);

    if (u_line_type == 1) {
        vec2 cross = rotation(angle + 1.57079632679) * centered;
        float crossDarkness = clamp((darkness - 0.35) / 0.65, 0.0, 1.0);
        ink = max(ink, lineMask(cross, crossDarkness));
    } else if (u_line_type == 2) {
        float contourField = rotated.y * max(u_line_frequency, 1.0) + lum * 10.0;
        float contourDist = abs(fract(contourField) - 0.5);
        float contourThickness = mix(0.02, 0.18, darkness);
        ink = 1.0 - step(contourThickness, contourDist);
    }

    vec3 result = mix(vec3(1.0), vec3(0.0), ink);
    fragColor = vec4(result, 1.0);
}
