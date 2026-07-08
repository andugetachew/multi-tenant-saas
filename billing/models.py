from django.db import models
from organizations.models import Organization


class Plan(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Feature limits
    max_projects = models.IntegerField(default=3)
    max_users = models.IntegerField(default=5)
    max_storage_mb = models.IntegerField(default=100)
    has_real_time_analytics = models.BooleanField(default=False)
    has_advanced_exports = models.BooleanField(default=False)
    has_priority_support = models.BooleanField(default=False)
    has_api_access = models.BooleanField(default=False)
    has_audit_logs = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ["price_monthly"]

    def __str__(self):
        return f"{self.name} - ${self.price_monthly}/month"


class Subscription(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending Approval"),
        ("active", "Active"),
        ("past_due", "Past Due"),
        ("canceled", "Canceled"),
        ("expired", "Expired"),
    ]

    organization = models.OneToOneField(
        Organization, on_delete=models.CASCADE, related_name="subscription"
    )
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Billing info
    billing_email = models.EmailField(blank=True)
    billing_address = models.TextField(blank=True)

    # Dates
    current_period_start = models.DateTimeField(auto_now_add=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    # Features enabled (cached from plan)
    max_projects = models.IntegerField(default=3)
    max_users = models.IntegerField(default=5)
    max_storage_mb = models.IntegerField(default=100)
    has_real_time_analytics = models.BooleanField(default=False)
    has_advanced_exports = models.BooleanField(default=False)
    has_priority_support = models.BooleanField(default=False)
    has_api_access = models.BooleanField(default=False)
    has_audit_logs = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return (
            f"{self.organization.name} - {self.plan.name if self.plan else 'No Plan'}"
        )


class Invoice(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending", "Pending Payment"),
        ("paid", "Paid"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="invoices"
    )
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True)

    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Request details
    requested_plan = models.ForeignKey(
        Plan, on_delete=models.SET_NULL, null=True, related_name="requests"
    )
    requested_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True
    )
    approved_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="approved_invoices",
    )

    # Dates
    issue_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    paid_date = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.invoice_number} - {self.organization.name} - {self.status}"


class FeatureFlag(models.Model):
    """Feature flags per organization (overrides plan defaults)"""

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="feature_flags"
    )
    feature_name = models.CharField(max_length=100)
    is_enabled = models.BooleanField(default=False)
    custom_limit = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["organization", "feature_name"]

    def __str__(self):
        return f"{self.organization.name}: {self.feature_name} = {self.is_enabled}"


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("subscription", "Subscription"),
        ("payment", "Payment"),
        ("refund", "Refund"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.organization.name} - {self.type} - {self.amount} {self.currency}"

class ProcessedWebhookEvent(models.Model):
    event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=100)
    processed_at = models.DateTimeField(auto_now_add=True)