"""Small toolbar widget that displays live CPU, RAM, and GPU usage with mini bars."""

import subprocess
import threading
import time

from ngapp.components import Div, QLinearProgress


# Cache nvidia-smi availability to avoid repeated failed spawns
_nvidia_smi_available = None


def _get_stats():
    """Gather system stats. Returns dict with available metrics."""
    global _nvidia_smi_available
    stats = {}

    try:
        import psutil
        stats["cpu"] = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        stats["ram_used_gb"] = mem.used / (1024**3)
        stats["ram_total_gb"] = mem.total / (1024**3)
        stats["ram_percent"] = mem.percent
    except ImportError:
        pass

    # Try nvidia-ml-py / pynvml first, fall back to nvidia-smi
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            from pynvml import (nvmlInit, nvmlDeviceGetHandleByIndex,
                                nvmlDeviceGetMemoryInfo, nvmlDeviceGetUtilizationRates)
        nvmlInit()
        handle = nvmlDeviceGetHandleByIndex(0)
        mem_info = nvmlDeviceGetMemoryInfo(handle)
        util = nvmlDeviceGetUtilizationRates(handle)
        stats["gpu_used_gb"] = mem_info.used / (1024**3)
        stats["gpu_total_gb"] = mem_info.total / (1024**3)
        stats["gpu_util"] = util.gpu
    except Exception:
        if _nvidia_smi_available is not False:
            try:
                out = subprocess.check_output(
                    ["nvidia-smi",
                     "--query-gpu=utilization.gpu,memory.used,memory.total",
                     "--format=csv,noheader,nounits"],
                    timeout=2, stderr=subprocess.DEVNULL,
                ).decode().strip()
                parts = [p.strip() for p in out.split(",")]
                if len(parts) == 3:
                    stats["gpu_util"] = int(parts[0])
                    stats["gpu_used_gb"] = float(parts[1]) / 1024
                    stats["gpu_total_gb"] = float(parts[2]) / 1024
                    _nvidia_smi_available = True
            except Exception:
                _nvidia_smi_available = False

    return stats


def _color_for_percent(pct):
    if pct < 50:
        return "teal-4"
    if pct < 80:
        return "amber-5"
    return "red-5"


class _StatBar(Div):
    """A single labeled mini-bar showing one metric."""

    def __init__(self, label, icon_name):
        self._label = Div(
            label,
            ui_style="font-size:11px; font-weight:600; color:#fff; display:inline;",
        )
        self._value = Div(
            "\u2014",
            ui_style="font-size:11px; font-weight:400; color:#fff; display:inline;",
        )
        self._bar = QLinearProgress(
            ui_value=0,
            ui_color="teal-4",
            ui_track_color="rgba(255,255,255,0.15)",
            ui_style="width:100%; height:3px; border-radius:2px;",
            ui_rounded=True,
        )

        header = Div(
            self._label,
            self._value,
            ui_style="display:flex; align-items:baseline; gap:5px;",
        )

        super().__init__(
            header,
            self._bar,
            ui_style="display:flex; flex-direction:column; gap:2px; min-width:80px;",
        )

    def update(self, value_text, fraction, color):
        self._value.ui_children = [value_text]
        self._bar.ui_value = max(0.0, min(1.0, fraction))
        self._bar.ui_color = color


class SystemMonitor(Div):
    """Compact system stats display for the toolbar with mini progress bars."""

    _STYLE = (
        "display: flex; align-items: center; gap: 14px; "
        "padding: 4px 14px; user-select: none; "
        "background: rgba(0,0,0,0.25); border-radius: 8px;"
    )

    def __init__(self, update_interval=0.5):
        self._interval = update_interval
        self._cpu_bar = _StatBar("CPU", "mdi-chip")
        self._ram_bar = _StatBar("RAM", "mdi-memory")
        self._gpu_bar = _StatBar("GPU", "mdi-expansion-card")
        self._vram_bar = _StatBar("VRAM", "mdi-expansion-card-variant")

        super().__init__(
            self._cpu_bar,
            self._ram_bar,
            self._gpu_bar,
            self._vram_bar,
            ui_style=self._STYLE,
        )

        self._running = True
        # Seed psutil cpu measurement
        try:
            import psutil
            psutil.cpu_percent(interval=None)
        except ImportError:
            pass
        threading.Thread(target=self._poll, daemon=True).start()

    def _poll(self):
        while self._running:
            time.sleep(self._interval)
            stats = _get_stats()
            self._refresh(stats)

    def _refresh(self, stats):
        if "cpu" in stats:
            pct = stats["cpu"]
            self._cpu_bar.update(f"{pct:.0f}%", pct / 100, _color_for_percent(pct))

        if "ram_used_gb" in stats:
            pct = stats["ram_percent"]
            used = stats["ram_used_gb"]
            total = stats["ram_total_gb"]
            self._ram_bar.update(
                f"{used:.1f}/{total:.0f}G", pct / 100, _color_for_percent(pct)
            )

        if "gpu_util" in stats:
            pct = stats["gpu_util"]
            self._gpu_bar.update(f"{pct}%", pct / 100, _color_for_percent(pct))
        else:
            self._gpu_bar.update("N/A", 0, "#475569")

        if "gpu_used_gb" in stats:
            used = stats["gpu_used_gb"]
            total = stats["gpu_total_gb"]
            pct = (used / total * 100) if total > 0 else 0
            self._vram_bar.update(
                f"{used:.1f}/{total:.0f}G", pct / 100, _color_for_percent(pct)
            )
        else:
            self._vram_bar.update("N/A", 0, "#475569")

    def stop(self):
        self._running = False
