import pytest
from unittest.mock import Mock
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

from organizations.models import Organization
from accounts.models import User
from billing.models import Plan, Invoice
from billing.admin import InvoiceAdmin

factory = RequestFactory()


def make_admin_request(user):
    request = factory.post("/admin/billing/invoice/")
    request.user = user
    setattr(request, "session", "session")
    messages = FallbackStorage(request)
    setattr(request, "_messages", messages)
    return request


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.fixture
def admin_user(org):
    return User.objects.create_superuser(email="admin@acme.com", password="pass123", organization=org)


@pytest.fixture
def invoice(org, admin_user):
    plan = Plan.objects.create(name="Pro", slug="pro-admin-test", price_monthly=49)
    return Invoice.objects.create(
        organization=org, invoice_number="INV-TEST01", amount=49,
        status="pending", requested_plan=plan, requested_by=admin_user,
    )


@pytest.mark.django_db
class TestInvoiceAdminApproveAction:
    def test_approve_invoices_crashes_on_missing_utility_function(self, admin_user, invoice):
        """
        Documents a real bug: approve_invoices imports
        create_activated_subscription from billing.utils, which does
        not exist in that module. Clicking 'Approve selected invoices'
        in the Django admin crashes with ImportError instead of
        approving the invoice.
        """
        site = AdminSite()
        admin = InvoiceAdmin(Invoice, site)
        request = make_admin_request(admin_user)
        queryset = Invoice.objects.filter(id=invoice.id)

        with pytest.raises(ImportError):
            admin.approve_invoices(request, queryset)

    def test_reject_invoices_works_correctly(self, admin_user, invoice):
        site = AdminSite()
        admin = InvoiceAdmin(Invoice, site)
        request = make_admin_request(admin_user)
        queryset = Invoice.objects.filter(id=invoice.id)

        admin.reject_invoices(request, queryset)

        invoice.refresh_from_db()
        assert invoice.status == "rejected"