import time
import pytest
from unittest.mock import Mock

from core.circuit_breaker import (
    CircuitBreaker,
    with_circuit_breaker,
    redis_fallback,
    email_fallback,
    webhook_fallback,
    check_circuit_breakers_health,
    reset_all_circuit_breakers,
    redis_circuit_breaker,
    email_circuit_breaker,
    database_circuit_breaker,
)


@pytest.fixture(autouse=True)
def reset_test_circuit():
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()

class TestCircuitBreakerStateTransitions:
    def test_starts_closed(self):
        cb = CircuitBreaker(name="test_closed_1")
        assert cb.get_state() == "CLOSED"
        assert cb.is_open() is False

    def test_opens_after_failure_threshold_reached(self):
        cb = CircuitBreaker(name="test_open_1", failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.get_state() == "OPEN"
        assert cb.is_open() is True

    def test_does_not_open_before_threshold(self):
        cb = CircuitBreaker(name="test_open_2", failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.get_state() == "CLOSED"
        assert cb.is_open() is False

    def test_success_resets_failure_count(self):
        cb = CircuitBreaker(name="test_reset_1", failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.get_failure_count() == 0

    def test_success_closes_open_circuit(self):
        cb = CircuitBreaker(name="test_reset_2", failure_threshold=2)
        cb.record_failure()
        cb.record_failure()
        assert cb.get_state() == "OPEN"

        cb.record_success()
        assert cb.get_state() == "CLOSED"

    def test_recovery_timeout_expiry_reverts_to_closed_not_half_open(self):
        """
        Documents a real design bug: the OPEN state is cached with a TTL
        equal to recovery_timeout, so by the time recovery_timeout elapses,
        the OPEN marker has already expired from cache. get_state() then
        falls back to the CLOSED default instead of ever transitioning
        through HALF_OPEN — meaning the HALF_OPEN path is effectively
        unreachable as currently implemented.
        """
        cb = CircuitBreaker(name="test_halfopen_1", failure_threshold=1, recovery_timeout=1)
        cb.record_failure()
        assert cb.get_state() == "OPEN"

        time.sleep(1.1)
        assert cb.is_open() is False
        assert cb.get_state() == "CLOSED"  
        
    def test_zero_recovery_timeout_prevents_open_state_from_persisting(self):
        """
        Documents a real bug: cache.set(..., timeout=0) causes the OPEN
        state to expire immediately, so a recovery_timeout of 0 makes the
        circuit breaker unable to actually register as OPEN, defeating
        its purpose.
        """
        cb = CircuitBreaker(name="test_zero_timeout_bug", failure_threshold=1, recovery_timeout=0)
        cb.record_failure()
        assert cb.get_state() == "CLOSED"  # should be OPEN, but isn't, due to the bug


class TestCircuitBreakerCall:
    def test_successful_call_returns_result_and_records_success(self):
        cb = CircuitBreaker(name="test_call_1")
        func = Mock(return_value="ok")

        result = cb.call(func, None, "arg1")

        assert result == "ok"
        func.assert_called_once_with("arg1")
        assert cb.get_failure_count() == 0

    def test_failed_call_records_failure_and_reraises_without_fallback(self):
        cb = CircuitBreaker(name="test_call_2", expected_exceptions=(ValueError,))
        func = Mock(side_effect=ValueError("boom"))

        with pytest.raises(ValueError):
            cb.call(func, None)

        assert cb.get_failure_count() == 1

    def test_failed_call_uses_fallback_when_provided(self):
        cb = CircuitBreaker(name="test_call_3", expected_exceptions=(ValueError,))
        func = Mock(side_effect=ValueError("boom"))
        fallback = Mock(return_value="fallback_result")

        result = cb.call(func, fallback)

        assert result == "fallback_result"
        fallback.assert_called_once()

    def test_open_circuit_uses_fallback_without_calling_func(self):
        cb = CircuitBreaker(name="test_call_4", failure_threshold=1)
        cb.record_failure()  # opens the circuit
        assert cb.get_state() == "OPEN"

        func = Mock(return_value="should not be called")
        fallback = Mock(return_value="fallback_used")

        result = cb.call(func, fallback)

        assert result == "fallback_used"
        func.assert_not_called()

    def test_open_circuit_raises_without_fallback(self):
        cb = CircuitBreaker(name="test_call_5", failure_threshold=1)
        cb.record_failure()

        func = Mock()

        with pytest.raises(Exception, match="is OPEN"):
            cb.call(func, None)
        func.assert_not_called()


class TestGetMetrics:
    def test_returns_expected_metric_fields(self):
        cb = CircuitBreaker(name="test_metrics_1")
        metrics = cb.get_metrics()

        assert metrics["name"] == "test_metrics_1"
        assert metrics["state"] == "CLOSED"
        assert metrics["failure_count"] == 0
        assert "failure_threshold" in metrics


class TestWithCircuitBreakerDecorator:
    def test_decorator_passes_through_on_success(self):
        cb = CircuitBreaker(name="test_decorator_1")

        @with_circuit_breaker(cb)
        def my_func(x):
            return x * 2

        assert my_func(5) == 10

    def test_decorator_uses_fallback_on_failure(self):
        cb = CircuitBreaker(name="test_decorator_2", expected_exceptions=(ValueError,))

        @with_circuit_breaker(cb, fallback_func=lambda x: "fallback")
        def my_func(x):
            raise ValueError("fail")

        assert my_func(5) == "fallback"


class TestFallbackFunctions:
    def test_redis_fallback_returns_none(self):
        assert redis_fallback() is None

    def test_email_fallback_returns_queued_status(self):
        result = email_fallback("a@test.com", "subject", "body")
        assert result["status"] == "queued"
        assert result["delivered"] is False

    def test_webhook_fallback_returns_pending_status(self):
        result = webhook_fallback("http://example.com", {"data": 1})
        assert result["status"] == "queued"
        assert result["delivery"] == "pending"


class TestHealthAndReset:
    def test_check_circuit_breakers_health_returns_all_four(self):
        health = check_circuit_breakers_health()
        assert set(health.keys()) == {"redis", "email", "database", "webhook"}

    def test_reset_all_circuit_breakers_closes_them(self):
        redis_circuit_breaker.record_failure()
        reset_all_circuit_breakers()
        assert redis_circuit_breaker.get_state() == "CLOSED"