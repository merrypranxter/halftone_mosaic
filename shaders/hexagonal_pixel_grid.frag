#version 300 es
precision mediump float;
precision mediump int;

uniform sampler2D u_texture;
uniform vec2 u_resolution;
uniform float u_hex_size;
uniform bool u_show_border;
uniform bool u_pointy_top;

out vec4 fragColor;

const float SQRT3 = 1.7320508075688772;

vec3 cubeRound(vec3 cube) {
    vec3 rounded = floor(cube + 0.5);
    vec3 diff = abs(rounded - cube);

    if (diff.x > diff.y && diff.x > diff.z) {
        rounded.x = -rounded.y - rounded.z;
    } else if (diff.y > diff.z) {
        rounded.y = -rounded.x - rounded.z;
    } else {
        rounded.z = -rounded.x - rounded.y;
    }
    return rounded;
}

vec2 pixelToAxial(vec2 p, float size, bool pointy) {
    if (pointy) {
        float q = (SQRT3 / 3.0 * p.x - 1.0 / 3.0 * p.y) / size;
        float r = (2.0 / 3.0 * p.y) / size;
        return vec2(q, r);
    }

    float q = (2.0 / 3.0 * p.x) / size;
    float r = (-1.0 / 3.0 * p.x + SQRT3 / 3.0 * p.y) / size;
    return vec2(q, r);
}

vec2 axialToPixel(vec2 h, float size, bool pointy) {
    if (pointy) {
        return size * vec2(SQRT3 * (h.x + 0.5 * h.y), 1.5 * h.y);
    }

    return size * vec2(1.5 * h.x, SQRT3 * (h.y + 0.5 * h.x));
}

vec2 roundHex(vec2 h) {
    vec3 cube = vec3(h.x, -h.x - h.y, h.y);
    vec3 rounded = cubeRound(cube);
    return vec2(rounded.x, rounded.z);
}

float sdHexagon(vec2 p, float r) {
    const vec3 k = vec3(-0.8660254, 0.5, 0.5773503);
    p = abs(p);
    p -= 2.0 * min(dot(k.xy, p), 0.0) * k.xy;
    p -= vec2(clamp(p.x, -k.z * r, k.z * r), r);
    return length(p) * sign(p.y);
}

void main() {
    float size = max(u_hex_size, 1.0);
    vec2 pixel = gl_FragCoord.xy;
    vec2 hex = roundHex(pixelToAxial(pixel, size, u_pointy_top));
    vec2 center = axialToPixel(hex, size, u_pointy_top);

    vec2 sampleUV = clamp(center / u_resolution, vec2(0.0), vec2(1.0));
    vec3 color = texture(u_texture, sampleUV).rgb;

    if (u_show_border) {
        vec2 local = pixel - center;
        if (!u_pointy_top) {
            local = mat2(0.0, -1.0, 1.0, 0.0) * local;
        }
        float dist = abs(sdHexagon(local, size * 0.95));
        float borderMask = smoothstep(0.0, 1.0, dist);
        color = mix(vec3(0.0), color, borderMask);
    }

    fragColor = vec4(color, 1.0);
}
