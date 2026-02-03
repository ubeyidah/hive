"""Schedule storage and runner for Hive agents."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

import yaml

from hive.config.loader import get_config_dir


@dataclass
class ScheduledJob:
    job_id: str
    agent_name: str
    task: str
    schedule_type: str
    interval_minutes: Optional[int]
    cron: Optional[str]
    channel_id: Optional[int]
    next_run: str


class ScheduleStore:
    def __init__(self) -> None:
        self.path = get_config_dir() / "schedules.yaml"

    def load_jobs(self) -> List[ScheduledJob]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or []
        if not isinstance(data, list):
            return []
        jobs: List[ScheduledJob] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            jobs.append(
                ScheduledJob(
                    job_id=str(item.get("job_id")),
                    agent_name=str(item.get("agent_name")),
                    task=str(item.get("task")),
                    schedule_type=str(item.get("schedule_type")),
                    interval_minutes=_safe_int(item.get("interval_minutes")),
                    cron=str(item.get("cron")) if item.get("cron") else None,
                    channel_id=_safe_int(item.get("channel_id")),
                    next_run=str(item.get("next_run")),
                )
            )
        return jobs

    def save_jobs(self, jobs: List[ScheduledJob]) -> None:
        payload = [job.__dict__ for job in jobs]
        with self.path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(payload, handle, sort_keys=False)

    def add_job(
        self,
        agent_name: str,
        task: str,
        schedule_type: str,
        interval_minutes: Optional[int],
        cron: Optional[str],
        channel_id: Optional[int],
    ) -> ScheduledJob:
        jobs = self.load_jobs()
        next_run = _compute_next_run(schedule_type, interval_minutes, cron)
        job = ScheduledJob(
            job_id=str(uuid4()),
            agent_name=agent_name,
            task=task,
            schedule_type=schedule_type,
            interval_minutes=interval_minutes,
            cron=cron,
            channel_id=channel_id,
            next_run=next_run.isoformat(),
        )
        jobs.append(job)
        self.save_jobs(jobs)
        return job

    def list_jobs(self, agent_name: Optional[str] = None) -> List[ScheduledJob]:
        jobs = self.load_jobs()
        if agent_name is None:
            return jobs
        return [job for job in jobs if job.agent_name == agent_name]

    def remove_job(self, job_id: str, agent_name: Optional[str] = None) -> bool:
        jobs = self.load_jobs()
        remaining: List[ScheduledJob] = []
        removed = False
        for job in jobs:
            if job.job_id == job_id and (
                agent_name is None or job.agent_name == agent_name
            ):
                removed = True
                continue
            remaining.append(job)
        if removed:
            self.save_jobs(remaining)
        return removed

    def update_job(self, job: ScheduledJob) -> None:
        jobs = self.load_jobs()
        updated: List[ScheduledJob] = []
        for item in jobs:
            if item.job_id == job.job_id:
                updated.append(job)
            else:
                updated.append(item)
        self.save_jobs(updated)


class ScheduleRunner:
    def __init__(self, store: ScheduleStore) -> None:
        self.store = store
        self._running = False

    async def run(self, execute) -> None:
        self._running = True
        while self._running:
            now = datetime.now()
            jobs = self.store.load_jobs()
            for job in jobs:
                next_run = _parse_datetime(job.next_run)
                if next_run and now >= next_run:
                    await execute(job)
                    job.next_run = _compute_next_run(
                        job.schedule_type, job.interval_minutes, job.cron, now
                    ).isoformat()
                    self.store.update_job(job)
            await asyncio.sleep(30)

    def stop(self) -> None:
        self._running = False


def _parse_datetime(value: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _compute_next_run(
    schedule_type: str,
    interval_minutes: Optional[int],
    cron: Optional[str],
    now: Optional[datetime] = None,
) -> datetime:
    current = now or datetime.now()
    if schedule_type == "interval" and interval_minutes:
        return current + timedelta(minutes=interval_minutes)
    if schedule_type == "cron" and cron:
        minute, hour = _parse_cron(cron)
        candidate = current.replace(second=0, microsecond=0, minute=minute, hour=hour)
        if candidate <= current:
            candidate = candidate + timedelta(days=1)
        return candidate
    return current + timedelta(minutes=5)


def _parse_cron(expr: str) -> tuple[int, int]:
    parts = expr.split()
    if len(parts) < 2:
        return 0, 0
    minute = _safe_int(parts[0]) or 0
    hour = _safe_int(parts[1]) or 0
    return minute, hour


def _safe_int(value: object) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
