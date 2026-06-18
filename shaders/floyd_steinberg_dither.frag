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

    // True Floyd-Steinberg dithering is a scanline CPU algorithm that quantizes a pixel,
    // computes its error, and distributes that error to future neighbors (7/16, 3/16,
    // 5/16, 1/16). A single fragment shader has no writable neighborhood state, so this
    // WebGL2 version estimates the incoming diffused error by sampling already-visited
    // neighbors and reusing their quantization error as a local spatial approximation.
    float diffusedError =
        neighborError(uv, vec2(-1.0,  0.0)) * (7.0 / 16.0) +
        neighborError(uv, vec2(-1.0, -1.0)) * (3.0 / 16.0) +
        neighborError(uv, vec2( 0.0, -1.0)) * (5.0 / 16.0) +
        neighborError(uv, vec2( 1.0, -1.0)) * (1.0 / 16.0);

    float adjusted = clamp(lum + diffusedError, 0.0, 1.0);
    float ditheredLum = quantizeLevel(adjusted);
    vec3 result = (lum > 1e-4) ? src * (ditheredLum / lum) : vec3(ditheredLum);

    fragColor = vec4(clamp(result, 0.0, 1.0), 1.0);
}
