from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class AccountAuthType(StrEnum):
    password = "password"
    oauth = "oauth"


class MailSecurityMode(StrEnum):
    ssl = "ssl"
    starttls = "starttls"
    none = "none"


class RecipientKind(StrEnum):
    from_ = "from"
    to = "to"
    cc = "cc"
    bcc = "bcc"
    reply_to = "reply_to"


class SyncJobStatus(StrEnum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    paused = "paused"


class MailAccount(Base):
    __tablename__ = "mail_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    provider: Mapped[str | None] = mapped_column(String(64))
    auth_type: Mapped[str] = mapped_column(String(32), default=AccountAuthType.password.value)
    encrypted_secret: Mapped[bytes | None] = mapped_column(LargeBinary)
    imap_host: Mapped[str | None] = mapped_column(String(255))
    imap_port: Mapped[int | None] = mapped_column(Integer)
    imap_security: Mapped[str] = mapped_column(String(32), default=MailSecurityMode.ssl.value)
    smtp_host: Mapped[str | None] = mapped_column(String(255))
    smtp_port: Mapped[int | None] = mapped_column(Integer)
    smtp_security: Mapped[str] = mapped_column(String(32), default=MailSecurityMode.starttls.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="mail_accounts")
    folders: Mapped[list["MailFolder"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    sync_jobs: Mapped[list["MailSyncJob"]] = relationship(back_populates="account", cascade="all, delete-orphan")


class MailFolder(Base):
    __tablename__ = "mail_folders"
    __table_args__ = (
        UniqueConstraint("account_id", "path", name="uq_mail_folders_account_path"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("mail_accounts.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(String(512))
    delimiter: Mapped[str | None] = mapped_column(String(8))
    uid_validity: Mapped[int | None] = mapped_column(BigInteger)
    role: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    account: Mapped["MailAccount"] = relationship(back_populates="folders")
    messages: Mapped[list["MailMessage"]] = relationship(back_populates="folder", cascade="all, delete-orphan")


class MailMessage(Base):
    __tablename__ = "mail_messages"
    __table_args__ = (
        UniqueConstraint("folder_id", "imap_uid", name="uq_mail_messages_folder_uid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("mail_accounts.id", ondelete="CASCADE"), index=True)
    folder_id: Mapped[int] = mapped_column(ForeignKey("mail_folders.id", ondelete="CASCADE"), index=True)
    imap_uid: Mapped[int] = mapped_column(BigInteger)
    uid_validity: Mapped[int | None] = mapped_column(BigInteger)
    message_id: Mapped[str | None] = mapped_column(String(998), index=True)
    thread_id: Mapped[str | None] = mapped_column(String(255), index=True)
    subject: Mapped[str | None] = mapped_column(String(998))
    snippet: Mapped[str | None] = mapped_column(String(512))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    flags: Mapped[dict | None] = mapped_column(JSON)
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    headers_cached: Mapped[bool] = mapped_column(Boolean, default=True)
    body_cached: Mapped[bool] = mapped_column(Boolean, default=False)
    has_attachments: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    folder: Mapped["MailFolder"] = relationship(back_populates="messages")
    recipients: Mapped[list["MailRecipient"]] = relationship(back_populates="message", cascade="all, delete-orphan")
    body: Mapped["MailBody | None"] = relationship(back_populates="message", cascade="all, delete-orphan")
    attachments: Mapped[list["MailAttachment"]] = relationship(back_populates="message", cascade="all, delete-orphan")


class MailRecipient(Base):
    __tablename__ = "mail_recipients"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("mail_messages.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(32), index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    display_name: Mapped[str | None] = mapped_column(String(255))

    message: Mapped["MailMessage"] = relationship(back_populates="recipients")


class MailBody(Base):
    __tablename__ = "mail_bodies"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("mail_messages.id", ondelete="CASCADE"), unique=True)
    text_body: Mapped[str | None] = mapped_column(Text)
    sanitized_html: Mapped[str | None] = mapped_column(Text)
    raw_size_bytes: Mapped[int | None] = mapped_column(Integer)
    cached_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    message: Mapped["MailMessage"] = relationship(back_populates="body")


class MailAttachment(Base):
    __tablename__ = "mail_attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("mail_messages.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str | None] = mapped_column(String(512))
    content_type: Mapped[str | None] = mapped_column(String(255))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    content_id: Mapped[str | None] = mapped_column(String(255))
    imap_part_id: Mapped[str | None] = mapped_column(String(128))
    cache_path: Mapped[str | None] = mapped_column(String(1024))
    cache_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    message: Mapped["MailMessage"] = relationship(back_populates="attachments")


class MailSyncJob(Base):
    __tablename__ = "mail_sync_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("mail_accounts.id", ondelete="CASCADE"), index=True)
    folder_id: Mapped[int | None] = mapped_column(ForeignKey("mail_folders.id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String(32), default=SyncJobStatus.pending.value, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(String(1024))
    scanned_messages: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    account: Mapped["MailAccount"] = relationship(back_populates="sync_jobs")
