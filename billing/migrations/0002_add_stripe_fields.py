from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="plan",
            name="stripe_price_id",
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        migrations.AddField(
            model_name="subscription",
            name="stripe_customer_id",
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        migrations.AddField(
            model_name="subscription",
            name="stripe_subscription_id",
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
    ]