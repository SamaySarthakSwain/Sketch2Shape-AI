"""
Pipeline Execution Logger and Resource Monitor
Monitors GPU VRAM, System RAM, latency, and chronological stage events.
"""

import os
import sys
import time
import psutil
from typing import Dict, Any, List, Optional
import torch


class ExecutionLogger:
    @staticmethod
    def get_hardware_telemetry() -> Dict[str, float]:
        """Captures instantaneous VRAM and System RAM utilization."""
        vram_used_mb = 0.0
        vram_reserved_mb = 0.0
        if torch.cuda.is_available():
            try:
                vram_used_mb = round(torch.cuda.memory_allocated(0) / (1024 * 1024), 2)
                vram_reserved_mb = round(torch.cuda.memory_reserved(0) / (1024 * 1024), 2)
            except Exception:
                pass

        mem = psutil.virtual_memory()
        ram_used_mb = round((mem.total - mem.available) / (1024 * 1024), 2)

        return {
            "vram_used_mb": vram_used_mb,
            "vram_reserved_mb": vram_reserved_mb,
            "ram_used_mb": ram_used_mb,
            "timestamp": time.time(),
        }

    @staticmethod
    def cleanup_gpu_memory():
        """Flushes CUDA allocation cache and triggers Python garbage collection."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        import gc
        gc.collect()

    @staticmethod
    def log_stage_event(job_id: str, stage: str, message: str):
        t_str = time.strftime("%H:%M:%S")
        print(f"[{t_str}] [Job: {job_id[:8]}] [{stage}] {message}")
