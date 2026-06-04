# core/rate_limit_monitor.py
from django.core.cache import cache
import time
import json


class RateLimitMonitor:
    """Monitor rate limit violations and alert"""

    def __init__(self):
        self.violations = []

    def record_violation(self, ip, endpoint, user_id=None):
        """Record a rate limit violation"""
        violation = {
            "ip": ip,
            "endpoint": endpoint,
            "user_id": user_id,
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Store in Redis for monitoring
        cache_key = f"ratelimit_violations:{time.strftime('%Y-%m-%d')}"
        violations = cache.get(cache_key, [])
        violations.append(violation)
        cache.set(cache_key, violations, 86400)  # Keep for 24 hours

        # Alert if too many violations from same IP
        ip_violations = [v for v in violations if v["ip"] == ip]
        if len(ip_violations) > 10:
            self.alert_abuse(ip, ip_violations)

        return violation

    def alert_abuse(self, ip, violations):
        """Send alert for abuse detection"""
        # Log to sentry
        import sentry_sdk

        sentry_sdk.capture_message(
            f"Rate limit abuse detected from IP {ip}: {len(violations)} violations",
            level="warning",
        )

        # Could also send email or webhook here
        print(
            f"🚨 ABUSE DETECTED: IP {ip} exceeded rate limits {len(violations)} times"
        )

    def get_violations_summary(self, date=None):
        """Get violations summary for dashboard"""
        if not date:
            date = time.strftime("%Y-%m-%d")

        cache_key = f"ratelimit_violations:{date}"
        violations = cache.get(cache_key, [])

        # Group by endpoint
        by_endpoint = {}
        for v in violations:
            endpoint = v["endpoint"]
            by_endpoint[endpoint] = by_endpoint.get(endpoint, 0) + 1

        return {
            "total_violations": len(violations),
            "unique_ips": len(set(v["ip"] for v in violations)),
            "by_endpoint": by_endpoint,
            "top_offenders": self.get_top_offenders(violations),
        }

    def get_top_offenders(self, violations):
        """Get top offending IPs"""
        ip_counts = {}
        for v in violations:
            ip_counts[v["ip"]] = ip_counts.get(v["ip"], 0) + 1

        sorted_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"ip": ip, "count": count} for ip, count in sorted_ips[:5]]


rate_limit_monitor = RateLimitMonitor()
