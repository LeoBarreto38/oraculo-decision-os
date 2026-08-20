from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import BACKEND_DIR
from app.models.entities import SchemaMigration


MIGRATIONS_DIR = BACKEND_DIR / "migrations"


def record_migrations(db: Session) -> list[str]:
    """Record audited SQL artifacts after SQLAlchemy creates the equivalent v0 schema."""
    recorded: list[str] = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        existing = db.scalar(select(SchemaMigration).where(SchemaMigration.version == path.stem))
        if existing:
            if existing.checksum_sha256 != checksum:
                raise RuntimeError(f"Checksum da migração {path.name} foi alterado após aplicação.")
            continue
        db.add(SchemaMigration(version=path.stem, checksum_sha256=checksum))
        recorded.append(path.stem)
    db.commit()
    return recorded
