import pytest
from unittest.mock import patch
from django.db.utils import OperationalError
from django.test import RequestFactory, override_settings

from core.health import health_check


factory = RequestFactory()


@pytest.mark.django_db
class TestHealthCheck:

    def test_healthy_when_db_and_cache_up(self):
        request = factory.get("/health/")
        response = health_check(request)

        assert response.status_code == 200
        import json
        data = json.loads(response.content)
        assert data["status"] == "healthy"
        assert data["checks"]["database"] == "up"
        assert data["checks"]["cache"] == "up"

    @patch("core.health.connections")
    def test_unhealthy_when_database_down(self, mock_connections):
        mock_connections.__getitem__.side_effect = OperationalError("db down")

        request = factory.get("/health/")
        response = health_check(request)

        assert response.status_code == 503
        import json
        data = json.loads(response.content)
        assert data["status"] == "unhealthy"
        assert data["checks"]["database"] == "down"

    @patch("core.health.cache")
    def test_unhealthy_when_cache_returns_wrong_value(self, mock_cache):
        mock_cache.get.return_value = "not_ok"

        request = factory.get("/health/")
        response = health_check(request)

        assert response.status_code == 503
        import json
        data = json.loads(response.content)
        assert data["status"] == "unhealthy"
        assert data["checks"]["cache"] == "down"

    @patch("core.health.cache")
    def test_unhealthy_when_cache_raises_exception(self, mock_cache):
        mock_cache.set.side_effect = Exception("cache connection failed")

        request = factory.get("/health/")
        response = health_check(request)

        assert response.status_code == 503
        import json
        data = json.loads(response.content)
        assert data["checks"]["cache"] == "down"

    @override_settings(DEBUG=True)
    def test_no_disk_check_in_debug_mode(self):
        request = factory.get("/health/")
        response = health_check(request)

        import json
        data = json.loads(response.content)
        assert "disk_space" not in data["checks"]

    @override_settings(DEBUG=False)
    def test_disk_check_included_in_production(self):
        request = factory.get("/health/")
        response = health_check(request)

        import json
        data = json.loads(response.content)
        assert "disk_space" in data["checks"]
        assert "free_percent" in data["checks"]["disk_space"]