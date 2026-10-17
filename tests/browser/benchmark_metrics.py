"""Pure measurement bookkeeping: no browser dependency, tested by unittest."""
from statistics import median
from urllib.parse import urlsplit


def resource_kind(url):
    path = urlsplit(url).path
    if '/data/' in path and path.endswith('.json'):
        return 'legal_json'
    if path.endswith('/') or path.endswith('/index.html'):
        return 'shell'
    return 'other'


class NetworkLedger:
    def __init__(self):
        self.requests = {}
        self.phase = None

    def begin(self):
        self.phase = []
        return self.phase

    def stop(self):
        self.phase = None

    def request(self, event):
        if self.phase is None:
            return
        item = dict(kind=resource_kind(event['request']['url']), cached=False,
                    worker=False, finished=False, failed=False, encoded_bytes=0)
        self.requests[event['requestId']] = item
        self.phase.append(item)

    def cached(self, event):
        if item := self.requests.get(event['requestId']):
            item['cached'] = True

    def response(self, event):
        if item := self.requests.get(event['requestId']):
            response = event['response']
            item['cached'] |= bool(response.get('fromDiskCache') or response.get('fromPrefetchCache'))
            item['worker'] = bool(response.get('fromServiceWorker'))

    def finished(self, event):
        if item := self.requests.get(event['requestId']):
            item['finished'] = True
            item['encoded_bytes'] = event.get('encodedDataLength', 0)

    def failed(self, event):
        if item := self.requests.get(event['requestId']):
            item.update(finished=True, failed=True)


def transfer_summary(items):
    # Cached body bytes are not a new network transfer. Keep raw CDP bytes too.
    network = [item for item in items if not item['cached'] and not item['worker']]
    result = {
        'request_count': len(items),
        'cached_requests': sum(item['cached'] for item in items),
        'failed_requests': sum(item['failed'] for item in items),
        'unfinished_requests': sum(not item['finished'] for item in items),
        'network_bytes': sum(item['encoded_bytes'] for item in network),
        'cdp_reported_bytes': sum(item['encoded_bytes'] for item in items),
    }
    for kind in ['shell', 'legal_json', 'other']:
        result[kind + '_network_bytes'] = sum(item['encoded_bytes'] for item in network if item['kind'] == kind)
    return result


def summarize(samples):
    """Keep unsupported metrics null; never turn an unavailable metric into zero."""
    fields = ['duration_ms', 'next_frame_ms', 'js_heap_after_gc_bytes', 'js_heap_delta_bytes',
              'origin_body_bytes', 'origin_requests']
    result = {'runs': len(samples)}
    for field in fields:
        values = [sample[field] for sample in samples if sample.get(field) is not None]
        result[field + '_median'] = median(values) if values else None
    for field in ['request_count', 'cached_requests', 'failed_requests', 'unfinished_requests',
                  'network_bytes', 'shell_network_bytes', 'legal_json_network_bytes', 'other_network_bytes']:
        values = [sample['transfer'][field] for sample in samples]
        result[field + '_median'] = median(values)
    result['memory_measured_runs'] = sum(sample.get('js_heap_after_gc_bytes') is not None for sample in samples)
    return result
