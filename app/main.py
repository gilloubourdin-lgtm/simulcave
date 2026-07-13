# SimulCave/app/main.py

from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.database import Base, engine
from app.routers import auth, cave


def ensure_nrcave_link_columns() -> None:
    inspector = inspect(engine)

    if "caves" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("caves")
    }

    column_definitions = {
        "nrcave_cave_id": "INTEGER",
        "nrcave_site_key": "VARCHAR",
        "nrcave_instance": (
            "VARCHAR DEFAULT 'production'"
        ),
        "nrcave_last_sync_at": (
            "TIMESTAMP"
        ),
        "nrcave_schema_version": "VARCHAR",
    }

    with engine.begin() as connection:
        for column_name, definition in column_definitions.items():
            if column_name in existing_columns:
                continue

            connection.execute(
                text(
                    f"""
                    ALTER TABLE caves
                    ADD COLUMN {column_name} {definition}
                    """
                )
            )

        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS
                ix_caves_nrcave_cave_id
                ON caves (nrcave_cave_id)
                """
            )
        )

        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS
                ix_caves_nrcave_site_key
                ON caves (nrcave_site_key)
                """
            )
        )

        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS
                ix_caves_nrcave_instance
                ON caves (nrcave_instance)
                """
            )
        )

        if engine.dialect.name == "postgresql":
            connection.execute(
                text(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS
                    uq_simulcave_nrcave_project
                    ON caves (
                        nrcave_instance,
                        nrcave_cave_id
                    )
                    WHERE nrcave_cave_id IS NOT NULL
                    """
                )
            )


Base.metadata.create_all(bind=engine)

ensure_nrcave_link_columns()

app = FastAPI(title="SimulCave")

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

app.include_router(auth.router)
app.include_router(cave.router)