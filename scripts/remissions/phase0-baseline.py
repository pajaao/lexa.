"""Optional historical comparison only; no Python dependency in the Node extractor.
Reads the exact frozen Fase0 experimental code. Never writes legal data.
Usage: python scripts/remissions/phase0-baseline.py CORPUS_JSON OUTPUT_JSON
"""
import importlib.util,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('phase0',root/'tests/fixtures/remissions/phase0-poc.py')
poc=importlib.util.module_from_spec(spec);spec.loader.exec_module(poc)
corpus=json.loads(Path(sys.argv[1]).read_text())
rows=poc.extract(corpus)
output={'occurrences':rows,'examinedArticles':sum(len(c['code']['articles']) for c in corpus['collections'] if c['code']['id']!='sv'),'classifications':{status:sum(r['status']==status for r in rows) for status in 'ABCD'},'uniqueConnections':len(poc.graph(rows)['edges'])}
Path(sys.argv[2]).write_text(json.dumps(output,ensure_ascii=False,separators=(',',':')))
