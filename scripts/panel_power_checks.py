#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Exercise the actual panel power functions against the stock bias sequence."""
from pathlib import Path
import re
import subprocess
import tempfile


def function(text, signature):
    match = re.search(r'^' + re.escape(signature) + r'[^;{}]*\n\{', text, re.MULTILINE)
    assert match, 'Missing function: ' + signature
    start = match.start()
    return text[start:text.index('\n}\n', start) + 3]


def check_panel_power(source, panel_text=None):
    path = Path(source) / 'drivers/gpu/drm/panel/panel-novatek-nt36536.c'
    text = panel_text if panel_text is not None else path.read_text()
    names = ('static void novatek_bias_enable(', 'static void novatek_bias_disable(',
             'static void novatek_reset(', 'static int novatek_prepare(',
             'static int novatek_unprepare(')
    actual = '\n'.join(function(text, name) for name in names)
    with tempfile.TemporaryDirectory(prefix='tb522fu-panel-power-') as directory:
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
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#define y900_dev_info(...) ((void)0)
#define dev_dbg(...) ((void)0)
struct regulator { int id, refs; };
struct regulator_bulk_data { struct regulator *consumer; };
struct gpio_desc { int id, value; };
struct drm_panel { int dev; };
struct panel_desc {
 const unsigned int *supply_on_delays_us;
 unsigned int post_on_delay_us;
};
struct novatek {
 struct drm_panel panel; const struct panel_desc *desc;
 struct gpio_desc *reset_gpio, *vsp_gpio, *vsn_gpio;
 struct regulator_bulk_data *supplies; int num_supplies;
};
static struct novatek ctx;
static struct regulator regs[3];
static struct regulator_bulk_data supplies[3];
static struct gpio_desc positive={.id=0}, negative={.id=1};
static unsigned int now, positive_at, negative_off_at;
static int fail_enable, up_calls, down_calls, gpio_calls, bulk_up, bulk_down;
static const unsigned int on_delays[]={20000,0,20000};
static struct novatek *to_novatek(struct drm_panel *p) { assert(p==&ctx.panel); return &ctx; }
static void usleep_range(unsigned int lo, unsigned int hi) { assert(hi>=lo); now+=lo; }
static void gpiod_set_value_cansleep(struct gpio_desc *g, int value)
{
 assert(g==&positive || g==&negative);
 gpio_calls++;
 if(g==&positive) {
  if(value) {
   for(int i=0;i<3;i++)assert(regs[i].refs==1);
   positive_at=now;
  } else { assert(!negative.value && now-negative_off_at>=5000); }
 } else {
  if(value)assert(positive.value && now-positive_at>=5000);
  else negative_off_at=now;
 }
 g->value=value;
}
static int regulator_enable(struct regulator *r)
{
 assert(r->refs==0);
 assert(up_calls++==r->id);
 if(r->id==fail_enable)return -EIO;
 r->refs++; return 0;
}
static int regulator_disable(struct regulator *r)
{
 if(ctx.vsp_gpio)assert(!negative.value && !positive.value);
 assert(r->refs==1); r->refs--; down_calls++; return 0;
}
static int regulator_bulk_enable(int n, struct regulator_bulk_data *s)
{
 bulk_up++;
 for(int i=0;i<n;i++)assert(!regulator_enable(s[i].consumer));
 return 0;
}
static int regulator_bulk_disable(int n, struct regulator_bulk_data *s)
{
 bulk_down++;
 while(n--)assert(!regulator_disable(s[n].consumer));
 return 0;
}
ACTUAL_SOURCE
static void setup(bool bias, bool ordered)
{
 memset(&ctx,0,sizeof(ctx));
 static struct panel_desc desc;
 desc=(struct panel_desc){.supply_on_delays_us=ordered?on_delays:NULL};
 ctx.desc=&desc; ctx.supplies=supplies; ctx.num_supplies=3;
 for(int i=0;i<3;i++){regs[i]=(struct regulator){.id=i}; supplies[i].consumer=&regs[i];}
 positive.value=negative.value=1; /* Bootloader handover. */
 if(bias){ctx.vsp_gpio=&positive; ctx.vsn_gpio=&negative;}
 now=positive_at=negative_off_at=0;
 fail_enable=-1; up_calls=down_calls=gpio_calls=bulk_up=bulk_down=0;
}
int main(void)
{
 setup(true,true);
 for(int cycle=0;cycle<3;cycle++) {
  now=positive_at=negative_off_at=0;
  up_calls=down_calls=gpio_calls=bulk_up=bulk_down=0;
  assert(novatek_prepare(&ctx.panel)==0);
  assert(now==56000 && gpio_calls==2 && positive.value && negative.value);
  assert(novatek_unprepare(&ctx.panel)==0);
  assert(now==61000 && gpio_calls==4 && !positive.value && !negative.value);
  assert(down_calls==3 && !bulk_up && bulk_down==1);
  for(int i=0;i<3;i++)assert(!regs[i].refs);
 }
 for(int failure=0;failure<3;failure++) {
  setup(true,true); fail_enable=failure;
  assert(novatek_prepare(&ctx.panel)==-EIO);
  assert(up_calls==failure+1 && down_calls==failure);
  assert(gpio_calls==2 && !positive.value && !negative.value);
  for(int i=0;i<3;i++)assert(!regs[i].refs);
 }
 setup(false,false);
 assert(novatek_prepare(&ctx.panel)==0 && bulk_up==1 && !gpio_calls);
 assert(novatek_unprepare(&ctx.panel)==0 && bulk_down==1 && !gpio_calls);
 setup(false,true);
 assert(novatek_prepare(&ctx.panel)==0 && !gpio_calls && now==40000);
 assert(novatek_unprepare(&ctx.panel)==0 && !gpio_calls);
 puts("panel power: stock bias ordering/discharge, three enable failures, legacy paths passed");
 return 0;
}
'''
