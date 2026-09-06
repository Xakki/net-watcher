import os
import stat
import importlib.util
import unittest
from unittest.mock import patch
from pathlib import Path

from tools.broker_runtime import (
    BrokerRuntimeError,
    RuntimeConfig,
    _EXPECTED_SECRET_GID,
    _EXPECTED_SECRET_MODE,
    _EXPECTED_SECRET_UID,
    preflight,
)


class FakeSecretFiles:
    def __init__(self, entries):
        self.entries = entries
        self.safe_open_calls = []
        self.fstat_calls = []
        self.read_fd_calls = []
        self.close_fd_calls = []

    def safe_open(self, path):
        self.safe_open_calls.append(path)
        if path not in self.entries:
            raise FileNotFoundError(path)
        return path

    def fstat(self, file_descriptor):
        self.fstat_calls.append(file_descriptor)
        try:
            return self.entries[file_descriptor][0]
        except KeyError as error:
            raise OSError("descriptor unavailable") from error

    def read_fd(self, file_descriptor):
        self.read_fd_calls.append(file_descriptor)
        try:
            return self.entries[file_descriptor][1]
        except KeyError as error:
            raise OSError("descriptor unavailable") from error

    def close_fd(self, file_descriptor):
        self.close_fd_calls.append(file_descriptor)


def metadata(mode=0o400, size=8, uid=1000, gid=1000, file_type=stat.S_IFREG, links=1):
    return os.stat_result((file_type | mode, 0, 0, links, uid, gid, size, 0, 0, 0))


class BrokerRuntimeTests(unittest.TestCase):
    def valid_config(self):
        return RuntimeConfig(
            listen_address="broker",
            listen_port=9443,
            database_path="/var/lib/broker/broker.sqlite3",
            ca_path="/run/secrets/broker_ca",
            certificate_path="/run/secrets/broker_certificate",
            private_key_path="/run/secrets/broker_private_key",
            verifier_path="/run/secrets/approval_verifier",
            client_identity="net-watcher-client",
        )

    def valid_files(self):
        config = self.valid_config()
        return FakeSecretFiles({
            config.ca_path: (metadata(), b"ca"),
            config.certificate_path: (metadata(), b"certificate"),
            config.private_key_path: (metadata(), b"private-key"),
            config.verifier_path: (metadata(), b"public-verifier"),
        })

    def test_preflight_requires_all_secret_material_before_dependencies(self):
        config = self.valid_config()
        with self.assertRaises(BrokerRuntimeError):
            preflight(config, FakeSecretFiles({}), lambda: self.fail("database opened"), lambda: self.fail("transport opened"))

    def test_preflight_rejects_unsafe_secret_metadata(self):
        config = self.valid_config()
        for path in (config.ca_path, config.certificate_path, config.private_key_path, config.verifier_path):
            files = self.valid_files()
            files.entries[path] = (metadata(mode=0o644), b"material")
            with self.subTest(path=path), self.assertRaises(BrokerRuntimeError):
                preflight(config, files, lambda: self.fail("database opened"), lambda: self.fail("transport opened"))

    def test_preflight_rejects_foreign_owner_or_group(self):
        config = self.valid_config()
        for owner_kwargs in ({"uid": 0}, {"gid": 0}):
            files = self.valid_files()
            files.entries[config.ca_path] = (metadata(**owner_kwargs), b"material")
            with self.subTest(owner_kwargs=owner_kwargs), self.assertRaises(BrokerRuntimeError):
                preflight(config, files, lambda: self.fail("database opened"), lambda: self.fail("transport opened"))

    def test_preflight_rejects_symlink_without_reading_unvalidated_path(self):
        config = self.valid_config()
        files = self.valid_files()
        files.entries[config.ca_path] = (metadata(file_type=stat.S_IFLNK), b"target")
        with self.assertRaises(BrokerRuntimeError):
            preflight(config, files, lambda: self.fail("database opened"), lambda: self.fail("transport opened"))
        self.assertEqual(files.safe_open_calls, [config.ca_path])
        self.assertEqual(files.read_fd_calls, [])

    def test_preflight_rejects_non_regular_secret_types(self):
        config = self.valid_config()
        for file_type in (stat.S_IFIFO, stat.S_IFCHR, stat.S_IFBLK, stat.S_IFSOCK, stat.S_IFDIR):
            files = self.valid_files()
            files.entries[config.ca_path] = (metadata(file_type=file_type), b"material")
            with self.subTest(file_type=file_type), self.assertRaises(BrokerRuntimeError):
                preflight(config, files, lambda: self.fail("database opened"), lambda: self.fail("transport opened"))

    def test_preflight_rejects_fake_or_incomplete_metadata(self):
        config = self.valid_config()
        for fake_metadata in (object(), None, {"st_mode": stat.S_IFREG | 0o400}):
            files = self.valid_files()
            files.entries[config.ca_path] = (fake_metadata, b"material")
            with self.subTest(fake_metadata=type(fake_metadata).__name__), self.assertRaises(BrokerRuntimeError):
                preflight(config, files, lambda: self.fail("database opened"), lambda: self.fail("transport opened"))

    def test_preflight_rejects_metadata_lookup_errors_before_dependencies(self):
        config = self.valid_config()

        class BrokenOpenFiles(FakeSecretFiles):
            def safe_open(self, path):
                raise OSError("open unavailable")

        with self.assertRaises(BrokerRuntimeError):
            preflight(config, BrokenOpenFiles({}), lambda: self.fail("database opened"), lambda: self.fail("transport opened"))

    def test_preflight_rejects_unsafe_secret_modes(self):
        config = self.valid_config()
        for mode in (0o000, 0o440, 0o600, 0o401, 0o2400):
            files = self.valid_files()
            files.entries[config.ca_path] = (metadata(mode=mode), b"material")
            with self.subTest(mode=oct(mode)), self.assertRaises(BrokerRuntimeError):
                preflight(config, files, lambda: self.fail("database opened"), lambda: self.fail("transport opened"))

    def test_preflight_rejects_hardlinked_secret(self):
        config = self.valid_config()
        files = self.valid_files()
        files.entries[config.ca_path] = (metadata(links=2), b"material")
        with self.assertRaises(BrokerRuntimeError):
            preflight(config, files, lambda: self.fail("database opened"), lambda: self.fail("transport opened"))

    def test_preflight_reads_only_from_validated_descriptor_after_swap(self):
        config = self.valid_config()
        files = self.valid_files()

        class SwappedFiles(FakeSecretFiles):
            def read_fd(self, file_descriptor):
                self.entries[file_descriptor] = (metadata(), b"replacement")
                return super().read_fd(file_descriptor)

        swapped = SwappedFiles(files.entries)
        preflight(config, swapped, lambda: None, lambda *args: None, lambda material: None)
        self.assertEqual(swapped.read_fd_calls[0], config.ca_path)
        self.assertEqual(swapped.close_fd_calls, [
            config.ca_path,
            config.certificate_path,
            config.private_key_path,
            config.verifier_path,
        ])

    def test_preflight_closes_descriptor_when_fstat_or_read_fails(self):
        config = self.valid_config()

        class BrokenFstatFiles(FakeSecretFiles):
            def fstat(self, file_descriptor):
                raise OSError("fstat unavailable")

        files = BrokenFstatFiles(self.valid_files().entries)
        with self.assertRaises(BrokerRuntimeError):
            preflight(config, files, lambda: self.fail("database opened"), lambda: self.fail("transport opened"))
        self.assertEqual(files.close_fd_calls, [config.ca_path])

        class BrokenReadFiles(FakeSecretFiles):
            def read_fd(self, file_descriptor):
                raise OSError("read unavailable")

        files = BrokenReadFiles(self.valid_files().entries)
        with self.assertRaises(BrokerRuntimeError):
            preflight(config, files, lambda: self.fail("database opened"), lambda: self.fail("transport opened"))
        self.assertEqual(files.close_fd_calls, [config.ca_path])

    def test_preflight_rejects_empty_or_malformed_material(self):
        config = self.valid_config()
        for path in (config.ca_path, config.certificate_path, config.private_key_path, config.verifier_path):
            files = self.valid_files()
            files.entries[path] = (metadata(), b"")
            with self.subTest(path=path), self.assertRaises(BrokerRuntimeError):
                preflight(config, files, lambda: self.fail("database opened"), lambda: self.fail("transport opened"))

    def test_preflight_never_accepts_plaintext_or_arbitrary_client_identity(self):
        config = self.valid_config()
        with self.assertRaises(BrokerRuntimeError):
            preflight(RuntimeConfig(**{**config.__dict__, "listen_port": 8080}), self.valid_files(), lambda: None, lambda: None)
        with self.assertRaises(BrokerRuntimeError):
            preflight(RuntimeConfig(**{**config.__dict__, "client_identity": "arbitrary"}), self.valid_files(), lambda: None, lambda: None)

    def test_valid_preflight_verifies_material_then_allows_dependencies(self):
        calls = []
        config = self.valid_config()
        result = preflight(config, self.valid_files(), lambda: calls.append("db") or object(), lambda *args: calls.append("transport") or object(), lambda material: object())
        self.assertEqual(result, config)
        self.assertEqual(calls, ["db", "transport"])

    def test_entrypoint_adapter_refuses_through_bounded_runtime_error(self):
        entrypoint_path = Path(__file__).parents[1].joinpath("broker-entrypoint.py")
        spec = importlib.util.spec_from_file_location("broker_entrypoint", entrypoint_path)
        if spec is None or spec.loader is None:
            self.fail("entrypoint module could not be loaded")
        entrypoint = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(entrypoint)
        env = {
            "BROKER_LISTEN_ADDRESS": "broker",
            "BROKER_LISTEN_PORT": "9443",
            "BROKER_DATABASE_PATH": "/var/lib/broker/broker.sqlite3",
            "BROKER_CA_PATH": "/run/secrets/broker_ca",
            "BROKER_CERTIFICATE_PATH": "/run/secrets/broker_certificate",
            "BROKER_PRIVATE_KEY_PATH": "/run/secrets/broker_private_key",
            "BROKER_VERIFIER_PATH": "/run/secrets/approval_verifier",
            "BROKER_CLIENT_IDENTITY": "net-watcher-client",
        }
        with patch.dict(os.environ, env, clear=True), self.assertRaises(BrokerRuntimeError) as raised:
            entrypoint.main()
        self.assertNotIn("AttributeError", str(raised.exception))


class ComposeTopologyTests(unittest.TestCase):
    def test_profile_topology_is_internal_and_broker_volume_is_private(self):
        compose = Path(__file__).parents[1].joinpath("compose.yaml").read_text()
        self.assertIn("profiles: [broker]", compose)
        self.assertIn("internal: true", compose)
        self.assertIn("broker_data:", compose)
        self.assertIn("broker_data:/var/lib/broker", compose)
        self.assertNotIn("/var/run/docker.sock", compose)
        self.assertNotIn("privileged: true", compose)
        self.assertIn("cap_drop:", compose)
        self.assertIn("no-new-privileges:true", compose)
        self.assertIn("external: true", compose)
        self.assertNotIn("ports:\n      - \"9443", compose)

    def test_runtime_users_and_secret_mount_policy_are_static_and_consistent(self):
        root = Path(__file__).parents[1]
        broker_dockerfile = root.joinpath("Dockerfile.broker").read_text()
        client_dockerfile = root.joinpath("Dockerfile.client").read_text()
        compose = root.joinpath("compose.yaml").read_text()
        self.assertIn("addgroup -S -g 1000 broker", broker_dockerfile)
        self.assertIn("adduser -S -D -u 1000 -G broker broker", broker_dockerfile)
        self.assertIn("addgroup -S -g 1000 client", client_dockerfile)
        self.assertIn("adduser -S -D -u 1000 -G client client", client_dockerfile)
        self.assertEqual(compose.count('user: "1000:1000"'), 2)
        self.assertGreaterEqual(compose.count('uid: "1000"'), 7)
        self.assertGreaterEqual(compose.count('gid: "1000"'), 7)
        self.assertGreaterEqual(compose.count("mode: 0400"), 7)
        self.assertEqual((_EXPECTED_SECRET_UID, _EXPECTED_SECRET_GID, _EXPECTED_SECRET_MODE), (1000, 1000, 0o400))


if __name__ == "__main__":
    unittest.main()
