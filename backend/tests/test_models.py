from app.db.base import Base


def test_expected_tables_are_registered() -> None:
    expected_tables = {
        "ai_reply_drafts",
        "ai_summaries",
        "mail_accounts",
        "mail_attachments",
        "mail_bodies",
        "mail_folders",
        "mail_messages",
        "mail_recipients",
        "mail_sync_jobs",
        "users",
    }

    assert expected_tables.issubset(Base.metadata.tables.keys())
