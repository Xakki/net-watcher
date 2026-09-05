import unittest
from datetime import datetime, timezone

from tools.stage2_request import (
    PROPOSED_EXPIRY,
    RUNTIME_CAPABILITY,
    RequestRefusal,
    RuntimeAuthorization,
    Stage2Request,
    Stage2TransportAdapter,
    plan_request,
)


class Stage2RequestTests(unittest.TestCase):
    def valid_request(self, **changes):
        values = {
            "method": "HEAD",
            "host": "www.ris.ripe.net",
            "path": "/dumps-per-rrc-rest/prototype/",
            "selector_start": datetime(2025, 7, 1, tzinfo=timezone.utc),
            "selector_end": datetime(2025, 7, 31, tzinfo=timezone.utc),
            "allow_redirects": False,
            "read_response_body": False,
        }
        values.update(changes)
        return Stage2Request(**values)

    def test_valid_request_plans_without_execution_by_default(self):
        plan = plan_request(self.valid_request())

        self.assertFalse(plan.execute)
        self.assertEqual(plan.method, "HEAD")
        self.assertEqual(plan.host, "www.ris.ripe.net")
        self.assertEqual(plan.path, "/dumps-per-rrc-rest/prototype/")
        self.assertEqual(plan.evidence["reviewer_role"], "independent-review")
        self.assertEqual(plan.evidence["proposed_expiry"], PROPOSED_EXPIRY)
        self.assertNotIn("url", plan.evidence)
        self.assertNotIn("id", plan.evidence)

    def test_invalid_request_is_refused_without_transport(self):
        for field, value in (
            ("method", "GET"),
            ("host", "ris.ripe.net"),
            ("path", "/other/"),
            ("allow_redirects", True),
            ("read_response_body", True),
            ("selector_end", datetime(2025, 8, 1, 1, tzinfo=timezone.utc)),
        ):
            with self.subTest(field=field):
                with self.assertRaises(RequestRefusal):
                    plan_request(self.valid_request(**{field: value}))

    def test_missing_selector_is_refused_during_planning(self):
        request = self.valid_request(selector_start=None, selector_end=None)

        with self.assertRaisesRegex(RequestRefusal, "selector is required"):
            plan_request(request)


    def test_selector_must_remain_inside_july_2025(self):
        request = self.valid_request(
            selector_start=datetime(2025, 6, 30, 23, tzinfo=timezone.utc),
        )
        with self.assertRaisesRegex(RequestRefusal, "July 2025"):
            plan_request(request)

    def test_full_july_window_is_the_744_hour_limit(self):
        request = self.valid_request(
            selector_start=datetime(2025, 7, 1, tzinfo=timezone.utc),
            selector_end=datetime(2025, 8, 1, tzinfo=timezone.utc),
        )
        plan = plan_request(request)
        self.assertEqual(plan.selector_end, request.selector_end)


    def test_runtime_configuration_matches_user_selected_window_and_capability(self):
        self.assertEqual(PROPOSED_EXPIRY, "2026-09-05T10:17:20Z")
        self.assertEqual(RUNTIME_CAPABILITY, "stage2-head-2026-09-05-60m")

    def test_runtime_authorization_rejects_at_and_after_user_selected_expiry(self):
        expiry = datetime(2026, 9, 5, 10, 17, 20, tzinfo=timezone.utc)
        for current_time in (expiry, expiry.replace(second=21)):
            with self.subTest(current_time=current_time):
                authorization = RuntimeAuthorization(
                    RUNTIME_CAPABILITY, clock=lambda: current_time
                )
                self.assertFalse(authorization.valid)

    def test_runtime_authorization_expires_at_exact_utc_boundary(self):
        expiry = datetime(2026, 9, 5, 10, 17, 20, tzinfo=timezone.utc)
        for current_time, expected_valid in (
            (expiry.replace(second=19), True),
            (expiry, False),
            (expiry.replace(second=21), False),
        ):
            with self.subTest(current_time=current_time):
                authorization = RuntimeAuthorization(
                    RUNTIME_CAPABILITY, clock=lambda: current_time
                )
                self.assertEqual(authorization.valid, expected_valid)



    def test_adapter_passes_canonical_https_head_policy_to_local_fake(self):
        from tools.stage2_request import Stage2TransportAdapter

        plan = plan_request(self.valid_request())
        calls = []

        def local_fake(**kwargs):
            calls.append(kwargs)
            return {"status": 204}

        outcome = Stage2TransportAdapter(local_fake).execute(
            plan,
            authorization=RuntimeAuthorization(
                RUNTIME_CAPABILITY,
                clock=lambda: datetime(2026, 9, 2, 10, 51, 27, tzinfo=timezone.utc),
            ),
        )

        self.assertEqual(outcome, "success")
        self.assertEqual(calls, [{
            "scheme": "https",
            "method": "HEAD",
            "host": "www.ris.ripe.net",
            "path": "/dumps-per-rrc-rest/prototype/",
            "selector_start": datetime(2025, 7, 1, tzinfo=timezone.utc),
            "selector_end": datetime(2025, 7, 31, tzinfo=timezone.utc),
            "allow_redirects": False,
            "proxy": None,
            "cookies": None,
            "automatic_compression": False,
            "read_response_body": False,
            "timeout_seconds": 1800,
        }])

    def test_adapter_rejects_unexpected_fake_result_without_exposing_details(self):
        from tools.stage2_request import Stage2TransportAdapter

        plan = plan_request(self.valid_request())

        def local_fake(**kwargs):
            return {"status": 200, "body": "secret-payload", "headers": {"X": "secret"}}

        with self.assertRaisesRegex(RequestRefusal, "unexpected transport result"):
            Stage2TransportAdapter(local_fake).execute(
                plan,
                authorization=RuntimeAuthorization(
                RUNTIME_CAPABILITY,
                clock=lambda: datetime(2026, 9, 2, 10, 51, 27, tzinfo=timezone.utc),
            ),
            )

    def test_adapter_maps_transport_failures_to_finite_bounded_outcome(self):
        from tools.stage2_request import Stage2TransportAdapter

        plan = plan_request(self.valid_request())

        def local_fake(**kwargs):
            raise RuntimeError("secret host and payload")

        self.assertEqual(
            Stage2TransportAdapter(local_fake).execute(
                plan,
                authorization=RuntimeAuthorization(
                RUNTIME_CAPABILITY,
                clock=lambda: datetime(2026, 9, 2, 10, 51, 27, tzinfo=timezone.utc),
            ),
            ),
            "transport-failure",
        )

    def test_adapter_rejects_mapping_inspection_exception_without_raw_details(self):
        from collections.abc import Mapping

        plan = plan_request(self.valid_request())

        class HostileResult(Mapping):
            def __getitem__(self, key):
                raise RuntimeError("SECRET payload detail")

            def __iter__(self):
                raise RuntimeError("SECRET mapping detail")

            def __len__(self):
                raise RuntimeError("SECRET length detail")

        with self.assertRaises(RequestRefusal) as raised:
            Stage2TransportAdapter(lambda **kwargs: HostileResult()).execute(
                plan,
                authorization=RuntimeAuthorization(
                    RUNTIME_CAPABILITY,
                    clock=lambda: datetime(2026, 9, 2, 10, 51, 27, tzinfo=timezone.utc),
                ),
            )

        self.assertEqual(str(raised.exception), "unexpected transport result")
        self.assertNotIn("SECRET", str(raised.exception))

    def test_adapter_rejects_hand_built_execute_true_plan_before_transport(self):
        valid_plan = plan_request(self.valid_request())
        executable_plan = valid_plan.__class__(
            method=valid_plan.method,
            host=valid_plan.host,
            path=valid_plan.path,
            selector_start=valid_plan.selector_start,
            selector_end=valid_plan.selector_end,
            allow_redirects=valid_plan.allow_redirects,
            read_response_body=valid_plan.read_response_body,
            timeout_seconds=valid_plan.timeout_seconds,
            execute=True,
            evidence=valid_plan.evidence,
        )
        calls = []

        with self.assertRaisesRegex(RequestRefusal, "refused-by-default"):
            Stage2TransportAdapter(lambda **kwargs: calls.append(kwargs)).execute(
                executable_plan,
                authorization=RuntimeAuthorization(
                    RUNTIME_CAPABILITY,
                    clock=lambda: datetime(2026, 9, 2, 10, 51, 27, tzinfo=timezone.utc),
                ),
            )

        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
