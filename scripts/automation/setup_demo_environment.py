from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import psycopg
from sqlalchemy.engine import URL, make_url

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.infra.settings import settings


def _to_sync_admin_url(url: URL, maintenance_database: str) -> str:
    normalized_url = _normalize_runtime_url(url)
    drivername = normalized_url.drivername
    dialect = drivername.split("+", 1)[0] if "+" in drivername else drivername
    sync_driver = "postgresql" if dialect.startswith("postgresql") else dialect
    return normalized_url.set(drivername=sync_driver, database=maintenance_database).render_as_string(hide_password=False)


def _demo_url(url: URL, database_name: str) -> str:
    return _normalize_runtime_url(url).set(database=database_name).render_as_string(hide_password=False)


def _normalize_runtime_url(url: URL) -> URL:
    if (url.host or "").lower() in {"db", "postgres", "postgresql"}:
        return url.set(host="127.0.0.1")
    return url


def _ensure_database(admin_url: str, database_name: str) -> None:
    with psycopg.connect(admin_url, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
            if cursor.fetchone():
                return
            cursor.execute(f'CREATE DATABASE "{database_name}"')


def _run_compose(args: list[str], *, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", *args],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=capture_output,
    )


def _ensure_database_via_docker(*, database_name: str, maintenance_database: str, user: str) -> None:
    exists = _run_compose(
        [
            "exec",
            "-T",
            "db",
            "psql",
            "-U",
            user,
            "-d",
            maintenance_database,
            "-tAc",
            f"SELECT 1 FROM pg_database WHERE datname = '{database_name}'",
        ],
        capture_output=True,
    )
    if exists.stdout.strip() == "1":
        return
    _run_compose(
        [
            "exec",
            "-T",
            "db",
            "psql",
            "-U",
            user,
            "-d",
            maintenance_database,
            "-c",
            f'CREATE DATABASE "{database_name}"',
        ]
    )


def _run(command: list[str], env: dict[str, str]) -> None:
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def _module_from_script(script_path: str) -> str:
    path = Path(script_path)
    if path.suffix == ".py":
        return ".".join(path.with_suffix("").parts)
    return script_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or refresh an isolated demo database with seeded dummy data.")
    parser.add_argument("--database-name", default="dgii_demo")
    parser.add_argument("--maintenance-database", default="postgres")
    parser.add_argument("--seed-script", default="scripts/automation/seed_public_demo_data.py")
    parser.add_argument("--skip-seed", action="store_true")
    args = parser.parse_args()

    base_url = make_url(os.getenv("DATABASE_URL", settings.database_url))
    if not base_url.drivername.startswith("postgresql"):
        raise SystemExit("El entorno demo independiente requiere una DATABASE_URL PostgreSQL.")

    host_demo_url = _demo_url(base_url, args.database_name)
    docker_demo_url = base_url.set(database=args.database_name).render_as_string(hide_password=False)
    admin_url = _to_sync_admin_url(base_url, args.maintenance_database)
    execution_mode = "host"
    try:
        _ensure_database(admin_url, args.database_name)
    except Exception:
        execution_mode = "docker"
        _ensure_database_via_docker(
            database_name=args.database_name,
            maintenance_database=args.maintenance_database,
            user=base_url.username or "dgii",
        )

    if execution_mode == "host":
        env = os.environ.copy()
        env["DATABASE_URL"] = host_demo_url
        _run([sys.executable, "-m", "alembic", "upgrade", "head"], env)
        if not args.skip_seed:
            _run([sys.executable, args.seed_script], env)
    else:
        _run_compose(["build", "web"])
        compose_env = ["-e", f"DATABASE_URL={docker_demo_url}"]
        _run_compose(["run", "--rm", *compose_env, "web", "alembic", "upgrade", "head"])
        if not args.skip_seed:
            _run_compose(
                [
                    "run",
                    "--rm",
                    *compose_env,
                    "web",
                    "python",
                    "-m",
                    _module_from_script(args.seed_script),
                ]
            )

    print(
        "\n".join(
            [
                f"Demo database ready: {args.database_name}",
                f"Execution mode: {execution_mode}",
                f"DATABASE_URL(host)={host_demo_url}",
                f"DATABASE_URL(docker)={docker_demo_url}",
                "Credenciales demo:",
                "  admin@getupsoft.com.do / ChangeMe123!",
                "  cliente@getupsoft.com.do / Tenant123!",
                "  seller@getupsoft.com.do / Seller123!",
                "  seller.auditor@getupsoft.com.do / SellerAudit123!",
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
