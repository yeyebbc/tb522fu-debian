#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Native display/GPU DT guards retained from the earlier bounded candidate."""
from pathlib import Path
import subprocess
import tempfile
import re

DISPLAY_MODULES = {'msm', 'dispcc_sm8750', 'ktz8866', 'panel_novatek_nt36536',
                   'gpucc_sm8750', 'gxclkctl_kaanapali'}


def check_panel_packets(source):
    """Execute the actual board init function against the stock packet contract."""
    # DVT2 on-command descriptors: 30 DCS long writes, then sleep-out/display-on.
    # Keep packet type independent of payload length, including two-byte writes.
    payloads = ('ff23 fb01 89a4 8bc1 ff2a fb01 bc7707 fff0 fb01 e602 '
                'ff27 fb01 d033 d10500 de43 df02 ffd0 fb01 0242 1caa 1d0a '
                'ff10 fb01 3b03121a040401803636 6000 900300 '
                '91aba80014d20000000252000d057a02dd 9210f0 b29180 b340 11 29').split()
    expected = []
    for i, value in enumerate(payloads):
        data = bytes.fromhex(value)
        delay = {29: 16, 30: 105, 31: 20}.get(i, 0)
        expected.append('{%d,%d,%d,{%s}}' %
                        (0x39 if i < 30 else 5, len(data), delay,
                         ','.join(str(b) for b in data)))
    path = Path(source) / 'drivers/gpu/drm/panel/panel-novatek-nt36536.c'
    panel = path.read_text()
    start = panel.index('static void y900_dcs_long_write_multi(')
    end = panel.index('static int y900_boe_nt36536e_exit_seq(', start)
    actual = panel[start:end]
    harness = r'''
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
typedef uint8_t u8;
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
#define MIPI_DSI_DCS_LONG_WRITE 0x39
#define MIPI_DSI_MODE_LPM 1
#define MIPI_DSI_MSG_USE_LPM 2
#define dev_err(...) ((void)0)
struct mipi_dsi_msg { unsigned channel, type, flags; const void *tx_buf; size_t tx_len; };
struct mipi_dsi_host;
struct mipi_dsi_host_ops { ssize_t (*transfer)(struct mipi_dsi_host *, const struct mipi_dsi_msg *); };
struct mipi_dsi_host { const struct mipi_dsi_host_ops *ops; };
struct mipi_dsi_device { unsigned channel, mode_flags; struct mipi_dsi_host *host; int dev; };
struct mipi_dsi_multi_context { struct mipi_dsi_device *dsi; int accum_err; };
struct packet { unsigned type, len, wait_ms; u8 data[32]; };
static const struct packet expected[] = { EXPECTED_PACKETS };
static unsigned count, delays, want_flags, want_channel;
static int fail_at;
static ssize_t transfer(struct mipi_dsi_host *host, const struct mipi_dsi_msg *msg)
{
    (void)host;
    assert(count < ARRAY_SIZE(expected));
    const struct packet *p = &expected[count];
    assert(msg->type == p->type && msg->tx_len == p->len);
    assert(msg->flags == want_flags && msg->channel == want_channel);
    assert(!memcmp(msg->tx_buf, p->data, p->len));
    if ((int)count++ == fail_at) return -EIO;
    /* MSM reports padded DMA length, not necessarily payload length. */
    return msg->tx_len + 8;
}
static void standard(struct mipi_dsi_multi_context *ctx, u8 command)
{
    if (ctx->accum_err) return;
    struct mipi_dsi_msg msg = { .channel=ctx->dsi->channel, .type=5,
        .flags=ctx->dsi->mode_flags ? MIPI_DSI_MSG_USE_LPM : 0,
        .tx_buf=&command, .tx_len=1 };
    ssize_t ret = ctx->dsi->host->ops->transfer(ctx->dsi->host, &msg);
    if (ret < 0) ctx->accum_err = ret;
}
static void mipi_dsi_dcs_exit_sleep_mode_multi(struct mipi_dsi_multi_context *ctx)
{ standard(ctx, 0x11); }
static void mipi_dsi_dcs_set_display_on_multi(struct mipi_dsi_multi_context *ctx)
{ standard(ctx, 0x29); }
static void mipi_dsi_msleep(struct mipi_dsi_multi_context *ctx, unsigned ms)
{
    if (ctx->accum_err) return;
    assert(count && ms == expected[count-1].wait_ms);
    delays += ms;
}
ACTUAL_SOURCE
int main(void)
{
    const struct mipi_dsi_host_ops ops = { .transfer=transfer };
    struct mipi_dsi_host host = { .ops=&ops };
    struct mipi_dsi_device dsi = { .host=&host };
    struct mipi_dsi_multi_context ctx = { .dsi=&dsi };
    for (unsigned lp=0; lp<2; lp++) {
        dsi.mode_flags = lp ? MIPI_DSI_MODE_LPM : 0;
        want_flags = lp ? MIPI_DSI_MSG_USE_LPM : 0;
        dsi.channel = want_channel = lp ? 0 : 2;
        for (fail_at=-1; fail_at<32; fail_at++) {
            count=delays=0; ctx.accum_err=0;
            int ret=y900_boe_nt36536e_init_seq(&ctx);
            assert(ret == (fail_at < 0 ? 0 : -EIO));
            assert(count == (fail_at < 0 ? 32u : (unsigned)fail_at+1));
            unsigned expected_delay=0;
            for (unsigned i=0; i<(fail_at < 0 ? 32u : (unsigned)fail_at); i++)
                expected_delay += expected[i].wait_ms;
            assert(delays == expected_delay);
        }
    }
    count=delays=0; ctx.accum_err=-EIO;
    assert(y900_boe_nt36536e_init_seq(&ctx) == -EIO && !count && !delays);
    ctx.accum_err=0; host.ops=NULL;
    assert(y900_boe_nt36536e_init_seq(&ctx) == -EOPNOTSUPP && !count && !delays);
    const struct mipi_dsi_host_ops empty_ops = {0};
    ctx.accum_err=0; host.ops=&empty_ops;
    assert(y900_boe_nt36536e_init_seq(&ctx) == -EOPNOTSUPP && !count && !delays);
    puts("DVT2 packets: 32 exact packets, LP/HS/channel, 64 failures and three early exits passed");
}
'''.replace('EXPECTED_PACKETS', ',\n'.join(expected)).replace('ACTUAL_SOURCE', actual)
    with tempfile.TemporaryDirectory(prefix='tb522fu-panel-check-') as directory:
        c = Path(directory) / 'check.c'
        binary = Path(directory) / 'check'
        c.write_text(harness)
        subprocess.run(['cc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', str(c), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)


def check_panel_power(source):
    """Exercise actual panel power callbacks, including partial-enable unwind."""
    panel = (Path(source) / 'drivers/gpu/drm/panel/panel-novatek-nt36536.c').read_text()
    assert panel.count('.test_keep_power = true') == 1
    desc = panel[panel.index('static const struct panel_desc y900_boe_nt36536e_desc'):]
    assert '.test_keep_power = true' in desc.split('};', 1)[0]
    probe = panel[panel.index('static int novatek_probe('):]
    assert (probe.index('devm_regulator_bulk_get(') <
            probe.index('devm_add_action_or_reset(dev, novatek_release_retained_power, ctx)') <
            probe.index('devm_drm_panel_add('))
    assert 'if (ctx->reset_gpio)\n\t\t\treturn dev_err_probe(dev, -EINVAL,' in probe

    def function(name):
        start = re.search(r'static (?:int|void) ' + name + r'\(', panel).start()
        opening = panel.index('{', start)
        depth = 1
        end = opening + 1
        while depth:
            depth += (panel[end] == '{') - (panel[end] == '}')
            end += 1
        return panel[start:end]

    actual = '\n'.join(function(name) for name in (
        'novatek_reset', 'novatek_release_retained_power',
        'novatek_prepare', 'novatek_unprepare'))
    harness = r'''
#include <assert.h>
#include <errno.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#define y900_dev_info(...) ((void)0)
#define dev_info(...) ((void)0)
#define dev_dbg(...) ((void)0)
#define dev_err(...) ((void)0)
struct regulator { int id, refs; };
struct regulator_bulk_data { struct regulator *consumer; };
struct drm_panel { void *dev; bool prepared; };
struct panel_desc {
    const unsigned int *supply_on_delays_us;
    unsigned int post_on_delay_us;
    bool test_keep_power;
};
struct novatek {
    struct drm_panel panel;
    const struct panel_desc *desc;
    void *reset_gpio;
    struct regulator_bulk_data *supplies;
    unsigned int num_supplies;
    bool power_retained;
};
struct action { int kind, value; };
static struct action trace[512];
static unsigned trace_count, enables, disables, resets, delay_count;
static int enable_fail = -1, disable_fail = -1;
static void record(int kind, int value)
{
    assert(trace_count < 512);
    trace[trace_count++] = (struct action){kind, value};
}
static struct novatek *to_novatek(struct drm_panel *panel)
{ return (struct novatek *)panel; }
static int regulator_enable(struct regulator *r)
{
    record('e', r->id);
    if (r->id == enable_fail) return -EIO;
    r->refs++; enables++;
    return 0;
}
static int regulator_disable(struct regulator *r)
{
    record('d', r->id);
    if (r->id == disable_fail) return -EIO;
    assert(r->refs > 0);
    r->refs--; disables++;
    return 0;
}
static int regulator_bulk_enable(int n, struct regulator_bulk_data *s)
{
    int i;
    for (i = 0; i < n; i++)
        if (regulator_enable(s[i].consumer)) {
            while (i--) assert(!regulator_disable(s[i].consumer));
            return -EIO;
        }
    return 0;
}
static int regulator_bulk_disable(int n, struct regulator_bulk_data *s)
{
    int i;
    for (i = n - 1; i >= 0; i--)
        if (regulator_disable(s[i].consumer)) {
            /* Match regulator core rollback after a failed bulk disable. */
            for (++i; i < n; i++) assert(!regulator_enable(s[i].consumer));
            return -EIO;
        }
    return 0;
}
static void usleep_range(unsigned min, unsigned max)
{ assert(max > min); delay_count++; record('s', min); }
static void gpiod_set_value_cansleep(void *gpio, int value)
{ assert(gpio); resets++; record('g', value); }
ACTUAL_CALLBACKS
static void refs(struct regulator *r, int want)
{ for (int i = 0; i < 3; i++) assert(r[i].refs == want); }
int main(void)
{
    unsigned cases = 0;
    static const unsigned delays[] = {20000, 0, 20000};
    for (int retain = 0; retain < 2; retain++)
    for (int ordered = 0; ordered < 2; ordered++)
    for (int fail = -1; fail < 3; fail++) {
        struct regulator r[] = {{0,0}, {1,0}, {2,0}};
        struct regulator_bulk_data s[] = {{r}, {r+1}, {r+2}};
        struct panel_desc d = {ordered ? delays : NULL, 7000, retain};
        struct novatek ctx = {.desc=&d, .supplies=s, .num_supplies=3,
                              .reset_gpio=retain ? NULL : &d};
        trace_count=enables=disables=resets=delay_count=0;
        enable_fail=fail; disable_fail=-1;
        novatek_release_retained_power(&ctx);
        assert(trace_count == 0);
        if (fail >= 0) {
            assert(novatek_prepare(&ctx.panel) == -EIO);
            refs(r,0); assert(!ctx.power_retained && !resets);
            assert(enables == (unsigned)fail && disables == enables);
            unsigned failed_trace = trace_count;
            novatek_release_retained_power(&ctx);
            assert(trace_count == failed_trace);
        }
        enable_fail=-1;
        trace_count=enables=disables=resets=delay_count=0;
        for (int cycle = 0; cycle < 3; cycle++) {
            unsigned before = trace_count;
            assert(!novatek_prepare(&ctx.panel)); refs(r,1);
            if (retain && cycle)
                for (unsigned i = before; i < trace_count; i++)
                    assert(trace[i].kind == 's');
            assert(!novatek_unprepare(&ctx.panel)); refs(r,retain);
            assert(ctx.power_retained == !!retain);
        }
        assert(enables == (retain ? 3u : 9u));
        assert(disables == (retain ? 0u : 9u));
        assert(resets == (retain ? 0u : 15u));
        assert(delay_count == (unsigned)(3 *
                                      (1 + (ordered ? 2 : 0) + (retain ? 0 : 4))));
        /* The first ordered acquisition must preserve its supply/delay order. */
        if (ordered) {
            static const struct action expected[] = {
                {'e',0}, {'s',20000}, {'e',1}, {'e',2}, {'s',20000}, {'s',7000}};
            assert(!memcmp(trace,expected,sizeof(expected)));
        }
        novatek_release_retained_power(&ctx); refs(r,0);
        assert(!ctx.power_retained && enables == disables);
        unsigned final = trace_count;
        novatek_release_retained_power(&ctx);
        assert(trace_count == final);
        cases++;
    }
    for (int fail = 0; fail < 3; fail++) {
        struct regulator r[] = {{0,0}, {1,0}, {2,0}};
        struct regulator_bulk_data s[] = {{r}, {r+1}, {r+2}};
        struct panel_desc d = {delays,0,true};
        struct novatek ctx = {.desc=&d,.supplies=s,.num_supplies=3};
        enable_fail=disable_fail=-1; trace_count=0;
        assert(!novatek_prepare(&ctx.panel));
        disable_fail=fail;
        novatek_release_retained_power(&ctx);
        refs(r,1); assert(ctx.power_retained);
        disable_fail=-1;
        novatek_release_retained_power(&ctx);
        refs(r,0); assert(!ctx.power_retained);
        cases++;
    }
    printf("Panel power: %u lifecycle/error cases passed\n",cases);
    return 0;
}
'''.replace('ACTUAL_CALLBACKS', actual)
    with tempfile.TemporaryDirectory(prefix='tb522fu-panel-power-') as directory:
        c = Path(directory) / 'power.c'
        binary = Path(directory) / 'power'
        c.write_text(harness)
        # The existing kernel callback uses a signed unwind index for an
        # unsigned supply count; match the kernel's sign-compare policy.
        subprocess.run(['cc', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                        '-Wno-sign-compare',
                        str(c), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)


def capture(args):
    return subprocess.check_output([str(x) for x in args], text=True).strip()


def check_native_display_wiring(dtb):
    # Native display coldplugs in disk profiles. Preserve the firmware
    # framebuffer until normal DRM dependency binding completes takeover.
    display = '/soc@0/display-subsystem@ae00000'
    panel = display + '/dsi@ae94000/panel@0'
    touch = '/soc@0/geniqup@ac0000/spi@a90000/touchscreen@0'
    for node in [display, '/soc@0/clock-controller@af00000',
                 '/soc@0/geniqup@8c0000', '/soc@0/geniqup@8c0000/i2c@888000',
                 '/soc@0/geniqup@8c0000/i2c@88c000', '/framebuffer@fc800000']:
        assert capture(['fdtget', '-t', 's', dtb, node, 'status']) == 'okay', node
    assert capture(['fdtget', '-t', 'x', dtb, touch, 'panel']) == capture(
        ['fdtget', '-t', 'x', dtb, panel, 'phandle'])
    for prop, regulator, uv in [('vddio-supply', 'ldo12', '1800000'),
                                ('vci-supply', 'ldo13', '3000000'),
                                ('tvdd-supply', 'ldo4', '1800000')]:
        node = '/soc@0/rsc@16500000/regulators-b/' + regulator
        assert capture(['fdtget', '-t', 'x', dtb, panel, prop]) == capture(
            ['fdtget', '-t', 'x', dtb, node, 'phandle'])
        assert capture(['fdtget', '-t', 'i', dtb, node, 'regulator-min-microvolt']) == uv
        assert capture(['fdtget', '-t', 'i', dtb, node, 'regulator-max-microvolt']) == uv
    assert 'vdd-supply' not in capture(['fdtget', '-p', dtb, panel]).splitlines()
    dma = '/soc@0/dma-controller@800000'
    assert capture(['fdtget', '-t', 's', dtb, dma, 'status']) == 'okay'
    assert capture(['fdtget', '-t', 'x', dtb, dma, 'dma-channel-mask']) == '1e'
    assert capture(['fdtget', '-t', 'x', dtb, dma, 'iommus']).split()[1:] == ['436', '0']
    ref = capture(['fdtget', '-t', 'x', dtb, dma, 'phandle'])
    for address, se in [('888000', 2), ('88c000', 3)]:
        bus = '/soc@0/geniqup@8c0000/i2c@' + address
        assert capture(['fdtget', '-t', 'x', dtb, bus, 'dmas']) == f'{ref} 0 {se} 3 {ref} 1 {se} 3'
    # Stock chip ID and signed-shader reservation; disk GPU providers coldplug.
    gpu = '/soc@0/gpu@3d00000'
    for node in [gpu, '/soc@0/gmu@3d6c000', '/soc@0/clock-controller@3d90000',
                 '/soc@0/clock-controller@3d64000']:
        assert capture(['fdtget', '-t', 's', dtb, node, 'status']) == 'okay'
    assert capture(['fdtget', '-t', 's', dtb, gpu, 'compatible']) == 'qcom,adreno-44050001 qcom,adreno'
    shader = gpu + '/zap-shader'
    memory = '/reserved-memory/gpu-micro-code@9b09a000'
    assert capture(['fdtget', '-t', 's', dtb, shader, 'firmware-name']) == 'qcom/sm8750/lenovo/tb522fu/gen80000_zap.mbn'
    assert capture(['fdtget', '-t', 'x', dtb, shader, 'memory-region']) == capture(['fdtget', '-t', 'x', dtb, memory, 'phandle'])
    assert capture(['fdtget', '-t', 'x', dtb, memory, 'reg']) == '0 9b09a000 0 2000'
