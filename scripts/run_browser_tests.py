#!/usr/bin/env python3
"""Run functional browser checks; performance timings are never a CI gate."""
import argparse
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ESSENTIAL = ['interface_review', 'data_loading', 'reading', 'reader_editorial', 'reader_navigation', 'library_search', 'home_refinements', 'home_search_layout', 'home_geometry', 'home_issue46', 'favorites', 'clipboard', 'pwa', 'pwa_update_check', 'offline_policy', 'benchmark_contract', 'ux_lote1', 'mobile_settings', 'mobile_index', 'mobile_search']
ESSENTIAL.extend(['legislative_history','simple_previous_wordings','previous_wordings_groups','previous_release','feedback'])
ALL = [*ESSENTIAL, 'structure', 'additional_legislation', 'memory_session', 'partial_update', 'recent_updates_pwa']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=['essential', 'all'], default='essential')
    parser.add_argument('--artifacts', type=Path, default=ROOT/'test-results/browser')
    args = parser.parse_args()
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    args.artifacts = args.artifacts.resolve()
    args.artifacts.mkdir(parents=True, exist_ok=True)
    failed = []
    environment = {**os.environ, 'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8',
                   'LEXA_TEST_ARTIFACTS': str(args.artifacts)}
    for name in ESSENTIAL if args.suite == 'essential' else ALL:
        print(f'Executando {name}…', flush=True)
        with (args.artifacts/(name+'.log')).open('w', encoding='utf-8') as log:
            try:
                result = subprocess.run([sys.executable, str(ROOT/'tests/browser'/(name+'.py'))],
                    cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT, timeout=300)
                success = result.returncode == 0
            except subprocess.TimeoutExpired:
                log.write('\nExecução interrompida após 300 s (proteção contra processo travado).\n')
                success = False
        if not success:
            failed.append(name)
            print((args.artifacts/(name+'.log')).read_text(encoding='utf-8'), flush=True)
    print(f'{len(ALL if args.suite=="all" else ESSENTIAL)-len(failed)} verificações passaram; {len(failed)} falharam.', flush=True)
    return int(bool(failed))


if __name__ == '__main__':
    sys.exit(main())
