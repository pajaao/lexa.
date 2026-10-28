"""Build-time documentary index. No network or manual link table."""
import argparse,json
from pathlib import Path
from maintain_amendments import legacy
from amendments_links import generate
ROOT=Path(__file__).resolve().parent.parent
p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=ROOT/'data/amendments/candidate');p.add_argument('--output',type=Path);a=p.parse_args()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
catalog=load(a.directory/'catalog.json');records=[legacy(load(a.directory/x['document'])) for x in catalog['entries']]
module=(ROOT/'data/official/legislation.js').read_text(encoding='utf-8');cf=json.loads(module[module.index('{'):].strip().rstrip(';'))['cf'];mon=load(ROOT/'monitor/official/cf.json')
if cf['source']['sha256']!=mon['semantic_sha256']:raise ValueError('Índice constitucional e snapshot pertencem a edições diferentes')
result=generate(cf,mon,records);result['constitutionSemanticHash']=mon['semantic_sha256']
text=json.dumps(result,ensure_ascii=False,separators=(',',':'))
if a.output:a.output.write_text(text,encoding='utf-8')
else:print(text)
