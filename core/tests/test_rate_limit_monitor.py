import pytest
from unittest.mock import patch
from django.core.cache import cache

from core.rate_limit_monitor import RateLimitMonitor


@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()
    yield
    cache.clear()


class TestRecordViolation:
    def test_records_violation_with_expected_fields(self):
        monitor = RateLimitMonitor()
        violation = monitor.record_violation(ip="1.2.3.4", endpoint="/api/login/", user_id=7)

        assert violation["ip"] == "1.2.3.4"
        assert violation["endpoint"] == "/api/login/"
        assert violation["user_id"] == 7
        assert "timestamp" in violation

    def test_alert_triggered_when_ip_exceeds_ten_violations(self):
        monitor = RateLimitMonitor()
        with patch.object(RateLimitMonitor, "alert_abuse") as mock_alert:
            for _ in range(11):
                monitor.record_violation(ip="9.9.9.9", endpoint="/api/login/")

        mock_alert.assert_called_once()

    def test_no_alert_under_threshold(self):
        monitor = RateLimitMonitor()
        with patch.object(RateLimitMonitor, "alert_abuse") as mock_alert:
            for _ in range(5):
                monitor.record_violation(ip="8.8.8.8", endpoint="/api/login/")

        mock_alert.assert_not_called()

    def test_alert_abuse_crashes_because_sentry_sdk_is_not_installed(self):
        """
        Documents a real bug: sentry_sdk is imported inside alert_abuse()
        but is not installed in this environment (not in requirements).
        This means any IP that actually exceeds 10 rate-limit violations
        crashes the request with ModuleNotFoundError instead of just
        logging/alerting as intended.
        """
        monitor = RateLimitMonitor()
        with pytest.raises(ModuleNotFoundError):
            monitor.alert_abuse("9.9.9.9", [{"ip": "9.9.9.9"}] * 11)

  

class TestGetViolationsSummary:
    def test_summarizes_violations_by_endpoint(self):
        monitor = RateLimitMonitor()
        monitor.record_violation(ip="1.1.1.1", endpoint="/api/login/")
        monitor.record_violation(ip="1.1.1.1", endpoint="/api/login/")
        monitor.record_violation(ip="2.2.2.2", endpoint="/api/search/")

        summary = monitor.get_violations_summary()

        assert summary["total_violations"] == 3
        assert summary["unique_ips"] == 2
        assert summary["by_endpoint"]["/api/login/"] == 2
        assert summary["by_endpoint"]["/api/search/"] == 1

    def test_empty_summary_when_no_violations(self):
        monitor = RateLimitMonitor()
        summary = monitor.get_violations_summary(date="2020-01-01")

        assert summary["total_violations"] == 0
        assert summary["unique_ips"] == 0


class TestGetTopOffenders:
    def test_returns_top_offenders_sorted_by_count(self):
        monitor = RateLimitMonitor()
        violations = (
            [{"ip": "1.1.1.1"}] * 5
            + [{"ip": "2.2.2.2"}] * 2
            + [{"ip": "3.3.3.3"}] * 8
        )
        top = monitor.get_top_offenders(violations)

        assert top[0]["ip"] == "3.3.3.3"
        assert top[0]["count"] == 8
        assert top[1]["ip"] == "1.1.1.1"

    def test_limits_to_top_five(self):
        monitor = RateLimitMonitor()
        violations = [{"ip": f"1.1.1.{i}"} for i in range(10)]
        top = monitor.get_top_offenders(violations)

        assert len(top) == 5