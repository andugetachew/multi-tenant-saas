import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organizations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField(unique=True)),
                ('price_monthly', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('price_yearly', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('max_projects', models.IntegerField(default=3)),
                ('max_users', models.IntegerField(default=5)),
                ('max_storage_mb', models.IntegerField(default=100)),
                ('has_real_time_analytics', models.BooleanField(default=False)),
                ('has_advanced_exports', models.BooleanField(default=False)),
                ('has_priority_support', models.BooleanField(default=False)),
                ('has_api_access', models.BooleanField(default=False)),
                ('has_audit_logs', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['price_monthly'],
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending Approval'), ('active', 'Active'), ('past_due', 'Past Due'), ('canceled', 'Canceled'), ('expired', 'Expired')], default='pending', max_length=20)),
                ('billing_email', models.EmailField(blank=True, max_length=254)),
                ('billing_address', models.TextField(blank=True)),
                ('current_period_start', models.DateTimeField(auto_now_add=True)),
                ('current_period_end', models.DateTimeField(blank=True, null=True)),
                ('canceled_at', models.DateTimeField(blank=True, null=True)),
                ('max_projects', models.IntegerField(default=3)),
                ('max_users', models.IntegerField(default=5)),
                ('max_storage_mb', models.IntegerField(default=100)),
                ('has_real_time_analytics', models.BooleanField(default=False)),
                ('has_advanced_exports', models.BooleanField(default=False)),
                ('has_priority_support', models.BooleanField(default=False)),
                ('has_api_access', models.BooleanField(default=False)),
                ('has_audit_logs', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to='organizations.organization')),
                ('plan', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='billing.plan')),
            ],
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_number', models.CharField(max_length=50, unique=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('pending', 'Pending Payment'), ('paid', 'Paid'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled')], default='draft', max_length=20)),
                ('issue_date', models.DateTimeField(auto_now_add=True)),
                ('due_date', models.DateTimeField(blank=True, null=True)),
                ('paid_date', models.DateTimeField(blank=True, null=True)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('admin_notes', models.TextField(blank=True)),
                ('approved_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_invoices', to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='organizations.organization')),
                ('requested_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('requested_plan', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='requests', to='billing.plan')),
                ('subscription', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='billing.subscription')),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('subscription', 'Subscription'), ('payment', 'Payment'), ('refund', 'Refund')], max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed'), ('refunded', 'Refunded')], default='pending', max_length=20)),
                ('stripe_payment_intent_id', models.CharField(blank=True, max_length=100, null=True)),
                ('stripe_subscription_id', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.TextField(blank=True)),
                ('metadata', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='organizations.organization')),
            ],
        ),
        migrations.CreateModel(
            name='FeatureFlag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feature_name', models.CharField(max_length=100)),
                ('is_enabled', models.BooleanField(default=False)),
                ('custom_limit', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feature_flags', to='organizations.organization')),
            ],
            options={
                'unique_together': {('organization', 'feature_name')},
            },
        ),
    ]
