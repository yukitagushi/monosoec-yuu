import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from app.domain.job_states import JobStatus


@dataclass
class JobRecord:
    id: UUID
    title: str
    input_summary: str
    reference_sources: list[str]
    status: JobStatus
    progress_current: int
    progress_total: int
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
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                input_summary TEXT NOT NULL,
                reference_sources TEXT NOT NULL,
                status TEXT NOT NULL,
                progress_current INTEGER NOT NULL,
                progress_total INTEGER NOT NULL,
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
        self._conn.commit()

    def create_job(self, record: JobRecord) -> None:
        self._conn.execute(
            """
            INSERT INTO jobs
                (id, title, input_summary, reference_sources, status,
                 progress_current, progress_total, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(record.id),
                record.title,
                record.input_summary,
                ",".join(record.reference_sources),
                record.status.value,
                record.progress_current,
                record.progress_total,
                record.created_at.isoformat(),
                record.updated_at.isoformat(),
            ),
        )
        self._conn.commit()

    def get_job(self, job_id: UUID) -> Optional[JobRecord]:
        row = self._conn.execute(
            "SELECT * FROM jobs WHERE id = ?",
            (str(job_id),),
        ).fetchone()
        if not row:
            return None
        return JobRecord(
            id=UUID(row["id"]),
            title=row["title"],
            input_summary=row["input_summary"],
            reference_sources=row["reference_sources"].split(",")
            if row["reference_sources"]
            else [],
            status=JobStatus(row["status"]),
            progress_current=row["progress_current"],
            progress_total=row["progress_total"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def update_job_status(
        self,
        job_id: UUID,
        status: JobStatus,
        progress_current: int,
        updated_at: datetime,
    ) -> Optional[JobRecord]:
        self._conn.execute(
            """
            UPDATE jobs
            SET status = ?, progress_current = ?, updated_at = ?
            WHERE id = ?
            """,
            (status.value, progress_current, updated_at.isoformat(), str(job_id)),
        )
        self._conn.commit()
        return self.get_job(job_id)

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
