import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from revalidate_previous_associations import evaluate, BASE, RUN, read


class AssociationReview(unittest.TestCase):
    def test_directed_replay_matches_each_retained_occurrence_and_quarantines_original_cp(self):
        result=evaluate()
        self.assertEqual(result,read(RUN/'results.json'))
        self.assertEqual(len(result['quarantined']),426)
        self.assertTrue(all(r['codeId']=='penal' for r in result['quarantined']))
        self.assertEqual({c:sum(r['codeId']==c for r in result['retained']) for c in ['cpp','clt','licitacoes']},
                         {'cpp':139,'clt':1,'licitacoes':2})
        self.assertTrue(all(r['review']=={'status':'pending'} for r in result['retained']+result['quarantined']))
        self.assertEqual(sum(n['differenceRemains'] for n in result['notes']),16)
        resolved={n['id'] for n in result['notes'] if not n['differenceRemains']}
        self.assertEqual(resolved,{'penal-116-batch-pdf-p24-b31','penal-117-previous-7e63bae85225-b1255','penal-117-previous-7e63bae85225-b1257'})

    def test_preview_preserves_all_baseline_records_and_excludes_quarantine(self):
        result=read(RUN/'results.json')
        baseline=read(BASE/'previous-fixture-before.json')
        current=read(ROOT/'tests/fixtures/previous-wordings-html.json')
        self.assertEqual(current,dict(baseline,records=baseline['records']+result['retained']))
        original=read(BASE/'existing.json')
        actual=read(ROOT/'experiments/html-history/existing-records.json')
        actual+=read(ROOT/'tests/fixtures/legislative-history-html.json')['records']+current['records']
        self.assertEqual(actual[:2373],original)
        self.assertFalse({r['id'] for r in result['quarantined']} & {r['id'] for r in current['records']})


if __name__=='__main__':
    unittest.main()
