"""Use the same Chromium selection locally and in CI, without a fixed OS path."""
import os
import shutil
from pathlib import Path
from playwright.sync_api import expect

expect.set_options(timeout=15_000)


def chromium_executable():
    explicit = os.environ.get('LEXA_CHROMIUM')
    if explicit:
        if not Path(explicit).is_file():
            raise RuntimeError('LEXA_CHROMIUM deve apontar para um executável existente.')
        return explicit
    # None asks Playwright to use its version-matched downloaded Chromium.
    return shutil.which('chromium') or shutil.which('chromium-browser')


def app_evaluate(page, expression, argument=None):
    """Inspect ES-module exports from tests, without a production debug global.
    The fallback keeps old inline baselines measurable by the same harness.
    """
    import json
    if not page.locator('script[type="module"][src]').count():
        return page.evaluate(expression, argument)
    return page.evaluate('''async argument=>{
        const base=new URL(document.querySelector('script[type="module"][src]').src);
        const {collections}=await import(new URL('data.js',base).href);
        const {searchLibraryText}=await import(new URL('library-search.js',base).href);
        const result=eval(''' + json.dumps(expression) + ''');
        return typeof result==='function'?result(argument):result;
    }''', argument)
