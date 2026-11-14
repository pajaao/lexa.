"""Inspect ordinary public navigation; never use its output as a legal capture."""
import json
import os
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from check_official_sources import ROOT, parse_html, validate
from official_http import MAX_BYTES

spec = json.loads((ROOT/'monitor/sources.json').read_text(encoding='utf-8'))[0]
with sync_playwright() as p:
    options = {'headless': True}
    if os.environ.get('LEXA_CHROMIUM'):
        options['executable_path'] = os.environ['LEXA_CHROMIUM']
    browser = p.chromium.launch(**options)
    try:
        page = browser.new_page(java_script_enabled=False, service_workers='block')
        page.route('**/*', lambda route: route.continue_() if route.request.resource_type == 'document' else route.abort())
        try:
            response = page.goto(spec['url'], wait_until='domcontentloaded', timeout=25000)
            destination = urlsplit(response.url)
            result = {'client': 'ordinary-browser', 'status': response.status,
                      'final_origin': destination.scheme+'://'+str(destination.hostname),
                      'final_path': destination.path, 'exact_source_url': response.url == spec['url']}
            if result['exact_source_url'] and response.status == 200:
                length = int(response.headers.get('content-length', '0'))
                if length > MAX_BYTES:
                    result['error'] = 'size_limit'
                else:
                    raw = response.body()
                    if len(raw) > MAX_BYTES:
                        result['error'] = 'size_limit'
                    else:
                        result['articles'] = validate(parse_html(raw), spec)
                        result['valid_document'] = True
            print(json.dumps(result), flush=True)
        except Exception as error:
            print(json.dumps({'client': 'ordinary-browser', 'error_type': type(error).__name__}), flush=True)
    finally:
        browser.close()
