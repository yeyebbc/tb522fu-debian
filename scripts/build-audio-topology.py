#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Compile and inspect the TB522FU speaker/capture topology without device access."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess

from audio_topology_checks import check_topology, check_module_configs, AR_PARAM_ID_CHMIXER_COEFF

ROOT = Path(__file__).resolve().parents[1]


def run(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'work/audio-topology')
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/audio')
    args = parser.parse_args()
    inputs = ROOT / 'configs/audio'
    spec = json.loads((inputs / 'source.json').read_text())
    if not args.source.exists():
        run(['git', 'init', args.source])
        run(['git', '-C', args.source, 'remote', 'add', 'origin', spec['upstream_repository']])
        run(['git', '-C', args.source, 'fetch', '--depth=1', 'origin', spec['upstream_commit']])
        run(['git', '-C', args.source, 'checkout', '--detach', 'FETCH_HEAD'])
    identity = subprocess.check_output(['git', '-C', str(args.source), 'rev-parse', 'HEAD'], text=True).strip()
    assert identity == spec['upstream_commit']
    assert not subprocess.check_output(['git', '-C', str(args.source), 'status', '--porcelain'], text=True).strip()
    args.output.mkdir(parents=True, exist_ok=True)
    assert not (args.output / 'manifest.json').exists(), 'Preserve the previous audited output'
    config = args.output / 'TB522FU.conf'
    with config.open('wb') as stream:
        run(['m4', '-I', inputs, '-I', args.source, inputs / 'TB522FU.m4'], stdout=stream)
    check_topology(config.read_text(), spec['kernel_dai_widgets'])
    assert spec['firmware_name'] == f"qcom/{spec['driver']}/{spec['model']}-tplg.bin"
    topology = args.output / Path(spec['firmware_name']).name
    run(['alsatplg', '-c', config, '-o', topology])
    mixing = check_module_configs(topology.read_bytes())
    assert list(mixing) == ['device40.mfc1']
    tables = mixing['device40.mfc1'][AR_PARAM_ID_CHMIXER_COEFF]
    assert len(tables) == 1 and tables[0][2] == [(16384, 0), (0, 16384)] * 4
    module_spec = importlib.util.spec_from_file_location('graph_check', ROOT / 'scripts/check-audioreach-tplg.py')
    graph_check = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(graph_check)
    decoded = graph_check.decode(topology)
    (args.output / 'decoded.conf').write_text(decoded)
    modules = graph_check.modules_binary(topology.read_bytes())
    graph = graph_check.check(modules)
    assert graph['verdict'] == 'PASS' and graph['modules'] == 14, graph
    # No positive DSP gain control in the stream graph.
    assert all(m['mid'] != 0x0700101b for m in modules.values())
    (args.output / 'checks.json').write_text(json.dumps({'graph': graph, 'mixing': mixing}, indent=2) + '\n')
    shutil.copy2(inputs / 'source.json', args.output / 'source.json')
    run(['tar', '-czf', args.output / 'ucm.tar.gz', '-C', ROOT / 'device',
         'usr/share/alsa/ucm2'])
    recipe = subprocess.check_output(['git', '-c', f'safe.directory={ROOT}', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    files = {p.name: {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
             for p in args.output.iterdir() if p.is_file()}
    (args.output / 'manifest.json').write_text(json.dumps({'recipe_commit': recipe, 'source': spec,
        'hardware_tested': False, 'files': files}, indent=2) + '\n')
    print('Audio topology compiled: fourteen modules, playback/capture routes, unity stereo duplication; hardware untested.')


if __name__ == '__main__':
    main()
