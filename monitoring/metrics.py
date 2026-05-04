# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
http_request_duration = Histogram(
    "http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"]
)
active_users = Gauge("active_users", "Number of active users")
project_count = Gauge("project_count", "Total number of projects")
task_count = Gauge("task_count", "Total number of tasks")


class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time

        # Record metrics
        http_requests_total.labels(
            method=request.method, endpoint=request.path, status=response.status_code
        ).inc()

        http_request_duration.labels(
            method=request.method, endpoint=request.path
        ).observe(duration)

        # Update gauges
        if request.user.is_authenticated:
            from accounts.models import User
            from projects.models import Project, Task

            active_users.set(User.objects.filter(is_active=True).count())
            project_count.set(Project.objects.count())
            task_count.set(Task.objects.count())

        return response
