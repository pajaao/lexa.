#!/usr/bin/env python3
"""Run functional browser checks; performance timings are never a CI gate."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
ESSENTIAL = ['interface_review', 'data_loading', 'reading', 'library_search', 'favorites', 'clipboard', 'pwa', 'offline_policy', 'benchmark_contract']
ALL = [*ESSENTIAL, 'structure', 'additional_legislation', 'memory_session', 'partial_update']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=['essential', 'all'], default='essential')
    parser.add_argument('--artifacts', type=Path, default=ROOT/'test-results/browser')
    args = parser.parse_args()
    args.artifacts.mkdir(parents=True, exist_ok=True)
    failed = []
    started = time.time_ns()
    for name in ESSENTIAL if args.suite == 'essential' else ALL:
        print(f'Executando {name}…', flush=True)
        with (args.artifacts/(name+'.log')).open('w') as log:
            try:
                result = subprocess.run([sys.executable, str(ROOT/'tests/browser'/(name+'.py'))],
                    cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=300)
                success = result.returncode == 0
            except subprocess.TimeoutExpired:
                log.write('\nExecução interrompida após 300 s (proteção contra processo travado).\n')
                success = False
        if not success:
            failed.append(name)
            print((args.artifacts/(name+'.log')).read_text(), flush=True)
    # Existing checks already save screenshots here. Never upload stale images.
    for image in Path('/tmp').glob('lexa-*.png'):
        if image.stat().st_mtime_ns >= started:
            shutil.copy2(image, args.artifacts/image.name)
    print(f'{len(ALL if args.suite=="all" else ESSENTIAL)-len(failed)} verificações passaram; {len(failed)} falharam.', flush=True)
    return int(bool(failed))


if __name__ == '__main__':
    sys.exit(main())
