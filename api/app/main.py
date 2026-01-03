from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.domain.job_states import JobStatus, can_transition, progress_for_status
from app.storage.sqlite import ArtifactRecord, JobRecord, SqliteStore

app = FastAPI(title="monosoec-yuu API", version="0.1.0")


class JobCreate(BaseModel):
    title: str
    input_summary: str
    reference_sources: list[str] = Field(default_factory=list)


class JobResponse(BaseModel):
    id: UUID
    title: str
    input_summary: str
    reference_sources: list[str]
    status: JobStatus
    progress_current: int
    progress_total: int
    created_at: datetime
    updated_at: datetime


class ArtifactCreate(BaseModel):
    artifact_type: str
    storage_uri: str
    metadata: dict = Field(default_factory=dict)


class JobStatusUpdate(BaseModel):
    status: JobStatus


STORE = SqliteStore(Path("api_data/store.db"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/jobs", response_model=JobResponse)
def create_job(payload: JobCreate) -> JobResponse:
    if not payload.reference_sources:
        raise HTTPException(status_code=400, detail="reference_sources is required")

    job_id = uuid4()
    now = datetime.utcnow()
    job = JobResponse(
        id=job_id,
        title=payload.title,
        input_summary=payload.input_summary,
        reference_sources=payload.reference_sources,
        status=JobStatus.QUEUED,
        progress_current=0,
        progress_total=8,
        created_at=now,
        updated_at=now,
    )
    STORE.create_job(
        JobRecord(
            id=job_id,
            title=job.title,
            input_summary=job.input_summary,
            reference_sources=job.reference_sources,
            status=job.status,
            progress_current=job.progress_current,
            progress_total=job.progress_total,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
    )
    return job


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID) -> JobResponse:
    record = STORE.get_job(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="job not found")
    return JobResponse(**record.__dict__)


@app.post("/jobs/{job_id}/status", response_model=JobResponse)
def update_job_status(job_id: UUID, payload: JobStatusUpdate) -> JobResponse:
    job = STORE.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    if not can_transition(job.status, payload.status):
        raise HTTPException(
            status_code=400,
            detail=f"cannot transition from {job.status} to {payload.status}",
        )

    updated_at = datetime.utcnow()
    progress_current = progress_for_status(payload.status)
    updated = STORE.update_job_status(
        job_id, payload.status, progress_current, updated_at
    )
    if not updated:
        raise HTTPException(status_code=404, detail="job not found")
    return JobResponse(**updated.__dict__)


@app.post("/jobs/{job_id}/artifacts", status_code=201)
def create_job_artifact(job_id: UUID, payload: ArtifactCreate) -> dict:
    job = STORE.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    artifact_id = uuid4()
    STORE.create_artifact(
        ArtifactRecord(
            id=artifact_id,
            job_id=job_id,
            artifact_type=payload.artifact_type,
            storage_uri=payload.storage_uri,
            metadata=payload.metadata,
            created_at=datetime.utcnow(),
        )
    )
    return {"id": artifact_id, "job_id": job_id}
