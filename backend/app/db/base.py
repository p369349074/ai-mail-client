from app.db.session import Base

# Import models so Alembic can discover metadata.
from app.models.ai import AiReplyDraft, AiSummary  # noqa: F401
from app.models.mail import (  # noqa: F401
    MailAccount,
    MailAttachment,
    MailBody,
    MailFolder,
    MailMessage,
    MailRecipient,
    MailSyncJob,
)
from app.models.user import User  # noqa: F401

__all__ = ["Base"]
