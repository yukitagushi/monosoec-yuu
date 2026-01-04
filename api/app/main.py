from __future__ import annotations

import shutil
import subprocess
import threading
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.domain.job_states import JobStatus, can_transition, progress_for_status
from app.storage.sqlite import (
    ArtifactRecord,
    AuditLogRecord,
    BillingUsageRecord,
    JobRecord,
    ProjectRecord,
    ReviewRecord,
    SqliteStore,
)

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
ARTIFACTS_DIR = DATA_DIR / "artifacts"
JOBS_DIR = DATA_DIR / "jobs"
WORKER_SCRIPT = BASE_DIR / "worker" / "render_worker.sh"

STORE = SqliteStore(DATA_DIR / "store.db")

app = FastAPI(title="monosoec-yuu API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProjectCreate(BaseModel):
    title: str
    reference_note: str = ""


class ProjectResponse(BaseModel):
    id: uuid.UUID
    title: str
    reference_note: str
    created_at: datetime


class JobCreate(BaseModel):
    title: str
    purpose: str
    tone: str
    target_duration_seconds: int = Field(gt=0)


class JobResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    purpose: str
    tone: str
    target_duration_seconds: int
    status: JobStatus
    progress_percent: int
    output_duration_seconds: Optional[int]
    created_at: datetime
    updated_at: datetime
    artifacts: list[dict] = Field(default_factory=list)
    logs: list[str] = Field(default_factory=list)
    reviews: list[dict] = Field(default_factory=list)
    billing: list[dict] = Field(default_factory=list)


class ReviewCreate(BaseModel):
    decision: str
    comment: Optional[str] = ""


def _job_to_response(job: JobRecord) -> JobResponse:
    artifacts = [
        {
            "id": artifact.id,
            "artifact_type": artifact.artifact_type,
            "storage_uri": artifact.storage_uri,
            "created_at": artifact.created_at,
        }
        for artifact in STORE.list_artifacts(job.id)
    ]
    logs = [
        f"{log.created_at.strftime('%Y-%m-%d %H:%M')} {log.detail}"
        for log in STORE.list_audit_logs(job.id)
    ]
    reviews = [
        {
            "decision": review.decision,
            "comment": review.comment,
            "created_at": review.created_at,
        }
        for review in STORE.list_reviews(job.id)
    ]
    billing = [
        {
            "duration_seconds": usage.duration_seconds,
            "created_at": usage.created_at,
        }
        for usage in STORE.list_billing_usage(job.id)
    ]
    return JobResponse(
        id=job.id,
        project_id=job.project_id,
        title=job.title,
        purpose=job.purpose,
        tone=job.tone,
        target_duration_seconds=job.target_duration_seconds,
        status=job.status,
        progress_percent=job.progress_percent,
        output_duration_seconds=job.output_duration_seconds,
        created_at=job.created_at,
        updated_at=job.updated_at,
        artifacts=artifacts,
        logs=logs,
        reviews=reviews,
        billing=billing,
    )


def _log(job_id: uuid.UUID, action: str, detail: str) -> None:
    STORE.create_audit_log(
        AuditLogRecord(
            id=uuid.uuid4(),
            job_id=job_id,
            action=action,
            detail=detail,
            created_at=datetime.utcnow(),
        )
    )


def _get_default_project() -> ProjectRecord:
    projects = list(STORE.list_projects())
    if projects:
        return projects[0]
    record = ProjectRecord(
        id=uuid.uuid4(),
        title="デフォルトプロジェクト",
        reference_note="",
        created_at=datetime.utcnow(),
    )
    STORE.create_project(record)
    return record


def _ensure_directories(job_id: uuid.UUID) -> tuple[Path, Path, Path]:
    job_dir = JOBS_DIR / str(job_id)
    input_dir = job_dir / "input"
    output_dir = job_dir / "out"
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / "audio").mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    return job_dir, input_dir, output_dir


def _extract_audio_zip(zip_path: Path, input_dir: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.namelist():
            if member.lower().endswith("/"):
                continue
            target_path = input_dir / "audio" / Path(member).name
            with archive.open(member) as source, open(target_path, "wb") as target:
                shutil.copyfileobj(source, target)


def _probe_duration(video_path: Path) -> int:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return 0
    try:
        return int(float(result.stdout.strip()))
    except ValueError:
        return 0


def _run_render(job_id: uuid.UUID) -> None:
    job = STORE.get_job(job_id)
    if not job:
        return

    job_dir, input_dir, output_dir = _ensure_directories(job_id)
    _log(job_id, "render.start", "動画合成を開始")

    updated = STORE.update_job_status(
        job_id,
        JobStatus.RUNNING_RENDER,
        progress_for_status(JobStatus.RUNNING_RENDER),
        datetime.utcnow(),
    )
    if not updated:
        return

    try:
        subprocess.run(
            ["bash", str(WORKER_SCRIPT)],
            cwd=job_dir,
            check=True,
        )
        output_path = output_dir / "final_1080p.mp4"
        if not output_path.exists():
            raise RuntimeError("output video not found")

        artifact_path = ARTIFACTS_DIR / f"{job_id}_final_1080p.mp4"
        shutil.copyfile(output_path, artifact_path)
        STORE.create_artifact(
            ArtifactRecord(
                id=uuid.uuid4(),
                job_id=job_id,
                artifact_type="video_mp4",
                storage_uri=str(artifact_path),
                metadata={},
                created_at=datetime.utcnow(),
            )
        )
        duration_seconds = _probe_duration(artifact_path)
        if duration_seconds:
            STORE.update_job_output(job_id, duration_seconds)
            STORE.create_billing_usage(
                BillingUsageRecord(
                    id=uuid.uuid4(),
                    job_id=job_id,
                    duration_seconds=duration_seconds,
                    created_at=datetime.utcnow(),
                )
            )
        STORE.update_job_status(
            job_id,
            JobStatus.NEEDS_REVIEW,
            progress_for_status(JobStatus.NEEDS_REVIEW),
            datetime.utcnow(),
        )
        _log(job_id, "render.complete", "動画合成が完了")
    except Exception as exc:
        STORE.update_job_status(
            job_id,
            JobStatus.FAILED,
            progress_for_status(JobStatus.FAILED),
            datetime.utcnow(),
        )
        _log(job_id, "render.failed", f"動画合成に失敗: {exc}")


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/projects", response_model=ProjectResponse)
def create_project(payload: ProjectCreate) -> ProjectResponse:
    project_id = uuid.uuid4()
    record = ProjectRecord(
        id=project_id,
        title=payload.title,
        reference_note=payload.reference_note,
        created_at=datetime.utcnow(),
    )
    STORE.create_project(record)
    return ProjectResponse(**record.__dict__)


@app.get("/projects", response_model=list[ProjectResponse])
def list_projects() -> list[ProjectResponse]:
    return [ProjectResponse(**project.__dict__) for project in STORE.list_projects()]


@app.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: uuid.UUID) -> ProjectResponse:
    project = STORE.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="project not found")
    return ProjectResponse(**project.__dict__)


@app.post("/projects/{project_id}/jobs", response_model=JobResponse)
def create_job(project_id: uuid.UUID, payload: JobCreate) -> JobResponse:
    if not STORE.get_project(project_id):
        raise HTTPException(status_code=404, detail="project not found")

    job_id = uuid.uuid4()
    now = datetime.utcnow()
    job = JobRecord(
        id=job_id,
        project_id=project_id,
        title=payload.title,
        purpose=payload.purpose,
        tone=payload.tone,
        target_duration_seconds=payload.target_duration_seconds,
        status=JobStatus.QUEUED,
        progress_percent=progress_for_status(JobStatus.QUEUED),
        output_duration_seconds=None,
        created_at=now,
        updated_at=now,
    )
    STORE.create_job(job)
    _log(job_id, "job.create", "ジョブを作成")
    return _job_to_response(job)


@app.get("/projects/{project_id}/jobs", response_model=list[JobResponse])
def list_jobs(project_id: uuid.UUID) -> list[JobResponse]:
    if not STORE.get_project(project_id):
        raise HTTPException(status_code=404, detail="project not found")
    return [_job_to_response(job) for job in STORE.list_jobs(project_id)]


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: uuid.UUID) -> JobResponse:
    job = STORE.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return _job_to_response(job)


@app.post("/jobs/{job_id}/upload", response_model=JobResponse)
def upload_inputs(
    job_id: uuid.UUID,
    slides_pdf: UploadFile = File(...),
    audio_zip: UploadFile = File(...),
) -> JobResponse:
    job = STORE.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    job_dir, input_dir, _ = _ensure_directories(job_id)
    slides_path = input_dir / "slides.pdf"
    audio_zip_path = input_dir / "audio.zip"

    with open(slides_path, "wb") as target:
        shutil.copyfileobj(slides_pdf.file, target)
    with open(audio_zip_path, "wb") as target:
        shutil.copyfileobj(audio_zip.file, target)

    _extract_audio_zip(audio_zip_path, input_dir)

    STORE.create_artifact(
        ArtifactRecord(
            id=uuid.uuid4(),
            job_id=job_id,
            artifact_type="slides_pdf",
            storage_uri=str(slides_path),
            metadata={},
            created_at=datetime.utcnow(),
        )
    )
    STORE.create_artifact(
        ArtifactRecord(
            id=uuid.uuid4(),
            job_id=job_id,
            artifact_type="audio_zip",
            storage_uri=str(audio_zip_path),
            metadata={},
            created_at=datetime.utcnow(),
        )
    )
    _log(job_id, "inputs.upload", "入力ファイルをアップロード")

    thread = threading.Thread(target=_run_render, args=(job_id,), daemon=True)
    thread.start()
    return _job_to_response(job)


@app.post("/jobs/{job_id}/reviews", response_model=JobResponse)
def review_job(job_id: uuid.UUID, payload: ReviewCreate) -> JobResponse:
    job = STORE.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    decision = payload.decision.lower()
    if decision not in {"approved", "rejected"}:
        raise HTTPException(status_code=400, detail="decision must be approved/rejected")

    next_status = JobStatus.APPROVED if decision == "approved" else JobStatus.REJECTED
    if not can_transition(job.status, next_status):
        raise HTTPException(status_code=400, detail="invalid job status transition")

    STORE.create_review(
        ReviewRecord(
            id=uuid.uuid4(),
            job_id=job_id,
            decision=decision,
            comment=payload.comment,
            created_at=datetime.utcnow(),
        )
    )
    STORE.update_job_status(
        job_id,
        next_status,
        progress_for_status(next_status),
        datetime.utcnow(),
    )
    _log(job_id, f"review.{decision}", f"レビュー: {decision}")
    updated = STORE.get_job(job_id)
    if not updated:
        raise HTTPException(status_code=404, detail="job not found")
    return _job_to_response(updated)


@app.get("/jobs/{job_id}/artifacts")
def list_job_artifacts(job_id: uuid.UUID) -> list[dict]:
    job = STORE.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return [
        {
            "id": artifact.id,
            "artifact_type": artifact.artifact_type,
            "storage_uri": artifact.storage_uri,
            "created_at": artifact.created_at,
        }
        for artifact in STORE.list_artifacts(job_id)
    ]


@app.get("/jobs/{job_id}/artifacts/{artifact_id}/download")
def download_artifact(job_id: uuid.UUID, artifact_id: uuid.UUID) -> FileResponse:
    job = STORE.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    artifact = next(
        (item for item in STORE.list_artifacts(job_id) if item.id == artifact_id),
        None,
    )
    if not artifact:
        raise HTTPException(status_code=404, detail="artifact not found")
    path = Path(artifact.storage_uri)
    if not path.exists():
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(path)


@app.post("/jobs", response_model=JobResponse)
def create_job_simple(payload: JobCreate) -> JobResponse:
    project = _get_default_project()
    job_id = uuid.uuid4()
    now = datetime.utcnow()
    job = JobRecord(
        id=job_id,
        project_id=project.id,
        title=payload.title,
        purpose=payload.purpose,
        tone=payload.tone,
        target_duration_seconds=payload.target_duration_seconds,
        status=JobStatus.QUEUED,
        progress_percent=progress_for_status(JobStatus.QUEUED),
        output_duration_seconds=None,
        created_at=now,
        updated_at=now,
    )
    STORE.create_job(job)
    _log(job_id, "job.create", "ジョブを作成")
    return _job_to_response(job)


@app.get("/jobs", response_model=list[JobResponse])
def list_jobs_simple() -> list[JobResponse]:
    return [_job_to_response(job) for job in STORE.list_all_jobs()]


@app.post("/jobs/{job_id}/render", response_model=JobResponse)
def render_job(job_id: uuid.UUID) -> JobResponse:
    job = STORE.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    thread = threading.Thread(target=_run_render, args=(job_id,), daemon=True)
    thread.start()
    _log(job_id, "render.request", "レンダリングを開始")
    updated = STORE.get_job(job_id)
    if not updated:
        raise HTTPException(status_code=404, detail="job not found")
    return _job_to_response(updated)
