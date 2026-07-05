"""add mail account security modes

Revision ID: 0002_mail_account_security_modes
Revises: 0001_initial_schema
Create Date: 2026-07-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_mail_account_security_modes"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "mail_accounts",
        sa.Column("imap_security", sa.String(length=32), server_default="ssl", nullable=False),
    )
    op.add_column(
        "mail_accounts",
        sa.Column("smtp_security", sa.String(length=32), server_default="starttls", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("mail_accounts", "smtp_security")
    op.drop_column("mail_accounts", "imap_security")
