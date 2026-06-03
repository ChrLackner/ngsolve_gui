import os
from pathlib import Path

import pytest

os.environ.setdefault("NGAPP_DEFAULT_COLORMAP", "matlab:jet")

pytest_plugins = ["ngapp.e2e_webgpu"]

TESTS_DIR = Path(__file__).parent


def pytest_configure(config):
    import ngapp.e2e_webgpu as e2e_webgpu

    e2e_webgpu.configure(
        output_dir=TESTS_DIR / "output",
        baseline_dir=TESTS_DIR / "baselines",
    )


@pytest.fixture
def browser():
    """Fresh browser per test.

    Prevents WebGPU/SwiftShader resource exhaustion and port conflicts
    in Docker environments without a real GPU.
    """
    from playwright.sync_api import sync_playwright
    from ngapp.e2e_webgpu import CHROMIUM_WEBGPU_ARGS

    pw = sync_playwright().start()
    b = pw.chromium.launch(
        channel="chrome",
        headless=False,
        args=["--headless=new"] + CHROMIUM_WEBGPU_ARGS,
    )
    yield b
    b.close()
    pw.stop()
