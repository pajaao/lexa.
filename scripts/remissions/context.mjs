// Conservative lexical reproduction guard, not an attribution of the quoted law.
const instruction=/(?:passa(?:m)?\s+a\s+vigorar|seguinte\s+reda[çc][aã]o|acrescent(?:e|a)-se|ficam?\s+acrescid[oa]s?|trecho\s+reproduzido\s+de\s+(?:um\s+)?diploma)/iu;
export function reproductionContext(article){
 // Preserve the article-wide exclusion of 1A; remove only its two-paragraph
 // cutoff. Do not guess the start/end of a transcription or authorize its
 // introductory references without a separately tested attribution grammar.
 return article.paragraphs.some(p=>instruction.test(p.runs.map(r=>r.text).join('')));
}
