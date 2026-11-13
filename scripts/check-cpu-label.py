#!/usr/bin/env python3
"""Compare GNOME's libgtop model names with util-linux's CPU decoder."""
import csv
import json
import os
import subprocess
import sys

env = dict(os.environ, LC_ALL='C')
raw = subprocess.check_output(['lscpu', '--parse=cpu,MODELNAME'], text=True, env=env)
expected = {int(row[0]): row[1] for row in csv.reader(
    line for line in raw.splitlines() if line and not line.startswith('#'))}
actual_text = subprocess.check_output([sys.argv[1]], text=True, env=env)
actual = {int(line.split('\t', 1)[0]): line.split('\t', 1)[1]
          for line in actual_text.splitlines()}
assert actual and actual == expected, {'actual': actual, 'lscpu': expected}
assert all(value and value not in ('-', 'unknown') for value in actual.values())
print(json.dumps({'passed': True, 'cpus': actual, 'reference': 'lscpu --parse=cpu,MODELNAME'}, indent=2))
