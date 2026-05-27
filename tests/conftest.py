from pathlib import Path

import pytest

pytest_plugins = ["ngapp.e2e_webgpu"]

TESTS_DIR = Path(__file__).parent


def pytest_configure(config):
    import ngapp.e2e_webgpu as e2e_webgpu

    e2e_webgpu.configure(
        output_dir=TESTS_DIR / "output",
        baseline_dir=TESTS_DIR / "baselines",
    )


@pytest.fixture(scope="module")
def _playwright():
    """Override session-scoped playwright to module scope for better GPU isolation."""
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    yield pw
    pw.stop()


@pytest.fixture(scope="module")
def browser(_playwright):
    """Override session-scoped browser to module scope.

    Restarting the browser per test module prevents WebGPU/SwiftShader
    resource exhaustion in Docker environments without a real GPU.
    """
    from ngapp.e2e_webgpu import CHROMIUM_WEBGPU_ARGS

    b = _playwright.chromium.launch(
        channel="chrome",
        headless=False,
        args=["--headless=new"] + CHROMIUM_WEBGPU_ARGS,
    )
    yield b
    b.close()
