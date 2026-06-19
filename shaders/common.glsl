// common.glsl — shared helpers for the halftone_mosaic shader set.
//
// These shaders are written in GLSL ES 1.00 (WebGL1 / ShaderToy-compatible
// style) so they can be dropped into a ShaderToy buffer, a glslViewer pass,
// or a minimal WebGL harness. To use a snippet in ShaderToy, replace the
// uniform block + main() with mainImage(out vec4, in vec2) and map:
//     u_resolution -> iResolution.xy
//     u_time       -> iTime
//     u_image      -> iChannel0
//
// Conventions used across every shader in this folder:
//   - fragCoord  : pixel coordinates (gl_FragCoord.xy)
//   - uv         : normalized [0,1] coordinates, origin bottom-left
//   - luma()     : Rec. 709 luminance
//   - All "screens" rotate around the image center so angle changes are stable.

#ifndef HALFTONE_COMMON
#define HALFTONE_COMMON

const float PI = 3.14159265358979323846;
const float DEG2RAD = PI / 180.0;

// Rec. 709 perceptual luminance.
float luma(vec3 c) {
    return dot(c, vec3(0.2126, 0.7152, 0.0722));
}

// 2D rotation matrix for a given angle in radians.
mat2 rot(float a) {
    float s = sin(a);
    float c = cos(a);
    return mat2(c, -s, s, c);
}

// Cheap, deterministic hash -> [0,1). Good enough for FM screening / jitter.
float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 345.45));
    p += dot(p, p + 34.345);
    return fract(p.x * p.y);
}

vec2 hash22(vec2 p) {
    float n = sin(dot(p, vec2(41.0, 289.0)));
    return fract(vec2(262144.0, 32768.0) * n);
}

// sRGB <-> linear helpers. Halftoning/dithering is perceptual, so most of
// these shaders operate in gamma space on purpose; convert explicitly when
// you want physically-linear averaging (e.g. tile averaging).
vec3 srgb2linear(vec3 c) {
    return pow(c, vec3(2.2));
}
vec3 linear2srgb(vec3 c) {
    return pow(c, vec3(1.0 / 2.2));
}

#endif // HALFTONE_COMMON
