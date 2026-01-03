from enum import Enum
from typing import Dict, Set


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING_VALIDATION = "running_validation"
    RUNNING_OUTLINE = "running_outline"
    RUNNING_SCRIPT = "running_script"
    RUNNING_SLIDES = "running_slides"
    RUNNING_TTS = "running_tts"
    RUNNING_RENDER = "running_render"
    RUNNING_QUALITY_CHECK = "running_quality_check"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    FAILED = "failed"

PIPELINE_ORDER = [
    JobStatus.RUNNING_VALIDATION,
    JobStatus.RUNNING_OUTLINE,
    JobStatus.RUNNING_SCRIPT,
    JobStatus.RUNNING_SLIDES,
    JobStatus.RUNNING_TTS,
    JobStatus.RUNNING_RENDER,
    JobStatus.RUNNING_QUALITY_CHECK,
    JobStatus.AWAITING_APPROVAL,
]

TRANSITIONS: Dict[JobStatus, Set[JobStatus]] = {
    JobStatus.QUEUED: {JobStatus.RUNNING_VALIDATION, JobStatus.FAILED},
    JobStatus.RUNNING_VALIDATION: {JobStatus.RUNNING_OUTLINE, JobStatus.FAILED},
    JobStatus.RUNNING_OUTLINE: {JobStatus.RUNNING_SCRIPT, JobStatus.FAILED},
    JobStatus.RUNNING_SCRIPT: {JobStatus.RUNNING_SLIDES, JobStatus.FAILED},
    JobStatus.RUNNING_SLIDES: {JobStatus.RUNNING_TTS, JobStatus.FAILED},
    JobStatus.RUNNING_TTS: {JobStatus.RUNNING_RENDER, JobStatus.FAILED},
    JobStatus.RUNNING_RENDER: {JobStatus.RUNNING_QUALITY_CHECK, JobStatus.FAILED},
    JobStatus.RUNNING_QUALITY_CHECK: {JobStatus.AWAITING_APPROVAL, JobStatus.FAILED},
    JobStatus.AWAITING_APPROVAL: {JobStatus.APPROVED, JobStatus.FAILED},
    JobStatus.APPROVED: set(),
    JobStatus.FAILED: set(),
}


def can_transition(current: JobStatus, target: JobStatus) -> bool:
    return target in TRANSITIONS.get(current, set())


def progress_for_status(status: JobStatus) -> int:
    if status in PIPELINE_ORDER:
        return PIPELINE_ORDER.index(status) + 1
    if status == JobStatus.APPROVED:
        return len(PIPELINE_ORDER)
    return 0
