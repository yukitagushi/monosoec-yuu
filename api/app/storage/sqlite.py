import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional
from uuid import UUID

from app.domain.job_states import JobStatus


@dataclass
class ProjectRecord:
    id: UUID
    title: str
    reference_note: str
    created_at: datetime


@dataclass
class JobRecord:
    id: UUID
    project_id: UUID
    title: str
    purpose: str
    tone: str
    target_duration_seconds: int
    status: JobStatus
    progress_percent: int
    output_duration_seconds: Optional[int]
    created_at: datetime
    updated_at: datetime


@dataclass
class ArtifactRecord:
    id: UUID
    job_id: UUID
    artifact_type: str
    storage_uri: str
    metadata: dict
    created_at: datetime


@dataclass
class ReviewRecord:
    id: UUID
    job_id: UUID
    decision: str
    comment: Optional[str]
    created_at: datetime


@dataclass
class AuditLogRecord:
    id: UUID
    job_id: UUID
    action: str
    detail: str
    created_at: datetime


@dataclass
class BillingUsageRecord:
    id: UUID
    job_id: UUID
    duration_seconds: int
    created_at: datetime


class SqliteStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                reference_note TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT NOT NULL,
                purpose TEXT NOT NULL,
                tone TEXT NOT NULL,
                target_duration_seconds INTEGER NOT NULL,
                status TEXT NOT NULL,
                progress_percent INTEGER NOT NULL,
                output_duration_seconds INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS job_artifacts (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                storage_uri TEXT NOT NULL,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS job_reviews (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                decision TEXT NOT NULL,
                comment TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                action TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS billing_usage (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def create_project(self, record: ProjectRecord) -> None:
        self._conn.execute(
            """
            INSERT INTO projects (id, title, reference_note, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                str(record.id),
                record.title,
                record.reference_note,
                record.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def list_projects(self) -> Iterable[ProjectRecord]:
        rows = self._conn.execute("SELECT * FROM projects ORDER BY created_at DESC")
        for row in rows:
            yield ProjectRecord(
                id=UUID(row["id"]),
                title=row["title"],
                reference_note=row["reference_note"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )

    def get_project(self, project_id: UUID) -> Optional[ProjectRecord]:
        row = self._conn.execute(
            "SELECT * FROM projects WHERE id = ?",
            (str(project_id),),
        ).fetchone()
        if not row:
            return None
        return ProjectRecord(
            id=UUID(row["id"]),
            title=row["title"],
            reference_note=row["reference_note"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def create_job(self, record: JobRecord) -> None:
        self._conn.execute(
            """
            INSERT INTO jobs
                (id, project_id, title, purpose, tone, target_duration_seconds,
                 status, progress_percent, output_duration_seconds, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(record.id),
                str(record.project_id),
                record.title,
                record.purpose,
                record.tone,
                record.target_duration_seconds,
                record.status.value,
                record.progress_percent,
                record.output_duration_seconds,
                record.created_at.isoformat(),
                record.updated_at.isoformat(),
            ),
        )
        self._conn.commit()

    def list_jobs(self, project_id: UUID) -> Iterable[JobRecord]:
        rows = self._conn.execute(
            "SELECT * FROM jobs WHERE project_id = ? ORDER BY created_at DESC",
            (str(project_id),),
        )
        for row in rows:
            yield self._row_to_job(row)

    def list_all_jobs(self) -> Iterable[JobRecord]:
        rows = self._conn.execute("SELECT * FROM jobs ORDER BY created_at DESC")
        for row in rows:
            yield self._row_to_job(row)

    def get_job(self, job_id: UUID) -> Optional[JobRecord]:
        row = self._conn.execute(
            "SELECT * FROM jobs WHERE id = ?",
            (str(job_id),),
        ).fetchone()
        if not row:
            return None
        return self._row_to_job(row)

    def update_job_status(
        self,
        job_id: UUID,
        status: JobStatus,
        progress_percent: int,
        updated_at: datetime,
    ) -> Optional[JobRecord]:
        self._conn.execute(
            """
            UPDATE jobs
            SET status = ?, progress_percent = ?, updated_at = ?
            WHERE id = ?
            """,
            (status.value, progress_percent, updated_at.isoformat(), str(job_id)),
        )
        self._conn.commit()
        return self.get_job(job_id)

    def update_job_output(self, job_id: UUID, duration_seconds: int) -> None:
        self._conn.execute(
            "UPDATE jobs SET output_duration_seconds = ? WHERE id = ?",
            (duration_seconds, str(job_id)),
        )
        self._conn.commit()

    def create_artifact(self, record: ArtifactRecord) -> None:
        self._conn.execute(
            """
            INSERT INTO job_artifacts
                (id, job_id, artifact_type, storage_uri, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(record.id),
                str(record.job_id),
                record.artifact_type,
                record.storage_uri,
                json.dumps(record.metadata, ensure_ascii=False),
                record.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def list_artifacts(self, job_id: UUID) -> Iterable[ArtifactRecord]:
        rows = self._conn.execute(
            "SELECT * FROM job_artifacts WHERE job_id = ? ORDER BY created_at DESC",
            (str(job_id),),
        )
        for row in rows:
            yield ArtifactRecord(
                id=UUID(row["id"]),
                job_id=UUID(row["job_id"]),
                artifact_type=row["artifact_type"],
                storage_uri=row["storage_uri"],
                metadata=json.loads(row["metadata"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )

    def create_review(self, record: ReviewRecord) -> None:
        self._conn.execute(
            """
            INSERT INTO job_reviews (id, job_id, decision, comment, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(record.id),
                str(record.job_id),
                record.decision,
                record.comment,
                record.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def list_reviews(self, job_id: UUID) -> Iterable[ReviewRecord]:
        rows = self._conn.execute(
            "SELECT * FROM job_reviews WHERE job_id = ? ORDER BY created_at DESC",
            (str(job_id),),
        )
        for row in rows:
            yield ReviewRecord(
                id=UUID(row["id"]),
                job_id=UUID(row["job_id"]),
                decision=row["decision"],
                comment=row["comment"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )

    def create_audit_log(self, record: AuditLogRecord) -> None:
        self._conn.execute(
            """
            INSERT INTO audit_logs (id, job_id, action, detail, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(record.id),
                str(record.job_id),
                record.action,
                record.detail,
                record.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def list_audit_logs(self, job_id: UUID) -> Iterable[AuditLogRecord]:
        rows = self._conn.execute(
            "SELECT * FROM audit_logs WHERE job_id = ? ORDER BY created_at DESC",
            (str(job_id),),
        )
        for row in rows:
            yield AuditLogRecord(
                id=UUID(row["id"]),
                job_id=UUID(row["job_id"]),
                action=row["action"],
                detail=row["detail"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )

    def create_billing_usage(self, record: BillingUsageRecord) -> None:
        self._conn.execute(
            """
            INSERT INTO billing_usage (id, job_id, duration_seconds, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                str(record.id),
                str(record.job_id),
                record.duration_seconds,
                record.created_at.isoformat(),
            ),
        )
        self._conn.commit()

    def list_billing_usage(self, job_id: UUID) -> Iterable[BillingUsageRecord]:
        rows = self._conn.execute(
            "SELECT * FROM billing_usage WHERE job_id = ? ORDER BY created_at DESC",
            (str(job_id),),
        )
        for row in rows:
            yield BillingUsageRecord(
                id=UUID(row["id"]),
                job_id=UUID(row["job_id"]),
                duration_seconds=row["duration_seconds"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> JobRecord:
        return JobRecord(
            id=UUID(row["id"]),
            project_id=UUID(row["project_id"]),
            title=row["title"],
            purpose=row["purpose"],
            tone=row["tone"],
            target_duration_seconds=row["target_duration_seconds"],
            status=JobStatus(row["status"]),
            progress_percent=row["progress_percent"],
            output_duration_seconds=row["output_duration_seconds"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
