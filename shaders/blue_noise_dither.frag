#version 300 es
precision mediump float;
precision mediump int;

uniform sampler2D u_texture;
uniform vec2 u_resolution;
uniform sampler2D u_blue_noise;
uniform int u_levels;
uniform bool u_use_procedural;

out vec4 fragColor;

float luminance(vec3 c) {
    return dot(c, vec3(0.299, 0.587, 0.114));
}

float ign(vec2 p) {
    return fract(52.9829189 * fract(0.06711056 * p.x + 0.00583715 * p.y));
}

float blueNoiseThreshold() {
    if (u_use_procedural) {
        return ign(gl_FragCoord.xy);
    }

    vec2 noiseSize = vec2(textureSize(u_blue_noise, 0));
    vec2 tiledUV = fract(gl_FragCoord.xy / max(noiseSize, vec2(1.0)));
    return texture(u_blue_noise, tiledUV).r;
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec3 src = texture(u_texture, uv).rgb;
    float lum = luminance(src);
    float threshold = blueNoiseThreshold();

    float levels = float(max(u_levels, 2) - 1);
    float scaled = clamp(lum, 0.0, 1.0) * levels;
    float base = floor(scaled);
    float fracPart = fract(scaled);
    float ditheredLum = (base + step(threshold, fracPart)) / levels;

    vec3 result = (lum > 1e-4) ? src * (ditheredLum / lum) : vec3(ditheredLum);
    fragColor = vec4(clamp(result, 0.0, 1.0), 1.0);
}
