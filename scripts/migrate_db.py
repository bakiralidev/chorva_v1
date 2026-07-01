import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncpg
from sqlalchemy import Boolean, Column, DateTime, String, false, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateColumn
from app.database import DATABASE_URL, engine, Base
import app.models  # noqa: F401 - register all SQLAlchemy models in Base.metadata

MISSING_COLUMNS = {
    "users": [
        Column("is_verified", Boolean(), nullable=False, server_default=false()),
        Column("accepted_offer", Boolean(), nullable=False, server_default=false()),
        Column("preferred_lang", String(10), nullable=True),
    ],
    "offers": [
        Column("has_file", Boolean(), nullable=False, server_default=false()),
        Column("file_url", String(255), nullable=True),
    ],
    "advertisements": [
        Column("updated_at", DateTime(), nullable=True),
        Column("is_deleted", Boolean(), nullable=False, server_default=false()),
        Column("deleted_at", DateTime(), nullable=True),
    ],
}


def _column_exists(sync_conn, table_name: str, column_name: str) -> bool:
    inspector = inspect(sync_conn)
    if not inspector.has_table(table_name):
        return False
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


async def _add_column_if_missing(conn, table_name: str, column: Column) -> bool:
    exists = await conn.run_sync(_column_exists, table_name, column.name)
    if exists:
        return False

    preparer = conn.dialect.identifier_preparer
    table_sql = preparer.quote(table_name)
    column_sql = CreateColumn(column).compile(dialect=conn.dialect)
    await conn.execute(text(f"ALTER TABLE {table_sql} ADD COLUMN {column_sql}"))
    return True


async def _create_postgresql_database() -> None:
    url = make_url(DATABASE_URL)
    if not url.drivername.startswith("postgresql") or not url.database:
        raise RuntimeError("Automatic database creation is only supported for PostgreSQL URLs.")

    database_name = url.database
    maintenance_url = url.set(drivername="postgresql", database="postgres")
    conn = await asyncpg.connect(dsn=maintenance_url.render_as_string(hide_password=False))
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            database_name,
        )
        if not exists:
            quoted_database_name = '"' + database_name.replace('"', '""') + '"'
            await conn.execute(f"CREATE DATABASE {quoted_database_name}")
            print(f"Created PostgreSQL database: {database_name}")
    finally:
        await conn.close()


async def _run_migration() -> list[str]:
    added_columns: list[str] = []

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        for table_name, columns in MISSING_COLUMNS.items():
            for column in columns:
                if await _add_column_if_missing(conn, table_name, column):
                    added_columns.append(f"{table_name}.{column.name}")

    return added_columns


async def migrate():
    try:
        added_columns = await _run_migration()
    except asyncpg.InvalidCatalogNameError:
        await _create_postgresql_database()
        await engine.dispose()
        added_columns = await _run_migration()

    if added_columns:
        print("Added missing columns: " + ", ".join(added_columns))
    else:
        print("No missing columns found.")
    print("Database migration completed successfully.")

if __name__ == "__main__":
    asyncio.run(migrate())
