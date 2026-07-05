from dataclasses import dataclass
import base64
import imaplib
import socket

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.mail import MailAccount, MailFolder, MailSecurityMode
from app.services.mail_connectivity import MailServerConfig


@dataclass(frozen=True)
class ImapListedFolder:
    name: str
    path: str
    delimiter: str | None
    attributes: tuple[str, ...]


class MailFolderSyncError(Exception):
    pass


class MailFolderSyncService:
    def __init__(self, timeout_seconds: int | None = None) -> None:
        self.timeout_seconds = timeout_seconds or settings.mail_connect_timeout_seconds

    def sync_account_folders(self, db: Session, account: MailAccount, password: str) -> list[MailFolder]:
        if not account.imap_host or not account.imap_port:
            raise MailFolderSyncError("IMAP settings are incomplete.")

        listed_folders = self.list_remote_folders(
            account.email,
            password,
            MailServerConfig(
                host=account.imap_host,
                port=account.imap_port,
                security=account.imap_security,
            ),
        )
        synced: list[MailFolder] = []
        seen_paths: set[str] = set()
        for listed in listed_folders:
            if listed.path in seen_paths:
                continue
            seen_paths.add(listed.path)
            existing = db.scalar(
                select(MailFolder).where(
                    MailFolder.account_id == account.id,
                    MailFolder.path == listed.path,
                )
            )
            folder = existing or MailFolder(account_id=account.id, path=listed.path)
            folder.name = listed.name
            folder.delimiter = listed.delimiter
            folder.role = infer_folder_role(listed.path, listed.name, listed.attributes)
            db.add(folder)
            synced.append(folder)

        db.commit()
        for folder in synced:
            db.refresh(folder)
        return synced

    def list_remote_folders(
        self,
        username: str,
        password: str,
        server: MailServerConfig,
    ) -> list[ImapListedFolder]:
        client: imaplib.IMAP4 | imaplib.IMAP4_SSL | None = None
        try:
            if server.security == MailSecurityMode.ssl:
                client = imaplib.IMAP4_SSL(server.host, server.port, timeout=self.timeout_seconds)
            else:
                client = imaplib.IMAP4(server.host, server.port, timeout=self.timeout_seconds)
                if server.security == MailSecurityMode.starttls:
                    client.starttls()
            client.login(username, password)
            status, rows = client.list()
            if status != "OK" or rows is None:
                raise MailFolderSyncError("IMAP folder listing failed.")
            return [folder for row in rows if (folder := parse_imap_list_row(row)) is not None]
        except MailFolderSyncError:
            raise
        except Exception as exc:
            raise MailFolderSyncError(_safe_sync_error_message(exc)) from exc
        finally:
            if client is not None:
                try:
                    client.logout()
                except Exception:
                    pass


def parse_imap_list_row(row: bytes | str | object) -> ImapListedFolder | None:
    if not isinstance(row, (bytes, str)):
        return None
    text = row.decode("utf-8", errors="replace") if isinstance(row, bytes) else row
    parser = _ImapListRowParser(text.strip())
    attributes = parser.read_parenthesized_atoms()
    if attributes is None:
        return None
    parser.skip_spaces()
    delimiter = parser.read_nstring()
    if delimiter == "":
        delimiter = None
    parser.skip_spaces()
    path = parser.read_mailbox_name()
    if not path:
        return None
    path = _decode_modified_utf7(path)
    name = path
    if delimiter and delimiter in path:
        name = path.rsplit(delimiter, 1)[-1]
    return ImapListedFolder(name=name, path=path, delimiter=delimiter, attributes=tuple(attributes))


def infer_folder_role(path: str, name: str, attributes: tuple[str, ...]) -> str | None:
    attribute_roles = {
        "\\inbox": "inbox",
        "\\sent": "sent",
        "\\drafts": "drafts",
        "\\trash": "trash",
        "\\archive": "archive",
        "\\all": "archive",
    }
    for attribute in attributes:
        role = attribute_roles.get(attribute.lower())
        if role:
            return role

    candidates = {_normalize_role_text(path), _normalize_role_text(name)}
    if "inbox" in candidates:
        return "inbox"
    if candidates & {"sent", "sent mail", "sent messages"}:
        return "sent"
    if candidates & {"draft", "drafts"}:
        return "drafts"
    if candidates & {"trash", "deleted", "deleted items", "bin"}:
        return "trash"
    if candidates & {"archive", "archives", "all mail"}:
        return "archive"
    return None


def _normalize_role_text(value: str) -> str:
    return value.strip().strip('"').lower().replace("_", " ")


def _decode_modified_utf7(value: str) -> str:
    decoded: list[str] = []
    index = 0
    while index < len(value):
        char = value[index]
        if char != "&":
            decoded.append(char)
            index += 1
            continue

        end = value.find("-", index + 1)
        if end == -1:
            decoded.append(char)
            index += 1
            continue

        token = value[index + 1 : end]
        if token == "":
            decoded.append("&")
        else:
            try:
                payload = token.replace(",", "/")
                payload += "=" * ((4 - len(payload) % 4) % 4)
                decoded.append(base64.b64decode(payload).decode("utf-16-be"))
            except Exception:
                decoded.append(value[index : end + 1])
        index = end + 1
    return "".join(decoded)


class _ImapListRowParser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.index = 0

    def skip_spaces(self) -> None:
        while self.index < len(self.text) and self.text[self.index].isspace():
            self.index += 1

    def read_parenthesized_atoms(self) -> list[str] | None:
        self.skip_spaces()
        if self.index >= len(self.text) or self.text[self.index] != "(":
            return None
        end = self.text.find(")", self.index + 1)
        if end == -1:
            return None
        content = self.text[self.index + 1 : end].strip()
        self.index = end + 1
        return content.split() if content else []

    def read_nstring(self) -> str | None:
        token = self.read_mailbox_name()
        if token is None:
            return None
        return None if token.upper() == "NIL" else token

    def read_mailbox_name(self) -> str | None:
        self.skip_spaces()
        if self.index >= len(self.text):
            return None
        if self.text[self.index] == '"':
            return self.read_quoted()

        start = self.index
        while self.index < len(self.text) and not self.text[self.index].isspace():
            self.index += 1
        token = self.text[start : self.index]
        return token or None

    def read_quoted(self) -> str:
        self.index += 1
        chars: list[str] = []
        while self.index < len(self.text):
            char = self.text[self.index]
            self.index += 1
            if char == "\\" and self.index < len(self.text):
                chars.append(self.text[self.index])
                self.index += 1
                continue
            if char == '"':
                break
            chars.append(char)
        return "".join(chars)


def _safe_sync_error_message(exc: Exception) -> str:
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "Connection timed out."
    if isinstance(exc, imaplib.IMAP4.error):
        return "Authentication failed or the IMAP server rejected the request."
    if isinstance(exc, OSError):
        return "Could not connect to the IMAP server with the saved settings."
    return "Could not sync IMAP folders with the saved settings."


def get_mail_folder_sync_service() -> MailFolderSyncService:
    return MailFolderSyncService()
