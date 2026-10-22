import {normalize} from './collection-model.js';
import {sectionPath,headingKind} from './structure.js';

export const escape = s => String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

export const number = n => n.toLocaleString('pt-BR');

export const codeHref = (code,article='') => `#/${encodeURIComponent(code.id)}${article?'/'+article:''}`;

export function feedbackHref(code,article) {
 const form=new URL('https://docs.google.com/forms/d/e/1FAIpQLSfV7zTS0Fb8I6L5RK9zSkBVNe1FsmvLitU2wJjvvp_V3mFKyA/viewform');
 form.searchParams.set('usp','pp_url');
 form.searchParams.set('entry.1354902092','https://pajaao.github.io/lexa./'+codeHref(code,article));
 return form.href;
}

export const collectionDate = source => new Intl.DateTimeFormat('pt-BR',{timeZone:'America/Sao_Paulo',dateStyle:'short'}).format(new Date(source.capturedAt));

export function sourcePanel(source) {
 if(['official_html','official_stf'].includes(source.kind))return `<p>${escape(source.coverage)}</p><p>${escape(source.reviewStatus)}</p><p>Coleta da fonte oficial: ${collectionDate(source)}. Novas versões são propostas para revisão no GitHub.</p><p><a href="${escape(source.url)}" target="_blank" rel="noopener noreferrer">Consultar página oficial ↗</a></p><p class="source-hash">SHA-256 do texto extraído: ${escape(source.sha256)}</p>`;
 return `<p>${escape(source.coverage)}</p><p>${escape(source.reviewStatus)}</p><p>Arquivo: ${escape(source.filename)} · ${escape(source.pages)} páginas.</p><p><a href="./${escape(source.pdf)}" target="_blank" rel="noopener">Abrir PDF fornecido ↗</a> <small>(disponível ao executar o site completo)</small></p><p class="source-hash">SHA-256: ${escape(source.sha256)}</p>`;
}

export function highlight(text, query) {
 const q=normalize(query.trim());
 if(!q || !/[a-z]/.test(q) || /^(?:adct\s*)?art\.?\s*\d/.test(q))return escape(text);
 const chars=Array.from(text), positions=[];
 let normalized='';
 chars.forEach((c,index)=>{const part=normalize(c);for(let i=0;i<part.length;i++)positions.push(index);normalized+=part;});
 let html='',cursor=0,search=0,found;
 while((found=normalized.indexOf(q,search))>=0){
  const start=positions[found],end=positions[found+q.length-1]+1;
  html+=escape(chars.slice(cursor,start).join(''))+'<mark>'+escape(chars.slice(start,end).join(''))+'</mark>';
  cursor=end;search=found+q.length;
 }
 return html+escape(chars.slice(cursor).join(''));
}


export function diffColumn(tokens, side) {
 if(!tokens.length)return '<p class="comparison-empty">Não constava nesta versão.</p>';
 let html='',paragraph=-1;
 for(const token of tokens){
  if(token.paragraph!==paragraph){if(paragraph>=0)html+='</p>';html+='<p>';paragraph=token.paragraph;}
  let text=escape(token.text);
  if(token.deleted)text=`<del title="Riscado na fonte original">${text}</del>`;
  if(token.changed)text=`<mark class="diff-${side}">${text}</mark>`;
  html+=text;
 }
 return html+'</p>';
}


export function sectionHeadings(section,previous){
  const path=sectionPath(section),before=previous?sectionPath(previous):[];
  let shared=0;while(shared<path.length&&path[shared]===before[shared])shared++;
  return `<div class="legal-divisions">${path.slice(shared).map((text,offset)=>{
   const depth=shared+offset,level=Math.min(6,depth+2),[label,...description]=text.split(' — ');
   return `<h${level} class="legal-heading legal-${headingKind(text)}"><span>${escape(label)}</span>${description.length?`<strong>${escape(description.join(' — '))}</strong>`:''}</h${level}>`;
  }).join('')}</div>`;
 }
