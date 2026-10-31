"""
Job Manager Module
Thread-safe background execution manager for pipeline jobs.
Ensures single-worker GPU execution to prevent VRAM contention on 4GB hardware.
"""

import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

from .pipeline_state import PipelineJob, PipelineStage
from .pipeline_config import PipelineConfig
from .pipeline_orchestrator import PipelineOrchestrator


class JobManager:
    def __init__(self, max_workers: int = 1):
        # max_workers=1 guarantees strictly sequential execution for GPU safety on RTX 3050 (4GB VRAM)
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="PipelineWorker")
        self.jobs: Dict[str, PipelineJob] = {}
        self.lock = threading.Lock()
        self.orchestrator = PipelineOrchestrator()

    def submit_job(self, config: PipelineConfig) -> PipelineJob:
        """Queues a new pipeline job and returns the initialized job tracker."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now = time.time()
        job = PipelineJob(
            job_id=job_id,
            created_at=now,
            updated_at=now,
            current_stage=PipelineStage.INITIALIZED,
            status="queued",
            config=config.dict() if hasattr(config, "dict") else config.model_dump()
        )

        with self.lock:
            self.jobs[job_id] = job

        # Submit background task
        self.executor.submit(self._worker_run, job_id, config)
        return job

    def run_sync(self, config: PipelineConfig) -> PipelineJob:
        """Executes a pipeline job synchronously in the current thread (useful for testing and CLI scripts)."""
        job_id = f"sync_{uuid.uuid4().hex[:12]}"
        now = time.time()
        job = PipelineJob(
            job_id=job_id,
            created_at=now,
            updated_at=now,
            current_stage=PipelineStage.INITIALIZED,
            status="processing",
            config=config.dict() if hasattr(config, "dict") else config.model_dump()
        )
        with self.lock:
            self.jobs[job_id] = job

        return self.orchestrator.run_pipeline(
            config=config,
            job_id=job_id,
            job_tracker=job
        )

    def _worker_run(self, job_id: str, config: PipelineConfig):
        with self.lock:
            job = self.jobs.get(job_id)

        if not job or job.is_cancelled:
            return

        def is_cancelled() -> bool:
            with self.lock:
                current_job = self.jobs.get(job_id)
                return current_job.is_cancelled if current_job else True

        self.orchestrator.run_pipeline(
            config=config,
            job_id=job_id,
            job_tracker=job,
            is_cancelled_check=is_cancelled
        )

    def get_job(self, job_id: str) -> Optional[PipelineJob]:
        with self.lock:
            return self.jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return False
            if job.status in ["completed", "failed", "cancelled"]:
                return False
            job.is_cancelled = True
            job.status = "cancelling"
            job.updated_at = time.time()
            return True

    def list_jobs(self, limit: int = 50) -> List[PipelineJob]:
        with self.lock:
            sorted_jobs = sorted(self.jobs.values(), key=lambda j: j.created_at, reverse=True)
            return sorted_jobs[:limit]


# Global singleton instance
job_manager = JobManager(max_workers=1)
