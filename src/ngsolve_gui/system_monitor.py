"""Small toolbar widget that displays live CPU, RAM, and GPU usage with mini bars."""

import os
import subprocess
import threading
import time

from ngapp.components import Div, QLinearProgress

from .cerbsim_style import (
    monitor,
    monitor_label,
    monitor_value,
    monitor_subvalue,
    monitor_stat,
    monitor_stat_header,
    monitor_bar,
    monitor_subbar,
)


# ── Cached constants (set once, never change) ────────────────────────────────
_pid = os.getpid()

# psutil state (populated by _ensure_psutil)
_psutil = None          # module ref
_cpu_count = None
_process = None         # psutil.Process for current pid
_psutil_tried = False

# pynvml state (populated by _ensure_nvml)
_nvml_handle = None
_nvml_tried = False
_nvml_ready = False
_nvml_get_mem_info = None
_nvml_get_util = None
_nvml_get_compute_procs = None
_nvml_get_graphics_procs = None

# nvidia-smi fallback
_nvidia_smi_available = None


def _ensure_psutil():
    """Import psutil once, cache module ref, cpu_count and Process handle."""
    global _psutil, _cpu_count, _process, _psutil_tried
    if _psutil_tried:
        return _psutil is not None
    _psutil_tried = True
    try:
        import psutil
        _psutil = psutil
        _cpu_count = psutil.cpu_count() or 1
        _process = psutil.Process(_pid)
        # Seed both cpu_percent counters so first real read is meaningful
        psutil.cpu_percent(interval=None)
        _process.cpu_percent(interval=None)
        return True
    except ImportError:
        return False


def _ensure_nvml():
    """Initialise pynvml once, cache device handle and function references."""
    global _nvml_tried, _nvml_ready, _nvml_handle
    global _nvml_get_mem_info, _nvml_get_util
    global _nvml_get_compute_procs, _nvml_get_graphics_procs
    if _nvml_tried:
        return _nvml_ready
    _nvml_tried = True
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            import pynvml
        pynvml.nvmlInit()
        _nvml_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        _nvml_get_mem_info = pynvml.nvmlDeviceGetMemoryInfo
        _nvml_get_util = pynvml.nvmlDeviceGetUtilizationRates
        _nvml_ready = True
        # Per-process helpers (may not exist in older pynvml)
        try:
            _nvml_get_compute_procs = pynvml.nvmlDeviceGetComputeRunningProcesses
        except AttributeError:
            pass
        try:
            _nvml_get_graphics_procs = pynvml.nvmlDeviceGetGraphicsRunningProcesses
        except AttributeError:
            pass
    except Exception:
        _nvml_ready = False
    return _nvml_ready


def _get_stats(include_proc_gpu):
    """Gather system and per-process stats.

    *include_proc_gpu* controls whether the (moderately expensive)
    per-process GPU memory query is performed this tick.
    """
    global _nvidia_smi_available
    stats = {}

    # ── CPU & RAM (system + process) ─────────────────────────────────────
    if _ensure_psutil():
        stats["cpu"] = _psutil.cpu_percent(interval=None)
        mem = _psutil.virtual_memory()
        stats["ram_used_gb"] = mem.used / (1024**3)
        stats["ram_total_gb"] = mem.total / (1024**3)
        stats["ram_percent"] = mem.percent

        try:
            stats["proc_cpu"] = _process.cpu_percent(interval=None) / _cpu_count
            rss = _process.memory_info().rss
            stats["proc_ram_gb"] = rss / (1024**3)
        except Exception:
            pass

    # ── GPU (pynvml fast-path) ───────────────────────────────────────────
    if _ensure_nvml():
        try:
            mem_info = _nvml_get_mem_info(_nvml_handle)
            util = _nvml_get_util(_nvml_handle)
            stats["gpu_used_gb"] = mem_info.used / (1024**3)
            stats["gpu_total_gb"] = mem_info.total / (1024**3)
            stats["gpu_util"] = util.gpu
        except Exception:
            pass

        # Per-process VRAM (only on selected ticks)
        if include_proc_gpu:
            try:
                for fn in (_nvml_get_compute_procs, _nvml_get_graphics_procs):
                    if fn is None:
                        continue
                    for p in fn(_nvml_handle):
                        if p.pid == _pid:
                            stats["proc_gpu_mem_gb"] = p.usedGpuMemory / (1024**3)
                            break
                    if "proc_gpu_mem_gb" in stats:
                        break
            except Exception:
                pass
    else:
        # ── nvidia-smi fallback ──────────────────────────────────────────
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


# Quasar brand color names, resolved by the theme to semantic colors.
def _color_for_percent(pct):
    if pct < 50:
        return "positive"
    if pct < 80:
        return "warning"
    return "negative"


def _proc_color_for_percent(pct):
    """Accent colours for the per-process sub-bar."""
    if pct < 50:
        return "info"
    if pct < 80:
        return "warning"
    return "negative"


class _StatBar(Div):
    """A single labeled mini-bar showing one metric with an optional process sub-bar."""

    def __init__(self, label, icon_name):
        self._label = Div(label, ui_class=monitor_label)
        self._value = Div("\u2014", ui_class=monitor_value)
        self._proc_value = Div("", ui_class=monitor_subvalue)
        self._bar = QLinearProgress(
            ui_value=0,
            ui_color="positive",
            ui_track_color="grey-3",
            ui_class=monitor_bar,
            ui_rounded=True,
        )
        self._proc_bar = QLinearProgress(
            ui_value=0,
            ui_color="info",
            ui_track_color="grey-3",
            ui_class=monitor_subbar,
            ui_rounded=True,
        )

        header = Div(
            self._label,
            self._value,
            self._proc_value,
            ui_class=monitor_stat_header,
        )

        super().__init__(
            header,
            self._bar,
            self._proc_bar,
            ui_class=monitor_stat,
        )

    def update(self, value_text, fraction, color,
               proc_text=None, proc_fraction=None):
        self._value.ui_children = [value_text]
        self._bar.ui_value = max(0.0, min(1.0, fraction))
        self._bar.ui_color = color

        if proc_text is not None:
            frac = max(0.0, min(1.0, proc_fraction or 0))
            self._proc_value.ui_children = [f"({proc_text})"]
            self._proc_bar.ui_value = frac
            self._proc_bar.ui_color = _proc_color_for_percent(frac * 100)
        else:
            self._proc_value.ui_children = [""]
            self._proc_bar.ui_value = 0


class SystemMonitor(Div):
    """Compact system stats display for the toolbar with mini progress bars."""

    def __init__(self, update_interval=1.0):
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
            ui_class=monitor,
        )

        self._running = True
        self._tick = 0
        self._last_proc_vram = None  # cache last known per-process VRAM
        # Trigger one-time init (seeds cpu_percent counters)
        _ensure_psutil()
        threading.Thread(target=self._poll, daemon=True).start()

    def _poll(self):
        while self._running:
            time.sleep(self._interval)
            # Per-process GPU query every other tick (every ~2s)
            include_proc_gpu = (self._tick % 2 == 0)
            self._tick += 1
            stats = _get_stats(include_proc_gpu)
            self._refresh(stats)

    def _refresh(self, stats):
        if "cpu" in stats:
            pct = stats["cpu"]
            proc_cpu = stats.get("proc_cpu")
            self._cpu_bar.update(
                f"{pct:.0f}%", pct / 100, _color_for_percent(pct),
                proc_text=f"{proc_cpu:.0f}%" if proc_cpu is not None else None,
                proc_fraction=proc_cpu / 100 if proc_cpu is not None else None,
            )

        if "ram_used_gb" in stats:
            pct = stats["ram_percent"]
            used = stats["ram_used_gb"]
            total = stats["ram_total_gb"]
            proc_ram = stats.get("proc_ram_gb")
            self._ram_bar.update(
                f"{used:.1f}/{total:.0f}G", pct / 100, _color_for_percent(pct),
                proc_text=f"{proc_ram:.1f}G" if proc_ram is not None else None,
                proc_fraction=proc_ram / total if proc_ram is not None and total > 0 else None,
            )

        if "gpu_util" in stats:
            pct = stats["gpu_util"]
            self._gpu_bar.update(f"{pct}%", pct / 100, _color_for_percent(pct))
        else:
            self._gpu_bar.update("N/A", 0, "grey-5")

        if "gpu_used_gb" in stats:
            used = stats["gpu_used_gb"]
            total = stats["gpu_total_gb"]
            pct = (used / total * 100) if total > 0 else 0
            proc_vram = stats.get("proc_gpu_mem_gb")
            if proc_vram is not None:
                self._last_proc_vram = proc_vram
            else:
                proc_vram = self._last_proc_vram
            self._vram_bar.update(
                f"{used:.1f}/{total:.0f}G", pct / 100, _color_for_percent(pct),
                proc_text=f"{proc_vram:.1f}G" if proc_vram is not None else None,
                proc_fraction=proc_vram / total if proc_vram is not None and total > 0 else None,
            )
        else:
            self._vram_bar.update("N/A", 0, "grey-5")

    def stop(self):
        self._running = False
