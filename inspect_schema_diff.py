from __future__ import annotations

from sqlalchemy import inspect

from app.db.base import Base
from app.db.session import engine

import app.models  # noqa: F401


def main() -> None:
    inspector = inspect(engine)
    database_tables = set(inspector.get_table_names())
    model_tables = set(Base.metadata.tables.keys())

    print("=== Tables absentes de la base ===")

    missing_tables = sorted(model_tables - database_tables)

    if not missing_tables:
        print("Aucune")
    else:
        for table_name in missing_tables:
            print(f"- {table_name}")

    print()
    print("=== Colonnes absentes par table ===")

    for table_name in sorted(model_tables & database_tables):
        model_columns = set(
            Base.metadata.tables[table_name].columns.keys()
        )

        database_columns = {
            column["name"]
            for column in inspector.get_columns(table_name)
        }

        missing_columns = sorted(
            model_columns - database_columns
        )

        if missing_columns:
            print(f"{table_name} :")

            for column_name in missing_columns:
                print(f"  - {column_name}")


if __name__ == "__main__":
    main()