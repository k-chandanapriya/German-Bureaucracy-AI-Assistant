"""Background reading jobs, so the page can show progress while a model works.

Reading a letter with a local model takes a minute or more. Running it in a
worker thread keeps the API responsive, and the frontend polls the job for
its current stage. One worker: a local model reads one letter at a time
anyway. Jobs live in memory; a restart forgets unfinished ones.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field

log = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="reader")
_lock = threading.Lock()
_jobs: dict[str, "Job"] = {}
KEEP_FINISHED_S = 3600


@dataclass
class Job:
    id: str
    owner: str = ""
    status: str = "queued"  # queued | running | done | error
    stage: str = "Waiting for the reader"
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    result: dict | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("owner")
        end = self.finished_at or time.time()
        d["elapsed_s"] = round(end - self.started_at)
        return d


def _update(job_id: str, **changes) -> None:
    with _lock:
        job = _jobs.get(job_id)
        if job:
            for k, v in changes.items():
                setattr(job, k, v)


def _cleanup() -> None:
    cutoff = time.time() - KEEP_FINISHED_S
    with _lock:
        for jid in [j.id for j in _jobs.values() if j.finished_at and j.finished_at < cutoff]:
            del _jobs[jid]


def submit(work: Callable[[Callable[[str], None]], dict], user_error: type[Exception], owner: str = "") -> Job:
    """Run work(progress) in the background. Errors of type user_error are shown as-is."""
    _cleanup()
    job = Job(id=uuid.uuid4().hex, owner=owner)
    with _lock:
        _jobs[job.id] = job

    def run() -> None:
        _update(job.id, status="running", stage="Starting")
        try:
            result = work(lambda stage: _update(job.id, stage=stage))
            _update(job.id, status="done", stage="Done", result=result, finished_at=time.time())
        except user_error as e:
            _update(job.id, status="error", error=str(e), finished_at=time.time())
        except Exception:  # noqa: BLE001 - never leave a job hanging
            log.exception("Reading job %s failed", job.id)
            _update(job.id, status="error", error="Something went wrong while reading the letter. Please try again.", finished_at=time.time())

    _executor.submit(run)
    return job


def get(job_id: str) -> Job | None:
    with _lock:
        return _jobs.get(job_id)
