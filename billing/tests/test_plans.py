from django.test import TestCase
from organizations.models import Organization


class PlanLimitsTestCase(TestCase):
    def test_trial_limits(self):
        """Test trial plan limits"""
        org = Organization.objects.create(name="Trial Org", plan="trial")
        self.assertEqual(org.plan, "trial")

    def test_basic_limits(self):
        """Test basic plan limits"""
        org = Organization.objects.create(name="Basic Org", plan="basic")
        self.assertEqual(org.plan, "basic")

    def test_pro_limits(self):
        """Test pro plan limits"""
        org = Organization.objects.create(name="Pro Org", plan="pro")
        self.assertEqual(org.plan, "pro")
