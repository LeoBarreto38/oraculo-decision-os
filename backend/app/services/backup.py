from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
import zipfile
from contextlib import closing
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.core.config import DATA_DIR, get_settings
from app.core.database import Base, SessionLocal, engine


BACKUP_DIR = DATA_DIR / "backups"


def _json_default(value: object) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _database_path() -> Path:
    url = get_settings().database_url
    prefix = "sqlite:///"
    if not url.startswith(prefix) or url.endswith(":memory:"):
        raise RuntimeError("Backup v0 requer um banco SQLite persistido em arquivo.")
    return Path(url.removeprefix(prefix)).resolve()


def export_readable_json() -> dict[str, list[dict[str, Any]]]:
    output: dict[str, list[dict[str, Any]]] = {}
    with SessionLocal() as db:
        for table in Base.metadata.sorted_tables:
            rows = db.execute(select(table)).mappings().all()
            output[table.name] = [dict(row) for row in rows]
    return output


def create_backup(destination_dir: Path | None = None) -> Path:
    """Create a consistent SQLite + readable JSON + non-secret configuration archive."""
    destination = (destination_dir or BACKUP_DIR).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    archive = destination / f"oraculo-backup-{timestamp}.zip"
    source_db = _database_path()
    if not source_db.exists():
        raise FileNotFoundError("Banco do Oráculo ainda não foi criado.")

    with tempfile.TemporaryDirectory(prefix="oraculo-backup-") as temporary_name:
        temporary = Path(temporary_name)
        db_copy = temporary / "oraculo.db"
        # sqlite3.Connection's context manager commits/rolls back but does not
        # close on Windows; explicit closing prevents locked files at cleanup.
        with closing(sqlite3.connect(source_db)) as source, closing(sqlite3.connect(db_copy)) as target:
            source.backup(target)
        json_path = temporary / "estado-oraculo.json"
        with json_path.open("w", encoding="utf-8") as handle:
            json.dump(export_readable_json(), handle, ensure_ascii=False, indent=2, default=_json_default)
            handle.write("\n")
        config_dir = temporary / "config"
        config_dir.mkdir()
        for name in ("score_weights.json", "model_pricing.json"):
            config_path = DATA_DIR / name
            if config_path.is_file():
                shutil.copy2(config_path, config_dir / name)
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for item in temporary.rglob("*"):
                if item.is_file():
                    bundle.write(item, item.relative_to(temporary).as_posix())
    _prune_backups(destination, get_settings().backup_retention)
    return archive


def _prune_backups(destination: Path, keep: int) -> None:
    archives = sorted(destination.glob("oraculo-backup-*.zip"), key=lambda item: item.stat().st_mtime, reverse=True)
    for old_archive in archives[keep:]:
        old_archive.unlink(missing_ok=True)
