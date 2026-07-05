from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.mail import MailAccount
from app.models.mail import MailFolder
from app.models.user import User
from app.schemas.accounts import (
    MailAccountConnectivityRead,
    MailAccountConnectivityRequest,
    MailAccountCreate,
    MailAccountRead,
    MailAccountUpdate,
    MailFolderRead,
    MailFolderSyncRead,
)
from app.services.mail_folders import (
    MailFolderSyncError,
    MailFolderSyncService,
    get_mail_folder_sync_service,
)
from app.services.mail_connectivity import (
    MailAccountConnectionConfig,
    MailConnectivityService,
    MailServerConfig,
    get_mail_connectivity_service,
)
from app.services.secrets import SecretEncryptionService, get_secret_encryption_service
from app.services.users import get_or_create_default_user


router = APIRouter(prefix="/accounts", tags=["accounts"])


def _account_read(account: MailAccount) -> MailAccountRead:
    return MailAccountRead(
        id=account.id,
        email=account.email,
        display_name=account.display_name,
        provider=account.provider,
        auth_type=account.auth_type,
        imap_host=account.imap_host,
        imap_port=account.imap_port,
        imap_security=account.imap_security,
        smtp_host=account.smtp_host,
        smtp_port=account.smtp_port,
        smtp_security=account.smtp_security,
        is_active=account.is_active,
        has_secret=account.encrypted_secret is not None,
    )


def _folder_read(folder: MailFolder) -> MailFolderRead:
    return MailFolderRead(
        id=folder.id,
        account_id=folder.account_id,
        name=folder.name,
        path=folder.path,
        delimiter=folder.delimiter,
        role=folder.role,
    )


def _connection_config_from_payload(payload: MailAccountCreate) -> MailAccountConnectionConfig:
    return MailAccountConnectionConfig(
        email=payload.email,
        imap=MailServerConfig(
            host=payload.imap_host,
            port=payload.imap_port,
            security=payload.imap_security,
        ),
        smtp=MailServerConfig(
            host=payload.smtp_host,
            port=payload.smtp_port,
            security=payload.smtp_security,
        ),
    )


def _connection_config_from_account(account: MailAccount) -> MailAccountConnectionConfig:
    if not account.imap_host or not account.imap_port or not account.smtp_host or not account.smtp_port:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mail server settings are incomplete.",
        )
    return MailAccountConnectionConfig(
        email=account.email,
        imap=MailServerConfig(
            host=account.imap_host,
            port=account.imap_port,
            security=account.imap_security,
        ),
        smtp=MailServerConfig(
            host=account.smtp_host,
            port=account.smtp_port,
            security=account.smtp_security,
        ),
    )


def _get_default_user(db: Session) -> User:
    return get_or_create_default_user(db)


def _get_account_for_user(db: Session, user: User, account_id: int) -> MailAccount:
    account = db.get(MailAccount, account_id)
    if account is None or account.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    return account


def _ensure_email_available(db: Session, user: User, email: str, account_id: int | None = None) -> None:
    statement = select(MailAccount).where(MailAccount.user_id == user.id, MailAccount.email == email)
    existing = db.scalar(statement)
    if existing is not None and existing.id != account_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account email already exists.")


@router.get("", response_model=list[MailAccountRead])
def list_accounts(db: Session = Depends(get_db)) -> list[MailAccountRead]:
    user = _get_default_user(db)
    accounts = db.scalars(
        select(MailAccount).where(MailAccount.user_id == user.id).order_by(MailAccount.email, MailAccount.id)
    ).all()
    return [_account_read(account) for account in accounts]


@router.post("", response_model=MailAccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: MailAccountCreate,
    db: Session = Depends(get_db),
    secrets: SecretEncryptionService = Depends(get_secret_encryption_service),
) -> MailAccountRead:
    user = _get_default_user(db)
    _ensure_email_available(db, user, payload.email)

    account = MailAccount(
        user_id=user.id,
        email=payload.email,
        display_name=payload.display_name,
        provider=payload.provider,
        auth_type=payload.auth_type.value,
        encrypted_secret=secrets.encrypt(payload.password),
        imap_host=payload.imap_host,
        imap_port=payload.imap_port,
        imap_security=payload.imap_security.value,
        smtp_host=payload.smtp_host,
        smtp_port=payload.smtp_port,
        smtp_security=payload.smtp_security.value,
        is_active=payload.is_active,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return _account_read(account)


@router.get("/{account_id}", response_model=MailAccountRead)
def get_account(account_id: int, db: Session = Depends(get_db)) -> MailAccountRead:
    user = _get_default_user(db)
    account = _get_account_for_user(db, user, account_id)
    return _account_read(account)


@router.patch("/{account_id}", response_model=MailAccountRead)
def update_account(
    account_id: int,
    payload: MailAccountUpdate,
    db: Session = Depends(get_db),
    secrets: SecretEncryptionService = Depends(get_secret_encryption_service),
) -> MailAccountRead:
    user = _get_default_user(db)
    account = _get_account_for_user(db, user, account_id)
    updates = payload.model_dump(exclude_unset=True)

    new_email = updates.get("email")
    if new_email is not None:
        _ensure_email_available(db, user, new_email, account_id=account.id)

    password = updates.pop("password", None)
    if password is not None:
        account.encrypted_secret = secrets.encrypt(password)

    for key, value in updates.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(account, key, value)

    db.commit()
    db.refresh(account)
    return _account_read(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: int, db: Session = Depends(get_db)) -> Response:
    user = _get_default_user(db)
    account = _get_account_for_user(db, user, account_id)
    db.delete(account)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/test", response_model=MailAccountConnectivityRead)
def test_account_settings(
    payload: MailAccountConnectivityRequest,
    connectivity: MailConnectivityService = Depends(get_mail_connectivity_service),
) -> MailAccountConnectivityRead:
    report = connectivity.test_account(_connection_config_from_payload(payload), payload.password)
    return MailAccountConnectivityRead.from_report(report)


@router.post("/{account_id}/test", response_model=MailAccountConnectivityRead)
def test_saved_account(
    account_id: int,
    db: Session = Depends(get_db),
    connectivity: MailConnectivityService = Depends(get_mail_connectivity_service),
    secrets: SecretEncryptionService = Depends(get_secret_encryption_service),
) -> MailAccountConnectivityRead:
    user = _get_default_user(db)
    account = _get_account_for_user(db, user, account_id)
    if account.encrypted_secret is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account has no stored secret.")

    password = secrets.decrypt(account.encrypted_secret)
    report = connectivity.test_account(_connection_config_from_account(account), password)
    return MailAccountConnectivityRead.from_report(report)


@router.get("/{account_id}/folders", response_model=list[MailFolderRead])
def list_account_folders(account_id: int, db: Session = Depends(get_db)) -> list[MailFolderRead]:
    user = _get_default_user(db)
    account = _get_account_for_user(db, user, account_id)
    folders = db.scalars(
        select(MailFolder)
        .where(MailFolder.account_id == account.id)
        .order_by(MailFolder.role.is_(None), MailFolder.role, MailFolder.path)
    ).all()
    return [_folder_read(folder) for folder in folders]


@router.post("/{account_id}/folders/sync", response_model=MailFolderSyncRead)
def sync_account_folders(
    account_id: int,
    db: Session = Depends(get_db),
    secrets: SecretEncryptionService = Depends(get_secret_encryption_service),
    folder_sync: MailFolderSyncService = Depends(get_mail_folder_sync_service),
) -> MailFolderSyncRead:
    user = _get_default_user(db)
    account = _get_account_for_user(db, user, account_id)
    if account.encrypted_secret is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account has no stored secret.")

    password = secrets.decrypt(account.encrypted_secret)
    try:
        folders = folder_sync.sync_account_folders(db, account, password)
    except MailFolderSyncError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return MailFolderSyncRead(account_id=account.id, folders=[_folder_read(folder) for folder in folders])
