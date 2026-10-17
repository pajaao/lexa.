"""Measurement bookkeeping must not require Playwright in the monitor jobs."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('benchmark_metrics', Path(__file__).resolve().parents[1]/'browser/benchmark_metrics.py')
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)


class BenchmarkMetricsTests(unittest.TestCase):
    def test_transfer_separates_shell_json_and_cached_responses(self):
        ledger = metrics.NetworkLedger();items = ledger.begin()
        for id_, url, size in [('html','http://localhost/lexa./',200),('norm','http://localhost/lexa./data/clt.hash.json',500),('cached','http://localhost/lexa./data/civil.hash.json',900)]:
            ledger.request({'requestId':id_,'request':{'url':url}})
            ledger.finished({'requestId':id_,'encodedDataLength':size})
        ledger.cached({'requestId':'cached'})
        ledger.stop()
        ledger.request({'requestId':'outside','request':{'url':'http://localhost/after'}})
        result=metrics.transfer_summary(items)
        self.assertEqual(result['network_bytes'],700)
        self.assertEqual(result['legal_json_network_bytes'],500)
        self.assertEqual(result['shell_network_bytes'],200)
        self.assertEqual(result['cached_requests'],1)
        self.assertEqual(result['request_count'],3)
        self.assertEqual(result['cdp_reported_bytes'],1600)

    def test_late_completion_stays_in_the_original_phase(self):
        ledger=metrics.NetworkLedger();first=ledger.begin()
        ledger.request({'requestId':'old','request':{'url':'http://localhost/data/cf.hash.json'}})
        ledger.stop();second=ledger.begin()
        ledger.finished({'requestId':'old','encodedDataLength':300})
        self.assertEqual(metrics.transfer_summary(first)['network_bytes'],300)
        self.assertEqual(metrics.transfer_summary(second)['request_count'],0)

    def test_failed_request_and_unavailable_memory_are_explicit(self):
        ledger=metrics.NetworkLedger();items=ledger.begin()
        ledger.request({'requestId':'x','request':{'url':'http://localhost/data/x.json'}})
        ledger.failed({'requestId':'x'})
        sample={'duration_ms':10,'next_frame_ms':20,'js_heap_after_gc_bytes':None,'transfer':metrics.transfer_summary(items)}
        result=metrics.summarize([sample,{**sample,'duration_ms':30}])
        self.assertEqual(result['duration_ms_median'],20)
        self.assertIsNone(result['js_heap_after_gc_bytes_median'])
        self.assertEqual(result['memory_measured_runs'],0)
        self.assertEqual(result['failed_requests_median'],1)

    def test_worker_response_is_not_counted_as_page_network_transfer(self):
        ledger=metrics.NetworkLedger();items=ledger.begin()
        ledger.request({'requestId':'x','request':{'url':'http://localhost/data/x.json'}})
        ledger.response({'requestId':'x','response':{'fromServiceWorker':True}})
        ledger.finished({'requestId':'x','encodedDataLength':1000})
        self.assertEqual(metrics.transfer_summary(items)['network_bytes'],0)
