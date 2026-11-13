#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build-time guards for the first TB522FU camera candidate, not acceptance."""
from pathlib import Path
import re
import subprocess

CAMERA_MODULES = {
    'camcc_sm8750', 'cambistmclkcc_sm8750', 'i2c_qcom_cci',
    'phy_qcom_mipi_csi2', 'qcom_camss', 'ov02b10',
}


def read(dtb, node, prop, kind='x'):
    output = subprocess.check_output(['fdtget', '-t' + kind, str(dtb), node, prop], text=True)
    return list(map(lambda x: int(x, 16), output.split())) if kind == 'x' else output.split()


def phandle(dtb, node):
    value = read(dtb, node, 'phandle')
    assert len(value) == 1
    return value[0]


def check_camera_wiring(dtb, source):
    sensor = '/soc@0/cci@ac7c000/i2c-bus@0/camera-sensor@3c'
    phy = '/soc@0/phy@adb3000'
    camss = '/soc@0/isp@ad27000'
    supplies = '/soc@0/rsc@16500000/regulators-'
    tlmm = '/soc@0/pinctrl@f100000'
    assert read(dtb, sensor, 'compatible', 's') == ['ovti,ov02b10']
    assert read(dtb, sensor, 'reg') == [0x3c]
    assert read(dtb, sensor, 'clocks') == [phandle(dtb, '/soc@0/clock-controller@1760000'), 6]
    assert read(dtb, sensor, 'assigned-clocks') == read(dtb, sensor, 'clocks')
    assert read(dtb, sensor, 'assigned-clock-rates') == [24000000]
    assert read(dtb, sensor, 'reset-gpios') == [phandle(dtb, tlmm), 109, 1]
    assert read(dtb, sensor, 'orientation') == [1]
    assert read(dtb, sensor, 'rotation') == [90]
    assert read(dtb, sensor, 'avdd-supply') == [phandle(dtb, supplies + 'b/ldo7')]
    assert read(dtb, sensor, 'dovdd-supply') == [phandle(dtb, supplies + 'b/ldo10')]
    assert read(dtb, phy, 'vdda-0p9-supply') == [phandle(dtb, supplies + 'f/ldo1')]
    assert read(dtb, phy, 'vdda-1p2-supply') == [phandle(dtb, supplies + 'g/ldo3')]
    for ldo, voltage in [(7, 2880000), (10, 1800000)]:
        node = supplies + f'b/ldo{ldo}'
        assert read(dtb, node, 'regulator-min-microvolt') == [voltage]
        assert read(dtb, node, 'regulator-max-microvolt') == [voltage]
        text = (Path(source) / 'drivers/regulator/qcom-rpmh-regulator.c').read_text()
        block = text.split('static const struct rpmh_vreg_init_data pm8550_vreg_data[] = {', 1)[1].split('\n};', 1)[0]
        hw = re.search(r'RPMH_VREG\("ldo' + str(ldo) + r'",\s*LDO,\s*\d+,\s*&([^,]+),', block)[1]
        config = text.split('static const struct rpmh_vreg_hw_data ' + hw + ' = {', 1)[1].split('\n};', 1)[0]
        base, first, last, step = map(int, re.search(r'REGULATOR_LINEAR_RANGE\((\d+), (\d+), (\d+), (\d+)\)', config).groups())
        assert any(base + step*(i-first) == voltage for i in range(first, last+1)), (ldo, voltage)
    # RPMh manages the undocumented L7 input dependency; don't guess a parent.
    props = subprocess.check_output(['fdtget', '-p', str(dtb), supplies + 'b'], text=True).split()
    assert 'vdd-l6-l7-supply' not in props
    for i in range(3):
        node = f'/soc@0/cci@{0xac7b000 + i*0x1000:x}'
        assert read(dtb, node, 'status', 's') == ['okay' if i == 1 else 'disabled']
        assert read(dtb, node, 'assigned-clock-rates') == [37500000]
        for j in range(2):
            assert read(dtb, node + f'/i2c-bus@{j}', 'status', 's') == [
                'okay' if (i, j) == (1, 0) else 'disabled']
    for i in range(6):
        node = f'/soc@0/phy@{0xada9000 + i*0x2000:x}'
        assert read(dtb, node, 'status', 's') == ['okay' if i == 5 else 'disabled']
    assert read(dtb, camss, 'status', 's') == ['okay']
    sensor_ep = sensor + '/port/endpoint'
    phy_in = phy + '/ports/port@0/endpoint'
    phy_out = phy + '/ports/port@1/endpoint'
    camss_ep = camss + '/ports/port@5/endpoint'
    for left, right in [(sensor_ep, phy_in), (phy_out, camss_ep)]:
        assert read(dtb, left, 'remote-endpoint') == [phandle(dtb, right)]
        assert read(dtb, right, 'remote-endpoint') == [phandle(dtb, left)]
    for node in [sensor_ep, phy_in, camss_ep]:
        assert read(dtb, node, 'data-lanes') == [1]
        assert read(dtb, node, 'clock-lanes') == [0]
        assert read(dtb, node, 'bus-type') == [4]
    assert read(dtb, sensor_ep, 'link-frequencies') == [0, 330000000]
    assert read(dtb, sensor, 'pinctrl-0') == [
        phandle(dtb, tlmm + '/camera-mclk3-default-state'),
        phandle(dtb, tlmm + '/camera-reset3-default-state')]
    for i, state in enumerate(['default', 'sleep']):
        assert read(dtb, '/soc@0/cci@ac7c000', f'pinctrl-{i}') == [
            phandle(dtb, tlmm + f'/camera-cci1-{state}-state')]
    for name, pin, function in [('sda', 117, 'cci_i2c_sda'), ('scl', 118, 'cci_i2c_scl')]:
        for state, bias in [('default', 'bias-pull-up'), ('sleep', 'bias-disable')]:
            node = tlmm + f'/camera-cci1-{state}-state/{name}-pins'
            assert read(dtb, node, 'pins', 's') == [f'gpio{pin}']
            assert read(dtb, node, 'function', 's') == [function]
            assert read(dtb, node, 'drive-strength') == [2]
            assert bias in subprocess.check_output(['fdtget', '-p', str(dtb), node], text=True).split()
    for suffix, pin, function in [('mclk3', 92, 'cam_mclk'), ('reset3', 109, 'gpio')]:
        node = tlmm + f'/camera-{suffix}-default-state'
        assert read(dtb, node, 'pins', 's') == [f'gpio{pin}']
        assert read(dtb, node, 'function', 's') == [function]
        assert read(dtb, node, 'drive-strength') == [2]


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dtb', type=Path)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    check_camera_wiring(args.dtb, args.source)
    print('Camera slot 2 wiring and voltage selector guards passed; hardware untested.')
