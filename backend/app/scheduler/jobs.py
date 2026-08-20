from __future__ import annotations

from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.scheduler.alerts import create_internal_event, run_alert_rules
from app.services.backup import create_backup


_scheduler: BackgroundScheduler | None = None


def _parse_hhmm(value: str) -> tuple[int, int]:
    hour, minute = value.split(":", maxsplit=1)
    return int(hour), int(minute)


def _alerts_job() -> None:
    with SessionLocal() as db:
        run_alert_rules(db)


def _morning_job() -> None:
    with SessionLocal() as db:
        create_internal_event(
            db,
            "BRIEFING_MATINAL",
            "Briefing matinal disponível: revise exatamente três prioridades e confirme a próxima ação comercial.",
        )


def _evening_job() -> None:
    with SessionLocal() as db:
        create_internal_event(db, "CHECKIN_NOTURNO", "Check-in do fim do dia disponível.")


def _backup_job() -> None:
    create_backup()


def start_scheduler() -> BackgroundScheduler | None:
    global _scheduler
    settings = get_settings()
    if not settings.scheduler_enabled or (_scheduler and _scheduler.running):
        return _scheduler
    morning_hour, morning_minute = _parse_hhmm(settings.morning_briefing_time)
    evening_hour, evening_minute = _parse_hhmm(settings.evening_checkin_time)
    _scheduler = BackgroundScheduler(timezone=settings.timezone, daemon=True)
    _scheduler.add_job(_alerts_job, "interval", minutes=30, id="deterministic-alerts", replace_existing=True)
    _scheduler.add_job(
        _morning_job,
        CronTrigger(hour=morning_hour, minute=morning_minute, timezone=settings.timezone),
        id="morning-briefing",
        replace_existing=True,
    )
    _scheduler.add_job(
        _evening_job,
        CronTrigger(hour=evening_hour, minute=evening_minute, timezone=settings.timezone),
        id="evening-checkin",
        replace_existing=True,
    )
    _scheduler.add_job(
        _backup_job,
        CronTrigger(hour=2, minute=15, timezone=settings.timezone),
        id="daily-backup",
        replace_existing=True,
    )
    _scheduler.start()
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None


def scheduler_status() -> dict[str, object]:
    if not _scheduler or not _scheduler.running:
        return {"running": False, "jobs": []}
    return {
        "running": True,
        "jobs": [
            {"id": job.id, "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None}
            for job in _scheduler.get_jobs()
        ],
    }
