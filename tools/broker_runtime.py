"""Fail-closed configuration boundary for the optional broker profile.

This module deliberately contains no TLS implementation, signer, socket, or
transport default. Containers must inject those capabilities after preflight.
"""

from dataclasses import dataclass
import os
import stat
from typing import Any, Protocol


class BrokerRuntimeError(ValueError):
    """A bounded preflight refusal with no secret-derived details."""


class SecretFiles(Protocol):
    def safe_open(self, path: str) -> int: ...
    def fstat(self, file_descriptor: int) -> os.stat_result: ...
    def read_fd(self, file_descriptor: int) -> bytes: ...
    def close_fd(self, file_descriptor: int) -> None: ...


class ApprovalVerifier(Protocol):
    """Production verifier seam; implementations must verify signed envelopes."""

    def verify(self, envelope: bytes) -> Any: ...


class RealSecretFiles:
    """Acquire and read secret files only through a no-follow descriptor."""

    @staticmethod
    def safe_open(path: str) -> int:
        return os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)

    @staticmethod
    def fstat(file_descriptor: int) -> os.stat_result:
        return os.fstat(file_descriptor)

    @staticmethod
    def read_fd(file_descriptor: int) -> bytes:
        return os.read(file_descriptor, 1_000_001)

    @staticmethod
    def close_fd(file_descriptor: int) -> None:
        os.close(file_descriptor)


_ALLOWED_CLIENT_IDENTITIES = frozenset({"net-watcher-client"})
_SECRET_PATHS = frozenset({
    "/run/secrets/broker_ca",
    "/run/secrets/broker_certificate",
    "/run/secrets/broker_private_key",
    "/run/secrets/approval_verifier",
})

_EXPECTED_SECRET_UID = 1000
_EXPECTED_SECRET_GID = 1000
_EXPECTED_SECRET_MODE = 0o400
_MAX_SECRET_SIZE = 1_000_000


@dataclass(frozen=True)
class RuntimeConfig:
    listen_address: str
    listen_port: int
    database_path: str
    ca_path: str
    certificate_path: str
    private_key_path: str
    verifier_path: str
    client_identity: str

    def __post_init__(self) -> None:
        if type(self.listen_address) is not str or self.listen_address != "broker":
            raise BrokerRuntimeError("broker address is invalid")
        if type(self.listen_port) is not int or self.listen_port != 9443:
            raise BrokerRuntimeError("TLS listener is required")
        if type(self.database_path) is not str or self.database_path != "/var/lib/broker/broker.sqlite3":
            raise BrokerRuntimeError("broker database path is invalid")
        for path in (self.ca_path, self.certificate_path, self.private_key_path, self.verifier_path):
            if type(path) is not str or path not in _SECRET_PATHS:
                raise BrokerRuntimeError("mounted secret path is invalid")
        if type(self.client_identity) is not str or self.client_identity not in _ALLOWED_CLIENT_IDENTITIES:
            raise BrokerRuntimeError("client identity is not approved")
        if len({self.ca_path, self.certificate_path, self.private_key_path, self.verifier_path}) != 4:
            raise BrokerRuntimeError("secret paths must be distinct")

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "RuntimeConfig":
        values = dict(os.environ if env is None else env)
        required = {
            "BROKER_LISTEN_ADDRESS": values.get("BROKER_LISTEN_ADDRESS"),
            "BROKER_LISTEN_PORT": values.get("BROKER_LISTEN_PORT"),
            "BROKER_DATABASE_PATH": values.get("BROKER_DATABASE_PATH"),
            "BROKER_CA_PATH": values.get("BROKER_CA_PATH"),
            "BROKER_CERTIFICATE_PATH": values.get("BROKER_CERTIFICATE_PATH"),
            "BROKER_PRIVATE_KEY_PATH": values.get("BROKER_PRIVATE_KEY_PATH"),
            "BROKER_VERIFIER_PATH": values.get("BROKER_VERIFIER_PATH"),
            "BROKER_CLIENT_IDENTITY": values.get("BROKER_CLIENT_IDENTITY"),
        }
        if any(type(value) is not str or not value for value in required.values()):
            raise BrokerRuntimeError("complete broker runtime configuration is required")
        try:
            port = int(required["BROKER_LISTEN_PORT"])
        except (TypeError, ValueError) as error:
            raise BrokerRuntimeError("broker listener port is invalid") from error
        return cls(
            listen_address=required["BROKER_LISTEN_ADDRESS"],
            listen_port=port,
            database_path=required["BROKER_DATABASE_PATH"],
            ca_path=required["BROKER_CA_PATH"],
            certificate_path=required["BROKER_CERTIFICATE_PATH"],
            private_key_path=required["BROKER_PRIVATE_KEY_PATH"],
            verifier_path=required["BROKER_VERIFIER_PATH"],
            client_identity=required["BROKER_CLIENT_IDENTITY"],
        )


def _read_secret(files: SecretFiles, path: str) -> bytes:
    file_descriptor = None
    try:
        file_descriptor = files.safe_open(path)
        metadata = files.fstat(file_descriptor)
        if type(metadata) is not os.stat_result:
            raise BrokerRuntimeError("secret file metadata is unsafe")
        if (
            type(metadata.st_mode) is not int
            or type(metadata.st_uid) is not int
            or type(metadata.st_gid) is not int
            or type(metadata.st_nlink) is not int
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_uid != _EXPECTED_SECRET_UID
            or metadata.st_gid != _EXPECTED_SECRET_GID
            or stat.S_IMODE(metadata.st_mode) != _EXPECTED_SECRET_MODE
        ):
            raise BrokerRuntimeError("secret file metadata is unsafe")
        data = files.read_fd(file_descriptor)
    except BrokerRuntimeError:
        raise
    except (AttributeError, OSError, TypeError, ValueError) as error:
        raise BrokerRuntimeError("required secret material is unavailable") from error
    finally:
        if file_descriptor is not None:
            try:
                files.close_fd(file_descriptor)
            except (AttributeError, OSError, TypeError, ValueError) as error:
                if not isinstance(error, BrokerRuntimeError):
                    if file_descriptor is not None:
                        raise BrokerRuntimeError("required secret material is unavailable") from error
    if type(data) is not bytes or not data or len(data) > _MAX_SECRET_SIZE:
        raise BrokerRuntimeError("required secret material is malformed")
    return data


def preflight(
    config: RuntimeConfig,
    files: SecretFiles,
    database_factory,
    transport_factory,
    verifier_factory=None,
) -> RuntimeConfig:
    """Validate all static boundaries before opening SQLite or transport."""
    if type(config) is not RuntimeConfig:
        raise BrokerRuntimeError("runtime configuration is required")
    materials = [_read_secret(files, path) for path in (
        config.ca_path, config.certificate_path, config.private_key_path, config.verifier_path,
    )]
    if verifier_factory is None or not callable(verifier_factory):
        raise BrokerRuntimeError("signed approval verifier is not configured")
    try:
        verifier_factory(materials[3])
    except BrokerRuntimeError:
        raise
    except Exception as error:
        raise BrokerRuntimeError("signed approval verifier is unavailable") from error
    if not callable(database_factory) or not callable(transport_factory):
        raise BrokerRuntimeError("runtime dependencies are invalid")
    database_factory()
    transport_factory(materials[0], materials[1], materials[2])
    return config


def main() -> int:
    """Entrypoint guard: fail before any database or transport construction."""
    config = RuntimeConfig.from_env()
    preflight(config, RealSecretFiles(), None, None, None)
    return 0
