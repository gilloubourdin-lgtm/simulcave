"""align existing simulcave schema

Revision ID: 060eb559e7d4
Revises: 
Create Date: 2026-07-16 09:44:50.439099

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from app.db.base import Base
from collections.abc import Sequence
from typing import Union

# Enregistre les tables dans Base.metadata.
import app.models  # noqa: F401


# revision identifiers, used by Alembic.
revision = "060eb559e7d4"
down_revision = None
branch_labels = None
depends_on = None


def _table_names() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return set(inspector.get_table_names())


def _column_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())

    if table_name not in inspector.get_table_names():
        return set()

    return {
        column["name"]
        for column in inspector.get_columns(table_name)
    }


def _index_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())

    if table_name not in inspector.get_table_names():
        return set()

    return {
        index["name"]
        for index in inspector.get_indexes(table_name)
        if index.get("name")
    }


def _create_missing_tables() -> None:
    bind = op.get_bind()
    existing = _table_names()

    # Ordre important en raison des clés étrangères.
    table_order = [
        "users",
        "weather_data",
        "renovation_scenarios",
        "zone_monthly_targets",
    ]

    for table_name in table_order:
        if table_name in existing:
            continue

        table = Base.metadata.tables[table_name]
        table.create(
            bind=bind,
            checkfirst=True,
        )

        existing.add(table_name)


def _add_missing_cave_columns() -> None:
    existing = _column_names("caves")

    columns = {
        "user_id": sa.Column(
            "user_id",
            sa.Integer(),
            nullable=True,
        ),
        "address": sa.Column(
            "address",
            sa.String(),
            nullable=True,
        ),
        "latitude": sa.Column(
            "latitude",
            sa.Float(),
            nullable=True,
        ),
        "longitude": sa.Column(
            "longitude",
            sa.Float(),
            nullable=True,
        ),
        "use_dynamic_weather": sa.Column(
            "use_dynamic_weather",
            sa.Boolean(),
            nullable=True,
            server_default=sa.false(),
        ),
        "altitude_m": sa.Column(
            "altitude_m",
            sa.Float(),
            nullable=True,
            server_default=sa.text("500"),
        ),
        "ventilation_rate_ach": sa.Column(
            "ventilation_rate_ach",
            sa.Float(),
            nullable=True,
            server_default=sa.text("0.2"),
        ),
        "ventilation_enabled": sa.Column(
            "ventilation_enabled",
            sa.Boolean(),
            nullable=True,
            server_default=sa.true(),
        ),
        "energy_source": sa.Column(
            "energy_source",
            sa.String(),
            nullable=True,
            server_default=sa.text("'electricity'"),
        ),
        "energy_price_chf_per_kwh": sa.Column(
            "energy_price_chf_per_kwh",
            sa.Float(),
            nullable=True,
            server_default=sa.text("0.24"),
        ),
        "co2_factor_kg_per_kwh": sa.Column(
            "co2_factor_kg_per_kwh",
            sa.Float(),
            nullable=True,
            server_default=sa.text("0.09"),
        ),
        "nrcave_cave_id": sa.Column(
            "nrcave_cave_id",
            sa.Integer(),
            nullable=True,
        ),
        "nrcave_site_key": sa.Column(
            "nrcave_site_key",
            sa.String(),
            nullable=True,
        ),
        "nrcave_instance": sa.Column(
            "nrcave_instance",
            sa.String(),
            nullable=True,
            server_default=sa.text("'production'"),
        ),
        "nrcave_last_sync_at": sa.Column(
            "nrcave_last_sync_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        "nrcave_schema_version": sa.Column(
            "nrcave_schema_version",
            sa.String(),
            nullable=True,
        ),
    }

    missing = [
        column
        for name, column in columns.items()
        if name not in existing
    ]

    if not missing:
        return

    # Le mode batch permet également la migration SQLite.
    with op.batch_alter_table(
        "caves",
        schema=None,
    ) as batch_op:
        for column in missing:
            batch_op.add_column(column)


def _add_missing_wall_columns() -> None:
    existing = _column_names("walls")

    columns = {
        "thickness_m": sa.Column(
            "thickness_m",
            sa.Float(),
            nullable=True,
            server_default=sa.text("0.40"),
        ),
        "inertia_factor": sa.Column(
            "inertia_factor",
            sa.Float(),
            nullable=True,
            server_default=sa.text("1.0"),
        ),
    }

    missing = [
        column
        for name, column in columns.items()
        if name not in existing
    ]

    if not missing:
        return

    with op.batch_alter_table(
        "walls",
        schema=None,
    ) as batch_op:
        for column in missing:
            batch_op.add_column(column)


def _add_missing_zone_columns() -> None:
    existing = _column_names("zones")

    columns = {
        "x_m": sa.Column(
            "x_m",
            sa.Float(),
            nullable=True,
            server_default=sa.text("0"),
        ),
        "y_m": sa.Column(
            "y_m",
            sa.Float(),
            nullable=True,
            server_default=sa.text("0"),
        ),
        "width_m": sa.Column(
            "width_m",
            sa.Float(),
            nullable=True,
            server_default=sa.text("1"),
        ),
        "length_m": sa.Column(
            "length_m",
            sa.Float(),
            nullable=True,
            server_default=sa.text("1"),
        ),
        "level_index": sa.Column(
            "level_index",
            sa.Integer(),
            nullable=True,
            server_default=sa.text("0"),
        ),
        "level_name": sa.Column(
            "level_name",
            sa.String(),
            nullable=True,
            server_default=sa.text("'Rez'"),
        ),
        "floor_depth_m": sa.Column(
            "floor_depth_m",
            sa.Float(),
            nullable=True,
            server_default=sa.text("0"),
        ),
        "process_heating_start_month": sa.Column(
            "process_heating_start_month",
            sa.Integer(),
            nullable=True,
            server_default=sa.text("1"),
        ),
        "process_heating_end_month": sa.Column(
            "process_heating_end_month",
            sa.Integer(),
            nullable=True,
            server_default=sa.text("12"),
        ),
        "process_cooling_start_month": sa.Column(
            "process_cooling_start_month",
            sa.Integer(),
            nullable=True,
            server_default=sa.text("1"),
        ),
        "process_cooling_end_month": sa.Column(
            "process_cooling_end_month",
            sa.Integer(),
            nullable=True,
            server_default=sa.text("12"),
        ),
    }

    missing = [
        column
        for name, column in columns.items()
        if name not in existing
    ]

    if not missing:
        return

    with op.batch_alter_table(
        "zones",
        schema=None,
    ) as batch_op:
        for column in missing:
            batch_op.add_column(column)


def _create_missing_cave_indexes() -> None:
    existing = _index_names("caves")

    if "ix_caves_nrcave_cave_id" not in existing:
        op.create_index(
            "ix_caves_nrcave_cave_id",
            "caves",
            ["nrcave_cave_id"],
            unique=False,
        )

    if "ix_caves_nrcave_site_key" not in existing:
        op.create_index(
            "ix_caves_nrcave_site_key",
            "caves",
            ["nrcave_site_key"],
            unique=False,
        )

    if "ix_caves_nrcave_instance" not in existing:
        op.create_index(
            "ix_caves_nrcave_instance",
            "caves",
            ["nrcave_instance"],
            unique=False,
        )

    if "uq_simulcave_nrcave_project" not in existing:
        op.create_index(
            "uq_simulcave_nrcave_project",
            "caves",
            [
                "nrcave_instance",
                "nrcave_cave_id",
            ],
            unique=True,
            postgresql_where=sa.text(
                "nrcave_cave_id IS NOT NULL"
            ),
            sqlite_where=sa.text(
                "nrcave_cave_id IS NOT NULL"
            ),
        )


def upgrade() -> None:
    _create_missing_tables()
    _add_missing_cave_columns()
    _add_missing_wall_columns()
    _add_missing_zone_columns()
    _create_missing_cave_indexes()


def downgrade() -> None:
    """
    Migration d’alignement non destructive.

    Les objets pouvaient exister avant l’arrivée d’Alembic,
    particulièrement sur PostgreSQL Render. Un downgrade
    automatique pourrait donc supprimer des données ou des
    structures historiques qui ne viennent pas de cette révision.
    """
    pass
