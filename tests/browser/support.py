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
