#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Native display/GPU DT guards retained from the earlier bounded candidate."""
from pathlib import Path
import subprocess
import tempfile

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


def capture(args):
    return subprocess.check_output([str(x) for x in args], text=True).strip()


def check_bonded_dsi_clocks(dtb):
    """Keep both bonded host clocks on PLL0, matching the slave PHY source."""
    display = '/soc@0/display-subsystem@ae00000'
    phy0 = display + '/phy@ae95000'
    phy1 = display + '/phy@ae97000'
    refs = [int(capture(['fdtget', '-t', 'x', dtb, p, 'phandle']), 16)
            for p in (phy0, phy1)]
    assert refs[0] != refs[1]
    for p in (phy0, phy1):
        assert capture(['fdtget', '-t', 'i', dtb, p, '#clock-cells']) == '1'
    names = ('byte byte_intf pixel core iface bus dsi_pll_pixel dsi_pll_byte '
             'esync osc byte_src pixel_src').split()
    for index, address in enumerate(('ae94000', 'ae96000')):
        node = display + '/dsi@' + address
        assert capture(['fdtget', '-t', 's', dtb, node, 'clock-names']).split() == names
        cells = [int(v, 16) for v in capture(['fdtget', '-t', 'x', dtb, node, 'clocks']).split()]
        assert len(cells) == 2 * len(names), 'Unexpected bonded clock specifiers'
        for name, output in (('dsi_pll_pixel', 1), ('dsi_pll_byte', 0)):
            offset = 2 * names.index(name)
            assert cells[offset:offset + 2] == [refs[0], output], (node, name)
        # The second controller still drives its own physical lane block.
        assert capture(['fdtget', '-t', 'x', dtb, node, 'phys']) == format(refs[index], 'x')
        assert 'qcom,dual-dsi-mode' in capture(['fdtget', '-p', dtb, node]).splitlines()


def check_native_display_wiring(dtb):
    check_bonded_dsi_clocks(dtb)
    # Native display coldplugs in disk profiles. Preserve the firmware
    # framebuffer until normal DRM dependency binding completes takeover.
    display = '/soc@0/display-subsystem@ae00000'
    panel = display + '/dsi@ae94000/panel@0'
    touch = '/soc@0/geniqup@ac0000/spi@a90000/touchscreen@0'
    # Diagnostic only: remove this isolation together with patch0213.
    assert capture(['fdtget', '-t', 's', dtb, touch, 'status']) == 'disabled'
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
