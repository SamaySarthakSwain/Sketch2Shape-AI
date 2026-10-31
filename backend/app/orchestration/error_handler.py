"""
Pipeline Error Handler & Retry Manager
Encapsulates structured exception handling, failure classification, and retry policies.
"""

from typing import Dict, Any, Optional
from .pipeline_state import PipelineStage


class PipelineException(Exception):
    def __init__(self, stage: PipelineStage, message: str, recoverable: bool = False):
        super().__init__(message)
        self.stage = stage
        self.message = message
        self.recoverable = recoverable


class RetryManager:
    @staticmethod
    def should_retry(stage: PipelineStage, attempt: int, max_attempts: int = 2) -> bool:
        """Determines if a failed stage is eligible for retry."""
        if attempt >= max_attempts:
            return False

        # Non-recoverable stages
        if stage in [PipelineStage.VALIDATING_INPUT, PipelineStage.CANCELLED]:
            return False

        # Recoverable stages (preprocessing, reconstruction, export)
        return True
