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
import stripe
import uuid
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .utils import get_organization_subscription, check_org_limit, sync_org_from_subscription
from .models import Transaction
from .models import Plan, Subscription, Invoice, Transaction, ProcessedWebhookEvent
stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateCheckoutSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        org = request.user.organization
        if not org:
            return Response({"error": "No organization found"}, status=400)
        if not request.user.is_owner:
            return Response({"error": "Only organization owners can upgrade"}, status=403)

        plan = Plan.objects.filter(slug=request.data.get("plan_slug"), is_active=True).first()
        if not plan:
            return Response({"error": "Invalid plan"}, status=400)
        if not plan.stripe_price_id:
            return Response({"error": "Plan not configured for Stripe"}, status=400)

        subscription, created = Subscription.objects.get_or_create(
            organization=org, defaults={"plan": plan, "status": "pending"}
        )
        if not created:
            subscription.plan = plan
            subscription.status = "pending"
            subscription.save(update_fields=["plan", "status"])

        if not subscription.stripe_customer_id:
            customer = stripe.Customer.create(
                email=request.user.email,
                name=org.name,
                metadata={"organization_id": org.id},
            )
            subscription.stripe_customer_id = customer.id
            subscription.save(update_fields=["stripe_customer_id"])

        session = stripe.checkout.Session.create(
            customer=subscription.stripe_customer_id,
            mode="subscription",
            line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
            success_url=settings.FRONTEND_URL + "/billing/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=settings.FRONTEND_URL + "/billing/cancel",
            metadata={"organization_id": org.id, "plan_slug": plan.slug},
        )

        invoice = Invoice.objects.create(
            organization=org,
            subscription=subscription,
            invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
            amount=plan.price_monthly,
            status="pending",
            requested_plan=plan,
            requested_by=request.user,
            notes=f"Stripe checkout initiated for {plan.name}",
        )

        return Response({"checkout_url": session.url, "invoice_id": invoice.id})

@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    permission_classes = []
    authentication_classes = []

   
    def post(self, request):
        try:
            event = stripe.Webhook.construct_event(
                request.body,
                request.META.get("HTTP_STRIPE_SIGNATURE"),
                settings.STRIPE_WEBHOOK_SECRET,
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response(status=400)

        event_id = event.get("id")
        if event_id and ProcessedWebhookEvent.objects.filter(event_id=event_id).exists():
            return Response(status=200)  # already processed, acknowledge and skip

        handler = {
            "checkout.session.completed": self._checkout_completed,
            "invoice.paid": self._invoice_paid,
            "invoice.payment_failed": self._payment_failed,
            "customer.subscription.deleted": self._subscription_deleted,
        }.get(event["type"])
        if handler:
            handler(event["data"]["object"])

        if event_id:
            ProcessedWebhookEvent.objects.create(event_id=event_id, event_type=event["type"])

        return Response(status=200)
    def _checkout_completed(self, data):
            org_id = data["metadata"].get("organization_id")
            plan_slug = data["metadata"].get("plan_slug")
            sub = Subscription.objects.filter(organization_id=org_id).first()
            if not sub:
                return

            plan = Plan.objects.filter(slug=plan_slug).first()
            if plan:
                sub.plan = plan

            sub.stripe_subscription_id = data.get("subscription")
            sub.status = "active"
            sub.save(update_fields=["plan", "stripe_subscription_id", "status"])

            invoice = Invoice.objects.filter(
                organization_id=org_id, status="pending"
            ).order_by("-issue_date").first()
            if invoice:
                invoice.status = "paid"
                invoice.paid_date = timezone.now()
                invoice.save(update_fields=["status", "paid_date"])

            sync_org_from_subscription(sub)
            Transaction.objects.create(
                organization_id=org_id,
                type="subscription",
                amount=(data.get("amount_total") or 0) / 100,
                status="completed",
                stripe_subscription_id=sub.stripe_subscription_id,
                description="Stripe checkout completed",
                completed_at=timezone.now(),
            )

    def _invoice_paid(self, data):
        sub = Subscription.objects.filter(
            stripe_subscription_id=data.get("subscription")
        ).first()
        if not sub:
            return
        period_end = data.get("lines", {}).get("data", [{}])[0].get("period", {}).get("end")
        if period_end:
            sub.current_period_end = timezone.datetime.fromtimestamp(period_end, tz=timezone.utc)
        sub.status = "active"
        sub.save(update_fields=["current_period_end", "status"])
        sync_org_from_subscription(sub)
        Transaction.objects.create(
            organization=sub.organization,
            type="subscription",
            amount=(data.get("amount_paid") or 0) / 100,
            status="completed",
            stripe_subscription_id=sub.stripe_subscription_id,
            description="Monthly renewal",
            completed_at=timezone.now(),
        )

    def _payment_failed(self, data):
        sub = Subscription.objects.filter(
            stripe_subscription_id=data.get("subscription")
        ).first()
        if sub:
            sub.status = "past_due"
            sub.save(update_fields=["status"])
            sync_org_from_subscription(sub)

    def _subscription_deleted(self, data):
        sub = Subscription.objects.filter(stripe_subscription_id=data.get("id")).first()
        if sub:
            sub.status = "canceled"
            sub.canceled_at = timezone.now()
            sub.save(update_fields=["status", "canceled_at"])
            sync_org_from_subscription(sub)

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
            # Γ£à removed billing_email and billing_address ΓÇö not on Invoice model
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
            from .utils import sync_org_from_subscription
            sync_org_from_subscription(subscription)
        
class CancelSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        org = request.user.organization
        if not org:
            return Response({"error": "No organization found"}, status=400)
        if not request.user.is_owner:
            return Response({"error": "Only organization owners can cancel"}, status=403)

        subscription = get_organization_subscription(org)
        if not subscription or not subscription.stripe_subscription_id:
            return Response({"error": "No active Stripe subscription found"}, status=400)

        if subscription.status == "canceled":
            return Response({"error": "Subscription already canceled"}, status=400)

        try:
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True,
            )
        except stripe.error.InvalidRequestError as e:
            return Response({"error": str(e)}, status=400)

        return Response(
            {
                "message": "Subscription will be canceled at the end of the current billing period",
                "current_period_end": subscription.current_period_end,
            }
        )