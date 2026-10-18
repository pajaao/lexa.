"""Documentary proposal only. Does not adjudicate or alter approved relations."""
import csv,json
from pathlib import Path
NOTES={
'civil/1070':'A comparação textual com regra dos administradores não contém nome de diploma; afinidade de conteúdo não prova identidade.',
'civil/1243':'A expressão literal “artigos antecedentes” indica posição relativa, mas não nomeia a norma. A outra remissão ao art. 1.242 também é numérica.',
'civil/1328':'A parentética encerra o período e não tem qualificador de diploma ou ponte normativa expressa.',
'civil/1410':'A mesma ocorrência lista 1.390 e 1.399; cada destino tem ID de aresta próprio, mas a ausência de identidade normativa é compartilhada.',
'civil/1489':'O inciso contém número expresso de artigo sem qualificador de norma; a expressão sobre pessoas de direito público não substitui identificação normativa.',
'civil/1649':'O parêntese sucede “quando necessária”; não há antecedente normativo nominal nessa ligação sintática.',
'civil/1935':'O número é expresso, mas a cláusula que o antecede não identifica diploma ou edição.',
'civil/442':'A proximidade numérica entre 441 e o artigo de origem 442 não pode ser usada para provar identidade de diploma.',
'civil/613':'A expressão que precede o parêntese é descrição do objeto regulado, não identificação de norma.',
'civil/65':'A expressão “suas bases” não identifica diploma; não funciona como antecedente normativo inequívoco.',
'civil/927':'“ato ilícito” é expressão material, não nome normativo. O exemplo conhecido não dispensa critério documental aprovado para a parentética.',
'civil/982':'O parêntese não contém nome de lei; existência do número no CC não basta para provar exclusividade de identidade.',
'civil/985':'“na forma da lei” é expressão genérica; a lista 45/1.150 não nomeia qual lei ou edição.',
'cpp/143':'A nota posterior “Redação dada pela Lei nº 11.435, de 2006” é editorial e não deve ser convertida em qualificador do art. 63.',
'cpp/211':'A parentética anterior ao art. 538, § 2º, também não nomeia diploma. O destino 561 possui nota de revogação: contexto histórico a adjudicar, não prova automática de erro.',
'cpp/46':'A expressão “autoridade policial” não identifica norma; a referência permanece apenas numerada na parentética.',
'cpp/571':'O inciso V apresenta remissão numérica; o cabeçalho do documento é metadado de origem, não qualificador literal da remissão.',
'cpp/597':'O art. 393 anterior e a lista 374/378 não nomeiam diploma. A expressão material sobre medidas de segurança não prova identidade normativa.',
'cpp/68':'O art. 32, §§ 1º e 2º, citado antes também não identifica diploma; não é antecedente normativo suficiente para as parentéticas 63/64.',
'cpp/685':'“Parágrafo único” indica posição estrutural da origem, não identifica a norma de destino do art. 762.',
'lep/118':'O inciso II contém “artigo 111” sem qualificação de diploma. Não inferir identidade por regime ou soma de penas.',
'lep/170':'O núcleo “artigo 168” não nomeia norma. Conteúdo sobre multa/remuneração não é evidência normativa suficiente.',
'lep/78':'O núcleo “artigo 26” é expresso; descrição de egressos não pode substituir nome ou qualificação normativa.',
'penal/318':'A descrição de contrabando/descaminho é temática. O art. 334 é numerado, mas o diploma não está literalmente identificado.',
'penal/97':'“inimputável” e “internação” são contexto material; a nota de redação posterior não identifica a norma da parentética.'}
def generate(source,output):
 data=json.loads(Path(source).read_text());rows=[]
 for e in data['edges']:
  if not all(v['syntaxClass']=='parenthetical-article-list' for v in e['evidence']):continue
  for v in e['evidence']:
   p=e['source']['article']['paragraphs'][v['paragraph']];raw=''.join(r['text'] for r in p['runs'])
   # Native artifact offsets are UTF-16, not Python code points.
   encoded=raw.encode('utf-16-le');prefix=encoded[:2*v['span']['start']].decode('utf-16-le');suffix=encoded[2*v['span']['end']:].decode('utf-16-le')
  key=e['source']['codeId']+'/'+e['source']['articleId']
  rows.append(dict(edgeId=e['edgeId'],occurrenceIds=' | '.join(e['occurrenceIds']),source=key,sourceScope=e['source']['scope'],sourceSHA=e['source']['editionSha256'],target=e['target']['codeId']+'/'+e['target']['articleId'],targetScope=e['target']['scope'],targetSHA=e['target']['editionSha256'],paragraph=' | '.join(str(v['paragraph']) for v in e['evidence']),startUTF16=' | '.join(str(v['span']['start']) for v in e['evidence']),endUTF16=' | '.join(str(v['span']['end']) for v in e['evidence']),literal=' | '.join(v['literal'] for v in e['evidence']),prefix=prefix,suffix=suffix,proposedCriterion='P3: identidade não demonstrada literalmente',unequivocalSelfReference='não demonstrada',expressNormativeAntecedent='não demonstrado na ligação sintática da remissão',contradiction='nenhuma demonstrada nos artefatos',originHistoricalState=' | '.join(json.dumps(v['historical'],ensure_ascii=False) for v in e['evidence']),destinationHeader=''.join(r['text'] for r in e['target']['article']['paragraphs'][0]['runs']),transcriptionOrHistoricalContext='destino com nota histórica expressa; confirmar documentalmente' if key=='cpp/211' else 'não demonstrado como evidência necessária de identidade; contexto integral preservado no inventário',thematicEligibility='proibida; não utilizada',individualAssessment=NOTES[key]+' Destino numérico avaliado: '+e['target']['number']+'.',provisionalConclusion='pendente de decisão',pendingDecision='Identidade literal não confirmada por critério humano aprovado. Não promover nem alterar a aresta experimental.',evidenceFile='docs/remissoes/fase-1a-2/arestas.json#'+e['edgeId']))
 assert len(rows)==30 and len({r['edgeId'] for r in rows})==30
 with Path(output).open('w',encoding='utf-8-sig',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 return {'candidata':0,'bloqueada':0,'pendente de decisão':30}
if __name__=='__main__':
 import sys;print(generate(sys.argv[1],sys.argv[2]))
