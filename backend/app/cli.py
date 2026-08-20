from __future__ import annotations

import argparse

from app.core.database import SessionLocal, init_database
from app.core.migrations import record_migrations
from app.scheduler.alerts import run_alert_rules
from app.services.backup import create_backup
from app.services.seed import seed_estado_zero


def init_db() -> None:
    init_database()
    with SessionLocal() as db:
        migrations = record_migrations(db)
        seed_estado_zero(db)
    suffix = f"; migrações registradas: {', '.join(migrations)}" if migrations else "; schema já atualizado"
    print(f"Banco do Oráculo inicializado com seed idempotente{suffix}.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="Administração local do Oráculo")
    parser.add_argument("command", choices=("init-db", "backup", "alerts"))
    args = parser.parse_args()
    if args.command == "init-db":
        init_db()
    elif args.command == "backup":
        init_db()
        archive = create_backup()
        print(f"Backup criado em {archive}")
    else:
        init_db()
        with SessionLocal() as db:
            created = run_alert_rules(db)
        print(f"Regras de alerta executadas: {sum(created.values())} novo(s).")


if __name__ == "__main__":
    main()
