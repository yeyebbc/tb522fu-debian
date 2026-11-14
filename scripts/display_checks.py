#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Native display/GPU DT guards retained from the earlier bounded candidate."""
from pathlib import Path
import subprocess

DISPLAY_MODULES = {'msm', 'dispcc_sm8750', 'ktz8866', 'panel_novatek_nt36536',
                   'gpucc_sm8750', 'gxclkctl_kaanapali'}


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
