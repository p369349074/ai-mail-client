from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.mail import AccountAuthType, MailSecurityMode
from app.services.mail_connectivity import MailConnectivityReport, MailConnectivityResult


class MailAccountBase(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    display_name: str | None = Field(default=None, max_length=255)
    provider: str | None = Field(default=None, max_length=64)
    auth_type: AccountAuthType = AccountAuthType.password
    imap_host: str = Field(min_length=1, max_length=255)
    imap_port: int = Field(default=993, ge=1, le=65535)
    imap_security: MailSecurityMode = MailSecurityMode.ssl
    smtp_host: str = Field(min_length=1, max_length=255)
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_security: MailSecurityMode = MailSecurityMode.starttls
    is_active: bool = True

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized:
            raise ValueError("email must contain @")
        return normalized

    @field_validator("imap_host", "smtp_host")
    @classmethod
    def normalize_host(cls, value: str) -> str:
        return value.strip()


class MailAccountCreate(MailAccountBase):
    password: str = Field(min_length=1, max_length=4096)


class MailAccountUpdate(BaseModel):
    email: str | None = Field(default=None, min_length=3, max_length=320)
    display_name: str | None = Field(default=None, max_length=255)
    provider: str | None = Field(default=None, max_length=64)
    auth_type: AccountAuthType | None = None
    password: str | None = Field(default=None, min_length=1, max_length=4096)
    imap_host: str | None = Field(default=None, min_length=1, max_length=255)
    imap_port: int | None = Field(default=None, ge=1, le=65535)
    imap_security: MailSecurityMode | None = None
    smtp_host: str | None = Field(default=None, min_length=1, max_length=255)
    smtp_port: int | None = Field(default=None, ge=1, le=65535)
    smtp_security: MailSecurityMode | None = None
    is_active: bool | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().lower()
        if "@" not in normalized:
            raise ValueError("email must contain @")
        return normalized

    @field_validator("imap_host", "smtp_host")
    @classmethod
    def normalize_host(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value


class MailAccountRead(BaseModel):
    id: int
    email: str
    display_name: str | None
    provider: str | None
    auth_type: str
    imap_host: str | None
    imap_port: int | None
    imap_security: str
    smtp_host: str | None
    smtp_port: int | None
    smtp_security: str
    is_active: bool
    has_secret: bool

    model_config = ConfigDict(from_attributes=True)


class MailFolderRead(BaseModel):
    id: int
    account_id: int
    name: str
    path: str
    delimiter: str | None
    role: str | None

    model_config = ConfigDict(from_attributes=True)


class MailFolderSyncRead(BaseModel):
    account_id: int
    folders: list[MailFolderRead]


class MailAccountConnectivityRequest(MailAccountCreate):
    pass


class ConnectivityResultRead(BaseModel):
    ok: bool
    error: str | None = None

    @classmethod
    def from_result(cls, result: MailConnectivityResult) -> "ConnectivityResultRead":
        return cls(ok=result.ok, error=result.error)


class MailAccountConnectivityRead(BaseModel):
    imap: ConnectivityResultRead
    smtp: ConnectivityResultRead

    @classmethod
    def from_report(cls, report: MailConnectivityReport) -> "MailAccountConnectivityRead":
        return cls(
            imap=ConnectivityResultRead.from_result(report.imap),
            smtp=ConnectivityResultRead.from_result(report.smtp),
        )
