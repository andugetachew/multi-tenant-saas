from django.contrib import admin
from .models import Plan, Subscription, Invoice


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "slug",
        "price_monthly",
        "max_projects",
        "max_users",
        "is_active",
    ]
    list_filter = ["is_active"]
    search_fields = ["name"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["organization", "plan", "status", "current_period_end"]
    list_filter = ["status", "plan"]
    search_fields = ["organization__name"]
    readonly_fields = ["current_period_start", "updated_at"]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "invoice_number",
        "organization",
        "amount",
        "status",
        "requested_plan",
        "issue_date",
    ]
    list_filter = ["status", "requested_plan"]
    search_fields = ["invoice_number", "organization__name"]
    readonly_fields = ["issue_date"]

    actions = ["approve_invoices", "reject_invoices"]

    def approve_invoices(self, request, queryset):
        from django.utils import timezone
        from .utils import create_activated_subscription

        for invoice in queryset:
            invoice.status = "approved"
            invoice.approved_by = request.user
            invoice.approved_at = timezone.now()
            invoice.save()

            # Create or update subscription
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

            self.message_user(request, f"Approved invoice {invoice.invoice_number}")

    approve_invoices.short_description = "Approve selected invoices"

    def reject_invoices(self, request, queryset):
        queryset.update(status="rejected")
        self.message_user(request, "Rejected selected invoices")

    reject_invoices.short_description = "Reject selected invoices"
