import unittest
from datetime import datetime, timezone

from tools.stage2_request import (
    PROPOSED_EXPIRY,
    RequestRefusal,
    RuntimeAuthorization,
    Stage2Request,
    execute_head,
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

    def test_missing_selector_is_refused_before_execution_transport(self):
        valid_plan = plan_request(self.valid_request())
        missing_selector_plan = valid_plan.__class__(
            method=valid_plan.method,
            host=valid_plan.host,
            path=valid_plan.path,
            selector_start=None,
            selector_end=None,
            allow_redirects=valid_plan.allow_redirects,
            read_response_body=valid_plan.read_response_body,
            timeout_seconds=valid_plan.timeout_seconds,
            execute=valid_plan.execute,
            evidence=valid_plan.evidence,
        )
        calls = []

        with self.assertRaisesRegex(RequestRefusal, "selector is required"):
            execute_head(
                missing_selector_plan,
                authorization=RuntimeAuthorization("stage2-head-2026-09-02"),
                transport=lambda **kwargs: calls.append(kwargs),
            )

        self.assertEqual(calls, [])

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

    def test_execution_revalidates_hand_constructed_plan_before_transport(self):
        valid_plan = plan_request(self.valid_request())
        malicious_plan = valid_plan.__class__(
            method="GET",
            host="evil.example",
            path="/other/",
            selector_start=valid_plan.selector_start,
            selector_end=valid_plan.selector_end,
            allow_redirects=True,
            read_response_body=True,
            timeout_seconds=1,
            execute=True,
            evidence=valid_plan.evidence,
        )
        calls = []

        with self.assertRaises(RequestRefusal):
            execute_head(
                malicious_plan,
                authorization=RuntimeAuthorization("stage2-head-2026-09-02"),
                transport=lambda **kwargs: calls.append(kwargs),
            )

        self.assertEqual(calls, [])

    def test_execution_requires_explicit_authorization_and_injected_transport(self):
        plan = plan_request(self.valid_request())
        with self.assertRaises(RequestRefusal):
            execute_head(plan)
        with self.assertRaises(RequestRefusal):
            execute_head(plan, authorization=RuntimeAuthorization("wrong"), transport=lambda **kwargs: None)

    def test_runtime_authorization_expires_at_exact_utc_boundary(self):
        expiry = datetime(2026, 9, 2, 10, 51, 28, tzinfo=timezone.utc)
        for current_time, expected_valid in (
            (expiry.replace(second=27), True),
            (expiry, False),
            (expiry.replace(second=29), False),
        ):
            with self.subTest(current_time=current_time):
                authorization = RuntimeAuthorization(
                    "stage2-head-2026-09-02", clock=lambda: current_time
                )
                self.assertEqual(authorization.valid, expected_valid)

    def test_execute_head_refuses_transport_at_and_after_expiry_boundary(self):
        plan = plan_request(self.valid_request())
        expiry = datetime(2026, 9, 2, 10, 51, 28, tzinfo=timezone.utc)
        calls = []

        def local_transport(**kwargs):
            calls.append(kwargs)
            return {"status": 200}

        for current_time, expected_result in (
            (expiry.replace(second=27), {"status": 200}),
            (expiry, RequestRefusal),
            (expiry.replace(second=29), RequestRefusal),
        ):
            with self.subTest(current_time=current_time):
                calls.clear()
                authorization = RuntimeAuthorization(
                    "stage2-head-2026-09-02", clock=lambda: current_time
                )
                if expected_result is RequestRefusal:
                    with self.assertRaises(RequestRefusal):
                        execute_head(
                            plan,
                            authorization=authorization,
                            transport=local_transport,
                        )
                    self.assertEqual(calls, [])
                else:
                    self.assertEqual(
                        execute_head(
                            plan,
                            authorization=authorization,
                            transport=local_transport,
                        ),
                        expected_result,
                    )
                    self.assertEqual(len(calls), 1)

    def test_explicit_transport_receives_head_only_no_redirect_no_body(self):
        plan = plan_request(self.valid_request())
        calls = []

        def local_transport(**kwargs):
            calls.append(kwargs)
            return {"status": 200, "content_length": 0}

        result = execute_head(
            plan,
            authorization=RuntimeAuthorization("stage2-head-2026-09-02"),
            transport=local_transport,
        )

        self.assertEqual(result, {"status": 200, "content_length": 0})
        self.assertEqual(calls, [{
            "method": "HEAD",
            "host": "www.ris.ripe.net",
            "path": "/dumps-per-rrc-rest/prototype/",
            "allow_redirects": False,
            "read_response_body": False,
            "timeout_seconds": 1800,
        }])


if __name__ == "__main__":
    unittest.main()
