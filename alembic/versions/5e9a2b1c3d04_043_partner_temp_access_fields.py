"""043 partner temporary access governance fields

Revision ID: 5e9a2b1c3d04
Revises: 3f02c8ab7d91
Create Date: 2026-05-04

Añade campos de activación temporal auditable al modelo Partner:
- partner_temp_access_enabled: flag de activación temporal activa
- partner_temp_access_expires_at: fecha/hora de expiración
- partner_temp_access_scope: flags habilitados (onboarding_bypass,portal_access)
- partner_temp_access_reason: justificación (mínimo 20 chars)
- partner_temp_access_ticket: ticket externo de referencia
- partner_temp_access_last_extended_at: última extensión del acceso
- partner_temp_access_last_extended_by: admin que extendió el acceso
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5e9a2b1c3d04"
down_revision: Union[str, Sequence[str], None] = "3f02c8ab7d91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("partners", sa.Column(
        "partner_temp_access_enabled",
        sa.Boolean(),
        nullable=False,
        server_default="false",
    ))
    op.add_column("partners", sa.Column(
        "partner_temp_access_expires_at",
        sa.DateTime(),
        nullable=True,
    ))
    op.add_column("partners", sa.Column(
        "partner_temp_access_scope",
        sa.String(length=100),
        nullable=True,
    ))
    op.add_column("partners", sa.Column(
        "partner_temp_access_reason",
        sa.Text(),
        nullable=True,
    ))
    op.add_column("partners", sa.Column(
        "partner_temp_access_ticket",
        sa.String(length=120),
        nullable=True,
    ))
    op.add_column("partners", sa.Column(
        "partner_temp_access_last_extended_at",
        sa.DateTime(),
        nullable=True,
    ))
    op.add_column("partners", sa.Column(
        "partner_temp_access_last_extended_by",
        sa.String(length=150),
        nullable=True,
    ))


def downgrade() -> None:
    op.drop_column("partners", "partner_temp_access_last_extended_by")
    op.drop_column("partners", "partner_temp_access_last_extended_at")
    op.drop_column("partners", "partner_temp_access_ticket")
    op.drop_column("partners", "partner_temp_access_reason")
    op.drop_column("partners", "partner_temp_access_scope")
    op.drop_column("partners", "partner_temp_access_expires_at")
    op.drop_column("partners", "partner_temp_access_enabled")
