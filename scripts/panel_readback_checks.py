#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Execute the opt-in readback and actual enable callback against failure paths."""
from pathlib import Path
import re
import subprocess
import tempfile


def function(text, signature):
    match = re.search(r'^' + re.escape(signature) + r'[^;{}]*\n\{', text, re.MULTILINE)
    assert match, signature
    return text[match.start():text.index('\n}\n', match.start()) + 3]


def check_panel_readback(source, panel_text=None):
    path = Path(source) / 'drivers/gpu/drm/panel/panel-novatek-nt36536.c'
    text = path.read_text() if panel_text is None else panel_text
    assert 'static bool power_mode_probe;' in text
    assert 'module_param(power_mode_probe, bool, 0400);' in text
    actual = '\n'.join(function(text, name) for name in (
        'static void novatek_read_power_mode(', 'static int novatek_enable('))
    with tempfile.TemporaryDirectory(prefix='tb522fu-panel-readback-') as directory:
        c = Path(directory) / 'check.c'
        binary = Path(directory) / 'check'
        c.write_text(HARNESS.replace('ACTUAL_SOURCE', actual))
        subprocess.run(['cc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', str(c),
                        '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)


HARNESS = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
typedef unsigned char u8;
#define dev_dbg(...) ((void)0)
#define dev_info(...) capture_info(__VA_ARGS__)
#define dev_err(...) ((void)0)
#define crc32_le(...) 0u
struct drm_panel { int dev; };
struct mipi_dsi_device { struct { bool of_node; } dev; };
struct mipi_dsi_multi_context { struct mipi_dsi_device *dsi; int accum_err; };
struct drm_dsc_config { unsigned int pic_width, pic_height, slice_width,
 slice_height, slice_count, bits_per_pixel, bits_per_component; };
struct drm_dsc_picture_parameter_set { int unused; };
struct panel_desc { int (*init_sequence)(struct mipi_dsi_multi_context *); };
struct novatek { struct drm_panel panel; struct mipi_dsi_device *dsi[2];
 const struct panel_desc *desc; struct drm_dsc_config dsc; int *backlight; };
static struct novatek ctx;
static struct mipi_dsi_device dsi[2];
static bool power_mode_probe;
static int phase, reads, init_error, pps_error, backlight_error, read_error;
static int reported_ret, reported_mode, reports;
static void capture_info(int dev, const char *format, ...)
{
 (void)dev;
 if(strstr(format,"DISPLAY_PANEL_POWER")) {
  va_list ap; va_start(ap,format);
  reported_ret=va_arg(ap,int); reported_mode=va_arg(ap,int); va_end(ap); reports++;
 }
}
static struct novatek *to_novatek(struct drm_panel *p) { assert(p==&ctx.panel); return &ctx; }
static struct mipi_dsi_device *to_primary_dsi(struct novatek *c) { assert(c==&ctx); return &dsi[1]; }
static bool of_device_is_compatible(bool node, const char *s)
{ assert(!strcmp(s,"lenovo,y900-boe-nt36536e")); return node; }
static void y900_dsi_panel_init_begin(void) { assert(phase==0); }
static void y900_dsi_panel_init_end(void) { }
static int init_sequence(struct mipi_dsi_multi_context *d)
{ assert(d->dsi==&dsi[1] && phase==0); phase=1; return init_error; }
static void drm_dsc_pps_payload_pack(struct drm_dsc_picture_parameter_set *p,
                                   struct drm_dsc_config *d)
{ (void)p; (void)d; assert(phase==1); phase=2; }
static void mipi_dsi_picture_parameter_set_multi(struct mipi_dsi_multi_context *d,
                                               struct drm_dsc_picture_parameter_set *p)
{ (void)p; assert(phase==2); phase=3; d->accum_err=pps_error; }
static void mipi_dsi_compression_mode_multi(struct mipi_dsi_multi_context *d, bool on)
{ (void)d; assert(phase==3 && on); phase=4; }
static void mipi_dsi_msleep(struct mipi_dsi_multi_context *d, unsigned int ms)
{ (void)d; assert(phase==4 && ms==28); phase=5; }
static int backlight_enable(int *b)
{ (void)b; assert(phase==5); phase=6; return backlight_error; }
static int mipi_dsi_dcs_get_power_mode(struct mipi_dsi_device *d, u8 *mode)
{ assert(d==&dsi[0] && phase==6 && !backlight_error); reads++; *mode=0x9c; return read_error; }
ACTUAL_SOURCE
static void setup(bool probe, bool boe)
{
 memset(&ctx,0,sizeof(ctx)); memset(dsi,0,sizeof(dsi));
 static const struct panel_desc desc={.init_sequence=init_sequence};
 ctx.dsi[0]=&dsi[0]; ctx.dsi[1]=&dsi[1]; ctx.desc=&desc; dsi[0].dev.of_node=boe;
 power_mode_probe=probe; phase=reads=init_error=pps_error=backlight_error=read_error=0;
 reported_ret=reported_mode=reports=0;
}
int main(void)
{
 for(int probe=0;probe<2;probe++)for(int boe=0;boe<2;boe++) {
  setup(probe,boe); assert(!novatek_enable(&ctx.panel)); assert(reads==(probe&&boe));
  assert(reports==reads); if(reads)assert(!reported_ret && reported_mode==0x9c);
 }
 const int errors[]={-EIO,-ENODATA,-ETIMEDOUT};
 for(unsigned i=0;i<sizeof(errors)/sizeof(errors[0]);i++) {
  setup(true,true); read_error=errors[i];
  assert(!novatek_enable(&ctx.panel) && reads==1); /* Diagnostic errors stay explicit. */
  assert(reports==1 && reported_ret==errors[i] && reported_mode==0x9c);
 }
 for(int failure=0;failure<3;failure++) {
  setup(true,true);
  if(failure==0)init_error=-EIO;
  if(failure==1)pps_error=-EIO;
  if(failure==2)backlight_error=-EIO;
  assert(novatek_enable(&ctx.panel)==-EIO && !reads);
 }
 puts("panel readback: opt-in/BOE/physical-host/enable ordering and all failure paths passed");
 return 0;
}
'''
