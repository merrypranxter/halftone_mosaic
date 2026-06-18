#version 300 es
precision mediump float;
precision mediump int;

uniform sampler2D u_texture;
uniform vec2 u_resolution;
uniform int u_levels;

out vec4 fragColor;

float luminance(vec3 c) {
    return dot(c, vec3(0.299, 0.587, 0.114));
}

float quantizeLevel(float v) {
    float steps = float(max(u_levels, 2) - 1);
    return floor(clamp(v, 0.0, 1.0) * steps + 0.5) / steps;
}

float neighborError(vec2 uv, vec2 pixelOffset) {
    vec2 sampleUV = clamp(uv + pixelOffset / u_resolution, vec2(0.0), vec2(1.0));
    float l = luminance(texture(u_texture, sampleUV).rgb);
    return l - quantizeLevel(l);
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec3 src = texture(u_texture, uv).rgb;
    float lum = luminance(src);

    // Atkinson dithering spreads 1/8 of the quantization error to six future pixels:
    // right, right+2, below-left, below, below-right, and two rows below. As with any
    // single-pass fragment shader, we cannot mutate neighboring pixels directly, so we
    // approximate the incoming error by sampling the set of prior neighbors that would
    // have contributed to the current pixel in a CPU implementation.
    float diffusedError = (
        neighborError(uv, vec2(-1.0,  0.0)) +
        neighborError(uv, vec2(-2.0,  0.0)) +
        neighborError(uv, vec2( 1.0, -1.0)) +
        neighborError(uv, vec2( 0.0, -1.0)) +
        neighborError(uv, vec2(-1.0, -1.0)) +
        neighborError(uv, vec2( 0.0, -2.0))
    ) * 0.125;

    float adjusted = clamp(lum + diffusedError, 0.0, 1.0);
    float ditheredLum = quantizeLevel(adjusted);
    vec3 result = (lum > 1e-4) ? src * (ditheredLum / lum) : vec3(ditheredLum);

    fragColor = vec4(clamp(result, 0.0, 1.0), 1.0);
}
