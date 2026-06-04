from django.test import TestCase, RequestFactory
from django.http import HttpResponse  # ✅ import this
from django.contrib.auth.models import AnonymousUser
from organizations.middleware import TenantMiddleware
from organizations.models import Organization
from accounts.models import User


class TenantMiddlewareTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="middlewareuser@example.com", 
            password="pass123",
            organization=self.org,
        )

    def get_response(self, request): 
        return HttpResponse(status=200)

    def test_middleware_sets_organization(self):
        """Test that middleware sets organization from header"""
        request = self.factory.get("/api/test/")
        request.user = self.user
        request.META["HTTP_X_ORGANIZATION_ID"] = str(self.org.id)  

        middleware = TenantMiddleware(self.get_response)
        middleware(request)

        self.assertEqual(request.organization, self.org)

    def test_middleware_rejects_wrong_organization(self):
        """Test that middleware rejects access to wrong organization"""
        other_org = Organization.objects.create(name="Other Org")

        request = self.factory.get("/api/test/")
        request.user = self.user
        request.META["HTTP_X_ORGANIZATION_ID"] = str(
            other_org.id
        ) 

        middleware = TenantMiddleware(self.get_response)
        response = middleware(request)

        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 403)

    def test_middleware_uses_user_org_fallback(self):
        """Test that middleware falls back to user's organization"""
        request = self.factory.get("/api/test/")
        request.user = self.user
        request.META = {}  

        middleware = TenantMiddleware(self.get_response)
        middleware(request)

        self.assertEqual(request.organization, self.org)
