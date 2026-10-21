"""Exercise the gated release with the normal PWA in CI, without publishing it."""
from pathlib import Path
import json
import os
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
site=ROOT/'test-results/previous-wordings-release/site'
script="import {stagePages} from './scripts/build-pages.mjs'; await stagePages("+json.dumps(str(site))+",{previousWordingsCandidate:true});"
subprocess.run(['node','--input-type=module','-e',script],cwd=ROOT,check=True)
subprocess.run([sys.executable,str(ROOT/'tests/browser/previous_wordings_groups.py'),'--candidate'],cwd=ROOT,check=True)
subprocess.run([sys.executable,str(ROOT/'tests/browser/pwa.py')],cwd=ROOT,
               env={**os.environ,'LEXA_TEST_SITE':str(site)},check=True)
print('Release candidate interface and real PWA passed; publication remains gated.')
