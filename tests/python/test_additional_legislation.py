import json
from pathlib import Path
import unittest
from check_official_sources import parse_html
from import_official import ROOT,convert,load_js

class AdditionalLegislationTests(unittest.TestCase):
 def test_utf16_official_html_with_ascii_padding(self):
  html='<html><body><p>Art. 1º Proteção à mulher.</p></body></html>'
  raw=html.encode('utf-16')+b' '*37
  doc=parse_html(raw,'windows-1252')
  self.assertEqual(''.join(r['text'] for r in doc['blocks'][0]),'Art. 1º Proteção à mulher.')
  self.assertEqual(len(doc['blocks']),1)
  with self.assertRaises(ValueError):parse_html(html.encode('utf-16')[:-5])

 def test_cpp_repeated_jury_articles_remain_distinct_from_each_other(self):
  data=load_js(ROOT/'data/official/legislation.js','officialImported')['cpp']
  archived=load_js(ROOT/'data/archive/legislation.js','imported')['cpp']
  for collection in [data,archived]:
   article=next(a for a in collection['articles'] if a['id']=='406')
   text='\n'.join(''.join(r['text'] for r in p['runs']) for p in article['paragraphs'])
   self.assertIn('O juiz, ao receber a denúncia',text)
   self.assertTrue(any(r['deleted'] for p in article['paragraphs'] for r in p['runs']))
   last=next(a for a in collection['articles'] if a['id']=='497')
   self.assertNotIn('Art. 406.', '\n'.join(''.join(r['text'] for r in p['runs']) for p in last['paragraphs']))
   self.assertEqual(len(collection['articles']),len({a['id'] for a in collection['articles']}))

 def test_licitacoes_penal_amendments_are_inside_article_178(self):
  data=load_js(ROOT/'data/official/legislation.js','officialImported')['licitacoes']
  self.assertFalse(any(a['number'].startswith('337') for a in data['articles']))
  article=next(a for a in data['articles'] if a['id']=='178')
  text='\n'.join(''.join(r['text'] for r in p['runs']) for p in article['paragraphs'])
  self.assertIn('337-E',text)
  self.assertIn('337-P',text)
  article=next(a for a in data['articles'] if a['id']=='182')
  self.assertIn('IPCA-E',''.join(r['text'] for p in article['paragraphs'] for r in p['runs']))

 def test_new_sources_and_all_base_articles(self):
  finals={'cpp':811,'eca':267,'lep':204,'maria-penha':46,'improbidade':25,'licitacoes':194}
  for location,export in [('data/archive/legislation.js','imported'),('data/official/legislation.js','officialImported')]:
   data=load_js(ROOT/location,export)
   for id,last in finals.items():
    with self.subTest(location=location,code=id):
     ids={a['id'] for a in data[id]['articles']}
     self.assertTrue({str(n) for n in range(1,last+1)}<=ids)
     self.assertTrue(data[id]['sections'])
