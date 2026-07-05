from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes.accounts import get_mail_connectivity_service, get_mail_folder_sync_service
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.mail import MailAccount, MailFolder, MailSecurityMode
from app.services.mail_connectivity import (
    MailConnectivityReport,
    MailConnectivityResult,
)


class FakeConnectivityService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str, str]] = []

    def test_account(self, config, password: str) -> MailConnectivityReport:
        self.calls.append((config.email, password, config.imap.host, config.smtp.host))
        return MailConnectivityReport(
            imap=MailConnectivityResult(ok=True),
            smtp=MailConnectivityResult(ok=True),
        )


class FakeFolderSyncService:
    def __init__(self) -> None:
        self.calls: list[tuple[int, str]] = []

    def sync_account_folders(self, db: Session, account: MailAccount, password: str) -> list[MailFolder]:
        self.calls.append((account.id, password))
        folders = [
            MailFolder(
                account_id=account.id,
                name="INBOX",
                path="INBOX",
                delimiter="/",
                role="inbox",
            ),
            MailFolder(
                account_id=account.id,
                name="Sent Mail",
                path="[Gmail]/Sent Mail",
                delimiter="/",
                role="sent",
            ),
        ]
        for folder in folders:
            db.add(folder)
        db.commit()
        for folder in folders:
            db.refresh(folder)
        return folders


@pytest.fixture
def client() -> Generator[
    tuple[TestClient, sessionmaker[Session], FakeConnectivityService, FakeFolderSyncService],
    None,
    None,
]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    fake_connectivity = FakeConnectivityService()
    fake_folder_sync = FakeFolderSyncService()

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_mail_connectivity_service] = lambda: fake_connectivity
    app.dependency_overrides[get_mail_folder_sync_service] = lambda: fake_folder_sync

    try:
        with TestClient(app) as test_client:
            yield test_client, TestingSessionLocal, fake_connectivity, fake_folder_sync
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


def account_payload(**overrides) -> dict:
    payload = {
        "email": "Owner@Example.com",
        "display_name": "Owner",
        "provider": "custom",
        "password": "super-secret",
        "imap_host": "imap.example.com",
        "imap_port": 993,
        "imap_security": "ssl",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_security": "starttls",
    }
    payload.update(overrides)
    return payload


def test_account_crud_does_not_expose_or_store_plaintext_secret(client) -> None:
    test_client, session_factory, _, _ = client

    created = test_client.post("/accounts", json=account_payload())

    assert created.status_code == 201
    body = created.json()
    assert body["email"] == "owner@example.com"
    assert body["has_secret"] is True
    assert "password" not in body
    assert "encrypted_secret" not in body

    account_id = body["id"]
    with session_factory() as db:
        account = db.scalar(select(MailAccount).where(MailAccount.id == account_id))
        assert account is not None
        assert account.encrypted_secret != b"super-secret"

    listed = test_client.get("/accounts")
    assert listed.status_code == 200
    assert [account["id"] for account in listed.json()] == [account_id]

    fetched = test_client.get(f"/accounts/{account_id}")
    assert fetched.status_code == 200
    assert fetched.json()["imap_host"] == "imap.example.com"

    updated = test_client.patch(
        f"/accounts/{account_id}",
        json={
            "display_name": "Updated Owner",
            "password": "new-secret",
            "smtp_security": "ssl",
            "smtp_port": 465,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["display_name"] == "Updated Owner"
    assert updated.json()["smtp_security"] == "ssl"

    deleted = test_client.delete(f"/accounts/{account_id}")
    assert deleted.status_code == 204
    assert test_client.get(f"/accounts/{account_id}").status_code == 404


def test_create_rejects_duplicate_account_email_for_default_user(client) -> None:
    test_client, _, _, _ = client

    assert test_client.post("/accounts", json=account_payload()).status_code == 201
    duplicate = test_client.post("/accounts", json=account_payload(email="owner@example.com"))

    assert duplicate.status_code == 409


def test_unsaved_account_connectivity_uses_payload_and_does_not_persist(client) -> None:
    test_client, _, fake_connectivity, _ = client

    response = test_client.post("/accounts/test", json=account_payload())

    assert response.status_code == 200
    assert response.json() == {
        "imap": {"ok": True, "error": None},
        "smtp": {"ok": True, "error": None},
    }
    assert fake_connectivity.calls == [
        ("owner@example.com", "super-secret", "imap.example.com", "smtp.example.com")
    ]
    assert test_client.get("/accounts").json() == []


def test_saved_account_connectivity_uses_decrypted_secret(client) -> None:
    test_client, _, fake_connectivity, _ = client
    created = test_client.post("/accounts", json=account_payload()).json()

    response = test_client.post(f"/accounts/{created['id']}/test")

    assert response.status_code == 200
    assert fake_connectivity.calls[-1] == (
        "owner@example.com",
        "super-secret",
        "imap.example.com",
        "smtp.example.com",
    )


def test_account_folder_sync_uses_decrypted_secret_and_returns_persisted_folders(client) -> None:
    test_client, _, _, fake_folder_sync = client
    created = test_client.post("/accounts", json=account_payload()).json()

    synced = test_client.post(f"/accounts/{created['id']}/folders/sync")

    assert synced.status_code == 200
    body = synced.json()
    assert body["account_id"] == created["id"]
    assert [folder["path"] for folder in body["folders"]] == ["INBOX", "[Gmail]/Sent Mail"]
    assert fake_folder_sync.calls == [(created["id"], "super-secret")]

    listed = test_client.get(f"/accounts/{created['id']}/folders")
    assert listed.status_code == 200
    assert [folder["role"] for folder in listed.json()] == ["inbox", "sent"]


def test_mail_connectivity_service_uses_stdlib_clients_without_real_network(monkeypatch) -> None:
    from app.services.mail_connectivity import MailAccountConnectionConfig, MailConnectivityService, MailServerConfig

    events: list[str] = []

    class FakeImap:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            events.append(f"imap:{host}:{port}:{timeout}")

        def starttls(self) -> None:
            events.append("imap-starttls")

        def login(self, username: str, password: str) -> None:
            events.append(f"imap-login:{username}:{password}")

        def logout(self) -> None:
            events.append("imap-logout")

    class FakeSmtp:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            events.append(f"smtp:{host}:{port}:{timeout}")

        def ehlo(self) -> None:
            events.append("smtp-ehlo")

        def starttls(self) -> None:
            events.append("smtp-starttls")

        def login(self, username: str, password: str) -> None:
            events.append(f"smtp-login:{username}:{password}")

        def quit(self) -> None:
            events.append("smtp-quit")

    monkeypatch.setattr("app.services.mail_connectivity.imaplib.IMAP4", FakeImap)
    monkeypatch.setattr("app.services.mail_connectivity.smtplib.SMTP", FakeSmtp)

    service = MailConnectivityService(timeout_seconds=3)
    report = service.test_account(
        MailAccountConnectionConfig(
            email="owner@example.com",
            imap=MailServerConfig("imap.example.com", 143, MailSecurityMode.starttls),
            smtp=MailServerConfig("smtp.example.com", 587, MailSecurityMode.starttls),
        ),
        "secret",
    )

    assert report.imap.ok is True
    assert report.smtp.ok is True
    assert events == [
        "imap:imap.example.com:143:3",
        "imap-starttls",
        "imap-login:owner@example.com:secret",
        "imap-logout",
        "smtp:smtp.example.com:587:3",
        "smtp-ehlo",
        "smtp-starttls",
        "smtp-ehlo",
        "smtp-login:owner@example.com:secret",
        "smtp-quit",
    ]


def test_mail_folder_sync_service_uses_stdlib_imap_and_upserts_without_real_network(monkeypatch, client) -> None:
    from app.services.mail_folders import MailFolderSyncService

    _, session_factory, _, _ = client
    events: list[str] = []

    class FakeImap:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            events.append(f"imap:{host}:{port}:{timeout}")

        def starttls(self) -> None:
            events.append("imap-starttls")

        def login(self, username: str, password: str) -> None:
            events.append(f"imap-login:{username}:{password}")

        def list(self):
            events.append("imap-list")
            return "OK", [
                b'(\\HasNoChildren) "/" "INBOX"',
                b'(\\HasNoChildren \\Sent) "/" "[Gmail]/Sent Mail"',
                b'(\\HasNoChildren) "/" "Projects \\"Q1\\""',
            ]

        def logout(self) -> None:
            events.append("imap-logout")

    monkeypatch.setattr("app.services.mail_folders.imaplib.IMAP4", FakeImap)

    with session_factory() as db:
        account = MailAccount(
            user_id=1,
            email="owner@example.com",
            encrypted_secret=b"not-used",
            imap_host="imap.example.com",
            imap_port=143,
            imap_security=MailSecurityMode.starttls.value,
            smtp_host="smtp.example.com",
            smtp_port=587,
        )
        db.add(account)
        db.commit()
        db.refresh(account)

        folders = MailFolderSyncService(timeout_seconds=3).sync_account_folders(db, account, "secret")
        folders_again = MailFolderSyncService(timeout_seconds=3).sync_account_folders(db, account, "secret")

        assert [folder.path for folder in folders] == ["INBOX", "[Gmail]/Sent Mail", 'Projects "Q1"']
        assert [folder.role for folder in folders] == ["inbox", "sent", None]
        assert [folder.id for folder in folders_again] == [folder.id for folder in folders]

    assert events == [
        "imap:imap.example.com:143:3",
        "imap-starttls",
        "imap-login:owner@example.com:secret",
        "imap-list",
        "imap-logout",
        "imap:imap.example.com:143:3",
        "imap-starttls",
        "imap-login:owner@example.com:secret",
        "imap-list",
        "imap-logout",
    ]
