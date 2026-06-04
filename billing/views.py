from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Plan, Subscription, Invoice
from .serializers import PlanSerializer, SubscriptionSerializer, InvoiceSerializer
from .utils import get_organization_subscription, check_org_limit
from organizations.utils import check_plan_limit_middleware
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from core.permissions import CanManageBilling, TwoFactorRequired
from organizations.models import Organization


class SubscriptionView(APIView):
    """Subscription management with 2FA requirement"""

    permission_classes = [IsAuthenticated, CanManageBilling, TwoFactorRequired]

    def get(self, request):
        org = request.user.organization
        if not org:
            return Response({"error": "No organization found"}, status=400)

        return Response(
            {
                "plan": org.plan,
                "status": org.subscription_status,
                "max_projects": (
                    5 if org.plan == "trial" else 20 if org.plan == "basic" else 100
                ),
                "max_users": (
                    3 if org.plan == "trial" else 10 if org.plan == "basic" else 50
                ),
            }
        )

    def post(self, request):
        """Upgrade/downgrade subscription"""
        org = request.user.organization
        new_plan = request.data.get("plan")

        if new_plan not in ["trial", "basic", "pro", "enterprise"]:
            return Response({"error": "Invalid plan"}, status=400)

        org.plan = new_plan
        org.save()

        return Response({"message": f"Plan updated to {new_plan}"})


class PlanListView(generics.ListAPIView):
    """List available plans"""

    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAuthenticated]


class CurrentSubscriptionView(APIView):
    """Get current organization subscription"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        subscription = get_organization_subscription(request.user.organization)

        if not subscription:
            return Response(
                {"plan": "Free", "features": {"max_projects": 3, "max_users": 5}}
            )

        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data)


class RequestUpgradeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        org = request.user.organization

        if not request.user.is_owner:
            return Response(
                {"error": "Only organization owners can request upgrades"}, status=403
            )

        plan_slug = request.data.get("plan_slug")

        try:
            plan = Plan.objects.get(slug=plan_slug, is_active=True)
        except Plan.DoesNotExist:
            return Response({"error": "Invalid plan"}, status=400)

        subscription = get_organization_subscription(org)
        if (
            subscription
            and subscription.plan == plan
            and subscription.status == "active"
        ):
            return Response({"error": "Already on this plan"}, status=400)

        import uuid

        invoice = Invoice.objects.create(
            organization=org,
            invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
            amount=plan.price_monthly,
            status="pending",
            requested_plan=plan,
            requested_by=request.user,
            # ✅ removed billing_email and billing_address — not on Invoice model
            notes=f"Plan upgrade request from current plan to {plan.name}",
        )

        return Response(
            {
                "message": "Upgrade request submitted for approval",
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "status": invoice.status,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class AdminApproveUpgradeView(APIView):
    """Admin endpoint to approve/reject upgrade requests"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, invoice_id):
        if not request.user.is_superuser:
            return Response({"error": "Admin access required"}, status=403)

        try:
            invoice = Invoice.objects.get(id=invoice_id)
        except Invoice.DoesNotExist:
            return Response({"error": "Invoice not found"}, status=404)

        action = request.data.get("action")  # 'approve' or 'reject'
        admin_notes = request.data.get("admin_notes", "")

        invoice.admin_notes = admin_notes

        if action == "approve":
            invoice.status = "approved"
            invoice.approved_by = request.user
            invoice.approved_at = timezone.now()
            invoice.save()

            # Activate subscription
            subscription, created = Subscription.objects.get_or_create(
                organization=invoice.organization,
                defaults={
                    "plan": invoice.requested_plan,
                    "status": "active",
                    "billing_email": invoice.billing_email,
                    "billing_address": invoice.billing_address,
                },
            )

            if not created:
                subscription.plan = invoice.requested_plan
                subscription.status = "active"
                subscription.save()

            # Update plan limits
            self.update_org_limits(subscription)

            return Response({"message": "Upgrade approved and activated"})

        elif action == "reject":
            invoice.status = "rejected"
            invoice.save()
            return Response({"message": "Upgrade request rejected"})

        return Response({"error": "Invalid action"}, status=400)

    def update_org_limits(self, subscription):
        """Update organization limits based on plan"""
        plan = subscription.plan
        subscription.max_projects = plan.max_projects
        subscription.max_users = plan.max_users
        subscription.max_storage_mb = plan.max_storage_mb
        subscription.has_real_time_analytics = plan.has_real_time_analytics
        subscription.has_advanced_exports = plan.has_advanced_exports
        subscription.has_priority_support = plan.has_priority_support
        subscription.has_api_access = plan.has_api_access
        subscription.has_audit_logs = plan.has_audit_logs
        subscription.save()
