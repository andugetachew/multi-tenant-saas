from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0002_add_stripe_fields"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE billing_subscription ADD COLUMN IF NOT EXISTS stripe_customer_id varchar(100) NULL;
                ALTER TABLE billing_subscription ADD COLUMN IF NOT EXISTS stripe_subscription_id varchar(100) NULL;
                ALTER TABLE billing_plan DROP COLUMN IF EXISTS stripe_customer_id;
                ALTER TABLE billing_plan DROP COLUMN IF EXISTS stripe_subscription_id;
            """,
            reverse_sql="""
                ALTER TABLE billing_plan ADD COLUMN IF NOT EXISTS stripe_customer_id varchar(100) NULL;
                ALTER TABLE billing_plan ADD COLUMN IF NOT EXISTS stripe_subscription_id varchar(100) NULL;
            """,
        ),
    ]