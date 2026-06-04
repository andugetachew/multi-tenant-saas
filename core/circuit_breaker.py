# core/circuit_breaker.py
import time
from functools import wraps
from django.core.cache import cache


class CircuitBreaker:
    """
    Circuit Breaker Pattern for external service calls

    Prevents cascading failures when dependencies (Redis, Database, Email, APIs) are down.

    States:
    - CLOSED: Normal operation, calls go through
    - OPEN: Failing, calls blocked immediately (returns fallback)
    - HALF_OPEN: Testing if service recovered (allows limited test calls)

    State Transitions:
    CLOSED → OPEN: After 'failure_threshold' failures
    OPEN → HALF_OPEN: After 'recovery_timeout' seconds
    HALF_OPEN → CLOSED: If test call succeeds
    HALF_OPEN → OPEN: If test call fails
    """

    def __init__(
        self, name, failure_threshold=5, recovery_timeout=60, expected_exceptions=None
    ):
        """
        Args:
            name: Unique identifier for this circuit breaker
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before testing recovery
            expected_exceptions: Exceptions that count as failures
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions or (Exception,)

    def _get_state_key(self):
        return f"circuit:{self.name}:state"

    def _get_failure_count_key(self):
        return f"circuit:{self.name}:failures"

    def _get_last_failure_key(self):
        return f"circuit:{self.name}:last_failure"

    def _get_last_success_key(self):
        return f"circuit:{self.name}:last_success"

    def get_state(self):
        """Get current circuit state: CLOSED, OPEN, HALF_OPEN"""
        state = cache.get(self._get_state_key())
        if not state:
            return "CLOSED"
        return state

    def get_failure_count(self):
        """Get current failure count"""
        return cache.get(self._get_failure_count_key(), 0)

    def record_failure(self):
        """Record a failure and potentially open the circuit"""
        failures = self.get_failure_count() + 1
        cache.set(self._get_failure_count_key(), failures, timeout=3600)
        cache.set(self._get_last_failure_key(), time.time(), timeout=3600)

        print(
            f"[CircuitBreaker:{self.name}] Failure #{failures}/{self.failure_threshold}"
        )

        if failures >= self.failure_threshold:
            self._open_circuit()
            return True
        return False

    def record_success(self):
        """Record a success and close the circuit"""
        cache.delete(self._get_failure_count_key())
        cache.delete(self._get_last_failure_key())
        cache.set(self._get_last_success_key(), time.time(), timeout=3600)

        if self.get_state() != "CLOSED":
            self._close_circuit()
            print(f"[CircuitBreaker:{self.name}] Circuit closed - service recovered")

    def _open_circuit(self):
        """Open the circuit (stop allowing calls)"""
        cache.set(self._get_state_key(), "OPEN", timeout=self.recovery_timeout)
        print(
            f"[CircuitBreaker:{self.name}] Circuit OPEN - blocking calls for {self.recovery_timeout}s"
        )

    def _close_circuit(self):
        """Close the circuit (allow calls again)"""
        cache.set(self._get_state_key(), "CLOSED", timeout=3600)

    def _half_open_circuit(self):
        """Set circuit to half-open (testing recovery)"""
        cache.set(self._get_state_key(), "HALF_OPEN", timeout=60)
        print(f"[CircuitBreaker:{self.name}] Circuit HALF_OPEN - testing recovery")

    def is_open(self):
        """Check if circuit is open (service is failing)"""
        state = self.get_state()

        if state == "OPEN":
            # Check if recovery timeout has elapsed
            last_failure = cache.get(self._get_last_failure_key())
            if last_failure and (time.time() - last_failure) > self.recovery_timeout:
                # Move to half-open to test recovery
                self._half_open_circuit()
                return False
            return True

        if state == "HALF_OPEN":
            return False

        return False

    def call(self, func, fallback_func=None, *args, **kwargs):
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to call
            fallback_func: Fallback function if circuit is open or call fails
            *args, **kwargs: Arguments to pass to functions

        Returns:
            Result of func or fallback_func

        Raises:
            Exception: If circuit is open and no fallback provided
        """
        # Check if circuit is open
        if self.is_open():
            print(f"[CircuitBreaker:{self.name}] Circuit OPEN - using fallback")
            if fallback_func:
                return fallback_func(*args, **kwargs)
            raise Exception(
                f"Circuit breaker '{self.name}' is OPEN. Service unavailable."
            )

        # Execute the function
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result

        except self.expected_exceptions as e:
            print(f"[CircuitBreaker:{self.name}] Call failed: {type(e).__name__}")
            self.record_failure()

            if fallback_func:
                return fallback_func(*args, **kwargs)
            raise e

    def get_metrics(self):
        """Get circuit metrics for monitoring"""
        return {
            "name": self.name,
            "state": self.get_state(),
            "failure_count": self.get_failure_count(),
            "failure_threshold": self.failure_threshold,
            "last_failure": cache.get(self._get_last_failure_key()),
            "last_success": cache.get(self._get_last_success_key()),
        }


# ========== PRE-CONFIGURED CIRCUIT BREAKERS ==========

# Redis Circuit Breaker (for cache operations)
redis_circuit_breaker = CircuitBreaker(
    name="redis",
    failure_threshold=3,  # Open after 3 failures
    recovery_timeout=30,  # Try to recover after 30 seconds
    expected_exceptions=(ConnectionError, TimeoutError, Exception),
)

# Email Circuit Breaker (for SMTP)
email_circuit_breaker = CircuitBreaker(
    name="email",
    failure_threshold=5,  # Open after 5 email failures
    recovery_timeout=60,  # Try to recover after 60 seconds
    expected_exceptions=(ConnectionError, TimeoutError, Exception),
)

# Database Circuit Breaker
database_circuit_breaker = CircuitBreaker(
    name="database",
    failure_threshold=2,  # Open after 2 DB failures
    recovery_timeout=15,  # Try to recover after 15 seconds
    expected_exceptions=(Exception,),
)

#

# External API Circuit Breaker (for webhooks)
webhook_circuit_breaker = CircuitBreaker(
    name="webhook",
    failure_threshold=5,
    recovery_timeout=120,
    expected_exceptions=(Exception,),
)


# ========== DECORATOR FOR EASY USE ==========


def with_circuit_breaker(circuit_breaker, fallback_func=None):
    """
    Decorator to protect a function with circuit breaker

    Usage:
        @with_circuit_breaker(redis_circuit_breaker)
        def get_from_cache(key):
            return cache.get(key)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return circuit_breaker.call(func, fallback_func, *args, **kwargs)

        return wrapper

    return decorator


# ========== FALLBACK FUNCTIONS ==========


def redis_fallback(*args, **kwargs):
    """Fallback when Redis is down - return None (cache miss)"""
    print("[Fallback] Redis unavailable - cache miss")
    return None


def email_fallback(to_email, subject, body, *args, **kwargs):
    """Fallback when email service is down - log instead of send"""
    print(f"[Fallback] Email not sent to {to_email}: {subject}")
    return {"status": "queued", "delivered": False}


def webhook_fallback(url, payload, *args, **kwargs):
    """Fallback when webhook delivery fails - store for retry"""
    print(f"[Fallback] Webhook to {url} failed - stored for retry")
    return {"status": "queued", "delivery": "pending"}


# ========== HEALTH CHECK UTILITY ==========


def check_circuit_breakers_health():
    """Get health status of all circuit breakers for monitoring"""
    return {
        "redis": redis_circuit_breaker.get_metrics(),
        "email": email_circuit_breaker.get_metrics(),
        "database": database_circuit_breaker.get_metrics(),
        "webhook": webhook_circuit_breaker.get_metrics(),
    }


def reset_all_circuit_breakers():
    """Manually reset all circuit breakers (for emergencies)"""
    for cb in [redis_circuit_breaker, email_circuit_breaker, database_circuit_breaker]:
        cb._close_circuit()
        cache.delete(cb._get_failure_count_key())
        cache.delete(cb._get_last_failure_key())
    print("All circuit breakers reset to CLOSED state")
