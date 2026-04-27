from pathlib import Path

pytest_plugins = ["ngapp.e2e_webgpu"]

TESTS_DIR = Path(__file__).parent


def pytest_configure(config):
    import ngapp.e2e_webgpu as e2e_webgpu

    e2e_webgpu.configure(
        output_dir=TESTS_DIR / "output",
        baseline_dir=TESTS_DIR / "baselines",
    )