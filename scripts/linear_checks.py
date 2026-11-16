#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Exercise the actual DPU modifier policy and plane advertisement offline."""
from pathlib import Path
import re
import subprocess
import tempfile


def plane_functions(source):
    text = (Path(source) / 'drivers/gpu/drm/msm/disp/dpu1/dpu_plane.c').read_text()
    parts = []
    for signature in ('static bool y900_linear_scanout',
                      'static const uint32_t qcom_compressed_supported_formats[]',
                      'static const uint64_t supported_format_modifiers[]',
                      'static const u64 linear_format_modifiers[]'):
        start = text.index(signature)
        parts.append(text[start:text.index(';', start) + 1])
    for signature in ('static bool dpu_plane_linear_scanout(',
                      'static bool dpu_plane_format_mod_supported(',
                      'static struct drm_plane *dpu_plane_init_common('):
        start = text.index(signature)
        parts.append(text[start:text.index('\n}\n', start) + 3])
    assert re.search(r'module_param_named\(dpu_linear_scanout,\s*'
                     r'y900_linear_scanout,\s*bool,\s*0400\);', text)
    return '\n\n'.join(parts)


HARNESS = r'''
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef uint64_t u64;
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
#define BIT(n) (1U << (n))
#define DPU_ZPOS_MAX 10
#define DRM_MODE_BLEND_PIXEL_NONE 0
#define DRM_MODE_BLEND_PREMULTI 1
#define DRM_MODE_BLEND_COVERAGE 2
#define DRM_MODE_ROTATE_0 1
#define DRM_MODE_ROTATE_180 4
#define DRM_MODE_ROTATE_MASK 15
#define DRM_MODE_REFLECT_MASK 48
#define DRM_FORMAT_MOD_LINEAR 0ULL
#define DRM_FORMAT_MOD_QCOM_COMPRESSED 0x500000000000001ULL
#define DRM_FORMAT_MOD_INVALID 0x00ffffffffffffffULL
#define DRM_FORMAT_ABGR8888 1
#define DRM_FORMAT_ARGB8888 2
#define DRM_FORMAT_XBGR8888 3
#define DRM_FORMAT_XRGB8888 4
#define DRM_FORMAT_ARGB2101010 5
#define DRM_FORMAT_XRGB2101010 6
#define DRM_FORMAT_BGR565 7
#define DRM_FORMAT_NV12 8
#define DRM_FORMAT_P010 9
#define DPU_ERROR(...) ((void)0)
#define DPU_DEBUG(...) ((void)0)
#define IS_ERR(p) ((uintptr_t)(p) == (uintptr_t)-12)
#define ERR_CAST(p) ((void *)(p))
enum drm_plane_type { PRIMARY, OVERLAY, CURSOR };
enum dpu_sspp { PIPE = 8 };
struct drm_plane { int unused; };
struct mdss { unsigned int ubwc_enc_version; };
struct dpu_kms { struct mdss *mdss; void *catalog; };
struct msm_drm_private { struct dpu_kms *kms; };
struct drm_device { struct msm_drm_private *dev_private; };
struct dpu_plane { struct drm_plane base; enum dpu_sspp pipe; void *catalog; };
static struct mdss mdss;
static struct dpu_kms kms = { .mdss = &mdss, .catalog = &mdss };
static struct dpu_plane allocated;
static bool board, allocation_fail;
static const uint64_t *advertised;
static unsigned int rotations, cases;
static int zpos_result;
static bool of_machine_is_compatible(const char *name)
{ assert(!strcmp(name, "lenovo,y900")); return board; }
static struct dpu_kms *_dpu_plane_get_kms(struct drm_plane *plane)
{ assert(plane == &allocated.base); return &kms; }
static struct dpu_kms *to_dpu_kms(struct dpu_kms *ptr) { return ptr; }
static bool dpu_find_format(uint32_t format, const uint32_t *list, size_t n)
{ for (size_t i = 0; i < n; ++i) if (list[i] == format) return true; return false; }
static struct dpu_plane *allocate_plane(struct drm_device *dev,
        const uint32_t *formats, uint32_t count, const uint64_t *modifiers,
        enum drm_plane_type type)
{
    assert(dev->dev_private->kms == &kms && formats && count == 1);
    assert(type >= PRIMARY && type <= CURSOR);
    advertised = modifiers;
    return allocation_fail ? (void *)(uintptr_t)-12 : &allocated;
}
#define drmm_universal_plane_alloc(d, t, m, mask, f, fs, n, mods, type, name) \
    allocate_plane(d, fs, n, mods, type)
static int drm_plane_create_zpos_property(struct drm_plane *p, int v, int lo, int hi)
{ assert(p == &allocated.base && v == 0 && lo == 0 && hi == DPU_ZPOS_MAX); return zpos_result; }
static void drm_plane_create_alpha_property(struct drm_plane *p)
{ assert(p == &allocated.base); }
static void drm_plane_create_blend_mode_property(struct drm_plane *p, unsigned int mask)
{ assert(p == &allocated.base && mask == 7); }
static void drm_plane_create_rotation_property(struct drm_plane *p, int initial, unsigned int mask)
{ assert(p == &allocated.base && initial == DRM_MODE_ROTATE_0); rotations = mask; }
static void drm_plane_enable_fb_damage_clips(struct drm_plane *p)
{ assert(p == &allocated.base); }

ACTUAL_FUNCTIONS

int main(void)
{
    struct msm_drm_private priv = { .kms = &kms };
    struct drm_device dev = { .dev_private = &priv };
    const uint32_t format = DRM_FORMAT_XRGB8888;
    assert(!y900_linear_scanout);
    for (unsigned int b = 0; b < 2; ++b)
    for (unsigned int opt = 0; opt < 2; ++opt)
    for (unsigned int ubwc = 0; ubwc < 2; ++ubwc) {
        board = b;
        y900_linear_scanout = opt;
        mdss.ubwc_enc_version = ubwc;
        bool linear = b && opt;
        assert(dpu_plane_linear_scanout() == linear);
        for (unsigned int f = 1; f <= 10; ++f) {
            assert(dpu_plane_format_mod_supported(&allocated.base, f, DRM_FORMAT_MOD_LINEAR));
            assert(dpu_plane_format_mod_supported(&allocated.base, f,
                       DRM_FORMAT_MOD_QCOM_COMPRESSED) == (!linear && ubwc && f <= 9));
            assert(!dpu_plane_format_mod_supported(&allocated.base, f, 0x1234));
            ++cases;
        }
        for (unsigned int rotate = 0; rotate < 2; ++rotate)
        for (enum drm_plane_type type = PRIMARY; type <= CURSOR; ++type) {
            struct drm_plane *p = dpu_plane_init_common(&dev, type, 0xff, rotate,
                                                        &format, 1, PIPE);
            assert(p == &allocated.base && allocated.pipe == PIPE);
            assert(allocated.catalog == kms.catalog);
            assert(rotations == (DRM_MODE_REFLECT_MASK |
                       (rotate ? DRM_MODE_ROTATE_MASK : DRM_MODE_ROTATE_0 | DRM_MODE_ROTATE_180)));
            assert(advertised[0] == (linear ? DRM_FORMAT_MOD_LINEAR : DRM_FORMAT_MOD_QCOM_COMPRESSED));
            if (linear) assert(advertised[1] == DRM_FORMAT_MOD_INVALID);
            else assert(advertised[1] == DRM_FORMAT_MOD_LINEAR && advertised[2] == DRM_FORMAT_MOD_INVALID);
            ++cases;
        }
    }
    allocation_fail = true;
    assert(IS_ERR(dpu_plane_init_common(&dev, PRIMARY, 0xff, false, &format, 1, PIPE)));
    allocation_fail = false;
    zpos_result = -22;
    assert(dpu_plane_init_common(&dev, PRIMARY, 0xff, false, &format, 1, PIPE) == &allocated.base);
    printf("DPU actual modifier/advertisement checks: %u cases + 2 error paths\n", cases);
    return 0;
}
'''


def execute_plane_functions(functions):
    with tempfile.TemporaryDirectory(prefix='dpu-linear-check-') as directory:
        root = Path(directory)
        program = root / 'check.c'
        program.write_text(HARNESS.replace('ACTUAL_FUNCTIONS', functions))
        executable = root / 'check'
        subprocess.run(['cc', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                        '-Wno-unused-parameter', str(program), '-o', str(executable)], check=True)
        subprocess.run([str(executable)], check=True)


def check_linear_scanout(source):
    execute_plane_functions(plane_functions(source))
