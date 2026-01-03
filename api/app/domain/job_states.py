from enum import Enum
from typing import Dict, Set


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING_RENDER = "running_render"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"

TRANSITIONS: Dict[JobStatus, Set[JobStatus]] = {
    JobStatus.QUEUED: {JobStatus.RUNNING_RENDER, JobStatus.FAILED},
    JobStatus.RUNNING_RENDER: {JobStatus.NEEDS_REVIEW, JobStatus.FAILED},
    JobStatus.NEEDS_REVIEW: {JobStatus.APPROVED, JobStatus.REJECTED},
    JobStatus.APPROVED: set(),
    JobStatus.REJECTED: set(),
    JobStatus.FAILED: set(),
}


def can_transition(current: JobStatus, target: JobStatus) -> bool:
    return target in TRANSITIONS.get(current, set())


def progress_for_status(status: JobStatus) -> int:
    mapping = {
        JobStatus.QUEUED: 0,
        JobStatus.RUNNING_RENDER: 60,
        JobStatus.NEEDS_REVIEW: 80,
        JobStatus.APPROVED: 100,
        JobStatus.REJECTED: 100,
        JobStatus.FAILED: 0,
    }
    return mapping.get(status, 0)
