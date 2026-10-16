import {articleLabel} from './data.js';

export function articleCopyText(code,article,permalink){
 const hasDeleted=article.paragraphs.some(p=>p.runs.some(run=>run.deleted));
 const paragraphs=article.paragraphs.map(p=>p.runs.map(run=>run.deleted?`[Trecho riscado na fonte: ${run.text}]`:run.text).join(''));
 const status={cancelled:'Cancelada',pending:'Pendente de publicação',suspended:'Suspensa'}[article.status];
 const source=code.source;
 const lines=[`${code.name} — ${articleLabel(article)}`,code.law,''];
 if(status)lines.push(`Situação indicada na edição: ${status}.`,'');
 if(article.title)lines.push(article.title,'');
 lines.push(paragraphs.join('\n\n'),'');
 if(hasDeleted)lines.push('Os trechos identificados como riscados estão preservados conforme a fonte consultada.','');
 lines.push(`Edição consultada no Lexa: ${source.edition}`);
 if(source.filename)lines.push(`Documento fornecido: ${source.filename}${article.page?' · página '+article.page+(article.endPage&&article.endPage!==article.page?' a '+article.endPage:''):''}`);
 lines.push(`Fonte oficial para conferência: ${article.url||source.url||code.url}`,`Consultar no Lexa: ${permalink}`);
 return lines.join('\n');
}
