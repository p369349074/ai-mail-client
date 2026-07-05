"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "mail_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("auth_type", sa.String(length=32), nullable=False),
        sa.Column("encrypted_secret", sa.LargeBinary(), nullable=True),
        sa.Column("imap_host", sa.String(length=255), nullable=True),
        sa.Column("imap_port", sa.Integer(), nullable=True),
        sa.Column("smtp_host", sa.String(length=255), nullable=True),
        sa.Column("smtp_port", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mail_accounts_email"), "mail_accounts", ["email"], unique=False)
    op.create_index(op.f("ix_mail_accounts_user_id"), "mail_accounts", ["user_id"], unique=False)

    op.create_table(
        "mail_folders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("path", sa.String(length=512), nullable=False),
        sa.Column("delimiter", sa.String(length=8), nullable=True),
        sa.Column("uid_validity", sa.BigInteger(), nullable=True),
        sa.Column("role", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["mail_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_id", "path", name="uq_mail_folders_account_path"),
    )
    op.create_index(op.f("ix_mail_folders_account_id"), "mail_folders", ["account_id"], unique=False)

    op.create_table(
        "mail_sync_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("folder_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.String(length=1024), nullable=True),
        sa.Column("scanned_messages", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["mail_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["folder_id"], ["mail_folders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mail_sync_jobs_account_id"), "mail_sync_jobs", ["account_id"], unique=False)
    op.create_index(op.f("ix_mail_sync_jobs_folder_id"), "mail_sync_jobs", ["folder_id"], unique=False)
    op.create_index(op.f("ix_mail_sync_jobs_status"), "mail_sync_jobs", ["status"], unique=False)

    op.create_table(
        "mail_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("folder_id", sa.Integer(), nullable=False),
        sa.Column("imap_uid", sa.BigInteger(), nullable=False),
        sa.Column("uid_validity", sa.BigInteger(), nullable=True),
        sa.Column("message_id", sa.String(length=998), nullable=True),
        sa.Column("thread_id", sa.String(length=255), nullable=True),
        sa.Column("subject", sa.String(length=998), nullable=True),
        sa.Column("snippet", sa.String(length=512), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("is_starred", sa.Boolean(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("flags", sa.JSON(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("headers_cached", sa.Boolean(), nullable=False),
        sa.Column("body_cached", sa.Boolean(), nullable=False),
        sa.Column("has_attachments", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["mail_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["folder_id"], ["mail_folders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("folder_id", "imap_uid", name="uq_mail_messages_folder_uid"),
    )
    op.create_index(op.f("ix_mail_messages_account_id"), "mail_messages", ["account_id"], unique=False)
    op.create_index(op.f("ix_mail_messages_folder_id"), "mail_messages", ["folder_id"], unique=False)
    op.create_index(op.f("ix_mail_messages_message_id"), "mail_messages", ["message_id"], unique=False)
    op.create_index(op.f("ix_mail_messages_received_at"), "mail_messages", ["received_at"], unique=False)
    op.create_index(op.f("ix_mail_messages_sent_at"), "mail_messages", ["sent_at"], unique=False)
    op.create_index(op.f("ix_mail_messages_thread_id"), "mail_messages", ["thread_id"], unique=False)

    op.create_table(
        "ai_reply_drafts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("prompt_hash", sa.String(length=128), nullable=False),
        sa.Column("draft_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["mail_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_reply_drafts_message_id"), "ai_reply_drafts", ["message_id"], unique=False)
    op.create_index(op.f("ix_ai_reply_drafts_prompt_hash"), "ai_reply_drafts", ["prompt_hash"], unique=False)

    op.create_table(
        "ai_summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["mail_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "provider", "model", name="uq_ai_summaries_message_provider_model"),
    )
    op.create_index(op.f("ix_ai_summaries_message_id"), "ai_summaries", ["message_id"], unique=False)

    op.create_table(
        "mail_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=True),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("content_id", sa.String(length=255), nullable=True),
        sa.Column("imap_part_id", sa.String(length=128), nullable=True),
        sa.Column("cache_path", sa.String(length=1024), nullable=True),
        sa.Column("cache_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["mail_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mail_attachments_message_id"), "mail_attachments", ["message_id"], unique=False)

    op.create_table(
        "mail_bodies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("text_body", sa.Text(), nullable=True),
        sa.Column("sanitized_html", sa.Text(), nullable=True),
        sa.Column("raw_size_bytes", sa.Integer(), nullable=True),
        sa.Column("cached_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["mail_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id"),
    )

    op.create_table(
        "mail_recipients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["message_id"], ["mail_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mail_recipients_email"), "mail_recipients", ["email"], unique=False)
    op.create_index(op.f("ix_mail_recipients_kind"), "mail_recipients", ["kind"], unique=False)
    op.create_index(op.f("ix_mail_recipients_message_id"), "mail_recipients", ["message_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_mail_recipients_message_id"), table_name="mail_recipients")
    op.drop_index(op.f("ix_mail_recipients_kind"), table_name="mail_recipients")
    op.drop_index(op.f("ix_mail_recipients_email"), table_name="mail_recipients")
    op.drop_table("mail_recipients")
    op.drop_table("mail_bodies")
    op.drop_index(op.f("ix_mail_attachments_message_id"), table_name="mail_attachments")
    op.drop_table("mail_attachments")
    op.drop_index(op.f("ix_ai_summaries_message_id"), table_name="ai_summaries")
    op.drop_table("ai_summaries")
    op.drop_index(op.f("ix_ai_reply_drafts_prompt_hash"), table_name="ai_reply_drafts")
    op.drop_index(op.f("ix_ai_reply_drafts_message_id"), table_name="ai_reply_drafts")
    op.drop_table("ai_reply_drafts")
    op.drop_index(op.f("ix_mail_messages_thread_id"), table_name="mail_messages")
    op.drop_index(op.f("ix_mail_messages_sent_at"), table_name="mail_messages")
    op.drop_index(op.f("ix_mail_messages_received_at"), table_name="mail_messages")
    op.drop_index(op.f("ix_mail_messages_message_id"), table_name="mail_messages")
    op.drop_index(op.f("ix_mail_messages_folder_id"), table_name="mail_messages")
    op.drop_index(op.f("ix_mail_messages_account_id"), table_name="mail_messages")
    op.drop_table("mail_messages")
    op.drop_index(op.f("ix_mail_sync_jobs_status"), table_name="mail_sync_jobs")
    op.drop_index(op.f("ix_mail_sync_jobs_folder_id"), table_name="mail_sync_jobs")
    op.drop_index(op.f("ix_mail_sync_jobs_account_id"), table_name="mail_sync_jobs")
    op.drop_table("mail_sync_jobs")
    op.drop_index(op.f("ix_mail_folders_account_id"), table_name="mail_folders")
    op.drop_table("mail_folders")
    op.drop_index(op.f("ix_mail_accounts_user_id"), table_name="mail_accounts")
    op.drop_index(op.f("ix_mail_accounts_email"), table_name="mail_accounts")
    op.drop_table("mail_accounts")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
