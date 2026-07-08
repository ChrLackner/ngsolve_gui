import os
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("NGAPP_DEFAULT_COLORMAP", "matlab:jet")

# Hermetic user settings: ngapp resolves its config dir via
# ``platformdirs.user_config_dir("ngapp")``, which honours ``XDG_CONFIG_HOME``.
# Point it at a throwaway directory so a developer's real
# ``~/.config/ngapp/NGSolve_GUI/config.json`` (discrete colormap, panel widths,
# theme, navcube visibility, ...) cannot bleed into the rendered baselines and
# make local runs diverge from CI.
os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp(prefix="ngsolve_gui_test_cfg_")

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


# ngapp's PlotlyComponent caches the plotly.js load state on the *class*
# (``_state``/``_plotly``/``_waiting``) so the library only loads once per app.
# That cache leaks across tests: each test gets a fresh browser but the same
# Python process, so after the first plot test ``_state`` stays ``"ready"`` and
# ``_plotly`` points at the first (now-closed) browser's ``window.Plotly``. The
# next plot test then skips loading the lib and draws through a dead proxy, so
# ``.js-plotly-plot`` never appears and the screenshot times out. Reset the
# class state before every test so each fresh browser loads plotly afresh.
@pytest.fixture(autouse=True)
def _reset_plotly_state():
    try:
        from ngapp.components.visualization import PlotlyComponent
    except Exception:
        return
    PlotlyComponent._state = "none"
    PlotlyComponent._plotly = None
    PlotlyComponent._waiting = []
