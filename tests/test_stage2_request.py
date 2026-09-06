import sqlite3
import tempfile
import unittest
from collections.abc import Mapping
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tools.stage2_request import (
    ApprovalEnvelope,
    ApprovalLedger,
    BrokerReceipt,
    ProtectedBroker,
    RequestRefusal,
    Stage2Request,
    Stage2TransportAdapter,
    TransportResult,
    TrustedPrincipal,
    VerifiedApproval,
    plan_request,
)


UTC_NOW = datetime(2026, 9, 6, 12, tzinfo=timezone.utc)


class FakeVerifier:
    def verify(self, envelope):
        return VerifiedApproval(
            envelope=envelope,
            operator=TrustedPrincipal("operator", "op-a"),
            reviewer=TrustedPrincipal("reviewer", "review-a"),
            approved=True,
        )


class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "ledger.sqlite3"
        self.plan = plan_request(Stage2Request(
            method="HEAD", host="www.ris.ripe.net",
            path="/dumps-per-rrc-rest/prototype/",
            selector_start=datetime(2025, 7, 1, tzinfo=timezone.utc),
            selector_end=datetime(2025, 7, 31, tzinfo=timezone.utc),
        ))
        self.envelope = ApprovalEnvelope(
            version=1, request_digest=self.plan.request_digest,
            nonce="nonce-1", issued_at=UTC_NOW,
            not_before=UTC_NOW, expires_at=UTC_NOW + timedelta(seconds=1810),
            max_transport_deadline=timedelta(seconds=1800),
            operator_approval_ref="op-approval", reviewer_approval_ref="review-approval",
            policy_version="policy-1", signature="synthetic-signature",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def broker(self, transport=None, clock=lambda: UTC_NOW, monotonic=lambda: 10.0):
        calls = []
        if transport is None:
            def transport(candidate, timeout_seconds):
                calls.append(candidate)
                return TransportResult("success", False)
        broker = ProtectedBroker(
            ApprovalLedger(self.path), FakeVerifier(), transport,
            clock=clock, monotonic=monotonic,
        )
        return broker, calls

    def test_envelope_canonical_digest_is_stable_and_exact(self):
        self.assertGreater(len(self.envelope.canonical_bytes()), 300)
        self.assertEqual(self.envelope.digest(), self.envelope.digest())
        with self.assertRaises(RequestRefusal):
            ApprovalEnvelope(**{**self.envelope.__dict__, "version": True})

    def test_verifier_result_requires_trusted_distinct_exact_principals(self):
        with self.assertRaises(RequestRefusal):
            VerifiedApproval(self.envelope, "operator", TrustedPrincipal("reviewer", "r"), True)
        with self.assertRaises(RequestRefusal):
            VerifiedApproval(self.envelope, TrustedPrincipal("operator", "same"),
                             TrustedPrincipal("reviewer", "same"), True)
        class EqualPrincipal:
            role = "operator"
            name = "op-a"
            def __eq__(self, other): return True
        with self.assertRaises(RequestRefusal):
            VerifiedApproval(self.envelope, EqualPrincipal(),
                             TrustedPrincipal("reviewer", "review-a"), True)

    def test_ledger_requires_caller_path_and_restarts(self):
        with self.assertRaises(RequestRefusal):
            ApprovalLedger()
        ledger = ApprovalLedger(self.path)
        verified = FakeVerifier().verify(self.envelope)
        ledger.issue(verified)
        self.assertEqual(ApprovalLedger(self.path).status(self.envelope.nonce), "issued")
        with self.assertRaises(RequestRefusal):
            ledger.issue(verified)

    def test_broker_consumes_before_transport_and_at_most_once(self):
        broker, calls = self.broker()
        receipt = broker.execute(self.plan, self.envelope)
        self.assertEqual(receipt, BrokerReceipt("success", False))
        self.assertEqual(len(calls), 1)
        with self.assertRaises(RequestRefusal):
            broker.execute(self.plan, self.envelope)
        self.assertEqual(len(calls), 1)
        self.assertEqual(ApprovalLedger(self.path).status("nonce-1"), "consumed")

    def test_transport_failure_is_bounded_and_still_consumed(self):
        def failing(_, timeout_seconds):
            raise RuntimeError("secret body and URL")
        broker, calls = self.broker(transport=failing)
        self.assertEqual(broker.execute(self.plan, self.envelope), BrokerReceipt("transport-failure", False))
        self.assertEqual(ApprovalLedger(self.path).status("nonce-1"), "consumed")
        self.assertEqual(calls, [])

    def test_invalid_approval_never_consumes_or_transports(self):
        class BadVerifier:
            def verify(self, envelope): return object()
        calls = []
        broker = ProtectedBroker(ApprovalLedger(self.path), BadVerifier(),
                                 lambda _, timeout_seconds: calls.append(1), clock=lambda: UTC_NOW,
                                 monotonic=lambda: 0.0)
        with self.assertRaises(RequestRefusal):
            broker.execute(self.plan, self.envelope)
        self.assertEqual(calls, [])
        self.assertIsNone(ApprovalLedger(self.path).status("nonce-1"))

    def test_invalid_monotonic_clock_refuses_before_ledger_mutation(self):
        invalid_clocks = (
            lambda: float("nan"),
            lambda: float("inf"),
            lambda: True,
            lambda: "clock",
            lambda: object(),
            lambda: (_ for _ in ()).throw(RuntimeError("clock detail")),
        )
        for index, monotonic in enumerate(invalid_clocks):
            with self.subTest(monotonic=monotonic):
                envelope = ApprovalEnvelope(**{**self.envelope.__dict__, "nonce": f"bad-clock-{index}"})
                broker, calls = self.broker(monotonic=monotonic)
                with self.assertRaisesRegex(RequestRefusal, "invalid monotonic clock"):
                    broker.execute(self.plan, envelope)
                self.assertEqual(calls, [])
                self.assertIsNone(ApprovalLedger(self.path).status(envelope.nonce))

    def test_ledger_operations_close_sqlite_connections_on_all_paths(self):
        connections = []
        original_connect = sqlite3.connect

        def connect(*args, **kwargs):
            connection = original_connect(*args, **kwargs)
            connections.append(connection)
            return connection

        with patch("tools.stage2_request.sqlite3.connect", side_effect=connect):
            ledger = ApprovalLedger(self.path)
            verified = FakeVerifier().verify(self.envelope)
            ledger.issue(verified)
            self.assertEqual(ledger.status(self.envelope.nonce), "issued")
            ledger.revoke(self.envelope.nonce)
            with self.assertRaises(RequestRefusal):
                ledger.consume(self.envelope, UTC_NOW)
            with original_connect(self.path) as db:
                db.execute("UPDATE leases SET status='issued' WHERE nonce=?", (self.envelope.nonce,))
                db.execute("UPDATE leases SET deadline_seconds=7 WHERE nonce=?", (self.envelope.nonce,))
            with self.assertRaises(RequestRefusal):
                ledger.consume(self.envelope, UTC_NOW)

        for connection in connections:
            with self.assertRaises(sqlite3.ProgrammingError):
                connection.execute("SELECT 1")

    def test_expiry_not_before_and_safety_margin_refuse_before_consume(self):
        for current, expires, not_before in (
            (UTC_NOW - timedelta(seconds=1), UTC_NOW + timedelta(seconds=1810), UTC_NOW),
            (UTC_NOW + timedelta(seconds=1810), UTC_NOW + timedelta(seconds=1810), UTC_NOW),
            (UTC_NOW, UTC_NOW + timedelta(seconds=1809), UTC_NOW),
            (UTC_NOW, UTC_NOW + timedelta(seconds=1810), UTC_NOW + timedelta(seconds=1)),
        ):
            with self.subTest(current=current):
                envelope = ApprovalEnvelope(**{**self.envelope.__dict__,
                    "expires_at": expires, "not_before": not_before,
                    "nonce": f"n-{current.timestamp()}"})
                broker, calls = self.broker(clock=lambda current=current: current)
                with self.assertRaises(RequestRefusal): broker.execute(self.plan, envelope)
                self.assertEqual(calls, [])
                self.assertIsNone(ApprovalLedger(self.path).status(envelope.nonce))

    def test_revocation_race_and_malformed_row_fail_closed(self):
        broker, calls = self.broker()
        broker.ledger.issue(FakeVerifier().verify(self.envelope))
        broker.ledger.revoke("nonce-1")
        with self.assertRaises(RequestRefusal): broker.execute(self.plan, self.envelope)
        self.assertEqual(calls, [])
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE leases SET deadline_seconds=7 WHERE nonce='nonce-1'")
        with self.assertRaises(RequestRefusal): broker.ledger.consume(self.envelope, UTC_NOW)

    def test_consume_rejects_every_tampered_issued_envelope_field(self):
        ledger = ApprovalLedger(self.path)
        ledger.issue(FakeVerifier().verify(self.envelope))
        fields = ("version", "request_digest", "nonce", "issued_at", "not_before",
                  "expires_at", "max_transport_deadline", "operator_approval_ref",
                  "reviewer_approval_ref", "policy_version", "signature")
        for field in fields:
            with self.subTest(field=field):
                changed = dict(self.envelope.__dict__)
                if field == "version": changed[field] = 2
                elif field == "request_digest": changed[field] = "0" * 64
                elif field == "nonce": changed[field] = "other-nonce"
                elif field == "issued_at": changed[field] = UTC_NOW - timedelta(seconds=1)
                elif field == "not_before": changed[field] = UTC_NOW + timedelta(seconds=1)
                elif field == "expires_at": changed[field] = UTC_NOW + timedelta(seconds=1811)
                elif field == "max_transport_deadline": changed[field] = timedelta(seconds=1799)
                else: changed[field] = "tampered-" + field
                try:
                    tampered = ApprovalEnvelope(**changed)
                except RequestRefusal:
                    continue
                with self.assertRaises(RequestRefusal): ledger.consume(tampered, UTC_NOW)
                with sqlite3.connect(self.path) as db:
                    self.assertEqual(db.execute("SELECT status FROM leases WHERE nonce='nonce-1'").fetchone()[0], "issued")

    def test_consume_rejects_hostile_sqlite_rows_before_mutation(self):
        ledger = ApprovalLedger(self.path)
        ledger.issue(FakeVerifier().verify(self.envelope))
        mutations = {
            "deadline_seconds": 1800.0,
            "issued_us": True,
            "not_before_us": "bad-timestamp",
            "expires_us": -1,
            "request_digest": "not-a-digest",
            "status": "hostile",
            "operator_name": "",
            "reviewer_name": 7,
            "envelope_digest": "not-a-digest",
        }
        for column, value in mutations.items():
            with self.subTest(column=column):
                ledger = ApprovalLedger(self.path)
                with sqlite3.connect(self.path) as db:
                    db.execute(f"UPDATE leases SET {column}=? WHERE nonce='nonce-1'", (value,))
                with self.assertRaises(RequestRefusal): ledger.consume(self.envelope, UTC_NOW)
                with sqlite3.connect(self.path) as db:
                    self.assertEqual(db.execute(f"SELECT {column} FROM leases WHERE nonce='nonce-1'").fetchone()[0],
                                     value)
                    db.execute("UPDATE leases SET request_digest=?, issued_us=?, not_before_us=?, expires_us=?, deadline_seconds=?, status=?, operator_name=?, reviewer_name=?, envelope_digest=? WHERE nonce='nonce-1'",
                               (self.envelope.request_digest, ledger._us(self.envelope.issued_at),
                                ledger._us(self.envelope.not_before), ledger._us(self.envelope.expires_at),
                                1800, "issued", "op-a", "review-a", self.envelope.digest()))

    def test_adapter_accepts_only_exact_status_dict_and_bounded_status(self):
        for result, expected in (({"status": 204}, "success"), ({"status": 404}, "not-found"),
                                 ({"status": 302}, "redirect-rejected"), ({"status": 503}, "transport-failure")):
            self.assertEqual(Stage2TransportAdapter(lambda **_: result)(self.plan).outcome, expected)
        class MappingResult(dict):
            pass
        class HostileMapping(Mapping):
            def __iter__(self): raise RuntimeError("secret")
            def __len__(self): raise RuntimeError("secret")
            def __getitem__(self, key): raise RuntimeError("secret")
        for result in (MappingResult(status=204), HostileMapping(), {"status": True},
                       {"status": 200.0}, {"status": 200, "body": "secret"}, {}):
            with self.subTest(result=type(result).__name__):
                with self.assertRaises(RequestRefusal) as raised:
                    Stage2TransportAdapter(lambda **_: result)(self.plan)
                self.assertEqual(str(raised.exception), "unexpected transport result")

    def test_adapter_maps_raw_transport_exception_to_finite_outcome(self):
        self.assertEqual(Stage2TransportAdapter(lambda **_: (_ for _ in ()).throw(RuntimeError("secret")))(self.plan).outcome,
                         "transport-failure")

    def test_forged_plan_and_envelope_are_revalidated(self):
        broker, calls = self.broker()
        forged_plan = object.__new__(type(self.plan))
        with self.assertRaises(RequestRefusal): broker.execute(forged_plan, self.envelope)
        forged = object.__new__(ApprovalEnvelope)
        with self.assertRaises(RequestRefusal): broker.execute(self.plan, forged)
        self.assertEqual(calls, [])

    def test_noncanonical_transport_result_is_refused_after_consume(self):
        broker, _ = self.broker(transport=lambda _, timeout: {"status": 200})
        self.assertEqual(broker.execute(self.plan, self.envelope), BrokerReceipt("transport-failure", False))
        self.assertEqual(ApprovalLedger(self.path).status("nonce-1"), "consumed")

    def test_concurrent_duplicate_nonce_allows_one_transport_call(self):
        calls = []
        broker, _ = self.broker(transport=lambda _, timeout: calls.append(1) or TransportResult("success", False))
        def run():
            try:
                return broker.execute(self.plan, self.envelope)
            except RequestRefusal:
                return None
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda _: run(), range(6)))
        self.assertEqual(sum(result is not None for result in results), 1)
        self.assertEqual(calls, [1])

    def test_fixed_budget_uses_exactly_two_monotonic_reads(self):
        readings = iter((0.0, 1.0))
        calls = []
        def monotonic():
            try:
                return next(readings)
            except StopIteration:
                raise AssertionError("post-consume monotonic read")
        def transport(plan, timeout_seconds):
            calls.append((plan, timeout_seconds))
            return TransportResult("success", False)
        broker, _ = self.broker(transport=transport, monotonic=monotonic)
        self.assertEqual(broker.execute(self.plan, self.envelope), BrokerReceipt("success", False))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], 1800)

    def test_transport_timeout_is_terminal_and_consumed(self):
        broker, _ = self.broker(transport=lambda plan, timeout: TransportResult("transport-failure", True),
                                monotonic=iter((0.0, 1.0)).__next__)
        self.assertEqual(broker.execute(self.plan, self.envelope), BrokerReceipt("transport-failure", True))
        self.assertEqual(ApprovalLedger(self.path).status("nonce-1"), "consumed")

    def test_transport_exception_is_terminal_and_consumed(self):
        def transport(plan, timeout):
            raise RuntimeError("synthetic transport failure")
        broker, _ = self.broker(transport=transport, monotonic=iter((0.0, 1.0)).__next__)
        self.assertEqual(broker.execute(self.plan, self.envelope), BrokerReceipt("transport-failure", False))
        self.assertEqual(ApprovalLedger(self.path).status("nonce-1"), "consumed")

    def test_malformed_transport_result_is_terminal_and_consumed(self):
        broker, _ = self.broker(transport=lambda plan, timeout: object(),
                                monotonic=iter((0.0, 1.0)).__next__)
        self.assertEqual(broker.execute(self.plan, self.envelope), BrokerReceipt("transport-failure", False))
        self.assertEqual(ApprovalLedger(self.path).status("nonce-1"), "consumed")

    def test_atomic_issue_and_consume_rolls_back_on_database_failure(self):
        ledger = ApprovalLedger(self.path)
        verified = FakeVerifier().verify(self.envelope)
        original = ledger._connect
        class FailingConnection:
            def __init__(self, db): self.db = db
            def __enter__(self): return self
            def __exit__(self, *args): self.db.close()
            def rollback(self): self.db.rollback()
            def close(self): self.db.close()
            def execute(self, sql, params=()):
                if sql == "COMMIT": raise sqlite3.OperationalError("synthetic commit failure")
                return self.db.execute(sql, params)
        ledger._connect = lambda: FailingConnection(original())
        with self.assertRaises(RequestRefusal):
            ledger.issue_and_consume(verified, UTC_NOW)
        self.assertIsNone(ApprovalLedger(self.path).status(self.envelope.nonce))


if __name__ == "__main__":
    unittest.main()
