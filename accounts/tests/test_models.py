from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from organizations.models import Organization

User = get_user_model()


class UserModelTestCase(TestCase):
    """Test User model behavior in multi-tenant SaaS system"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.filter(email='admin@example.com').delete()
        

    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Org",
            plan="trial"
        )


    def test_create_user_success(self):
        """Test normal user creation with organization"""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            organization=self.org
        )

        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))
        self.assertEqual(user.organization, self.org)
        self.assertEqual(user.role, "member")
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        """Test superuser creation"""
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="admin123",
            organization=self.org
        )

        self.assertEqual(user.email, "admin@example.com")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertEqual(user.organization, self.org)


    def test_unique_email_constraint(self):
        """Test email must be unique globally"""
        User.objects.create_user(
            email="unique@example.com",
            password="pass123",
            organization=self.org
        )

        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email="unique@example.com",
                password="pass123",
                organization=self.org
            )

    def test_user_requires_organization(self):
        """User must belong to an organization (multi-tenant rule)"""
        with self.assertRaises(Exception):
            User.objects.create_user(
                email="noorg@example.com",
                password="pass123"
            )

   

    def test_generate_email_verification_token(self):
        """Test email verification token generation"""
        user = User.objects.create_user(
            email="verify@example.com",
            password="pass123",
            organization=self.org
        )

        token = user.generate_email_verification_token()

        self.assertIsNotNone(token)
        self.assertEqual(user.email_verification_token, token)
        self.assertIsNotNone(user.email_verification_sent_at)

    def test_generate_password_reset_token(self):
        """Test password reset token generation"""
        user = User.objects.create_user(
            email="reset@example.com",
            password="pass123",
            organization=self.org
        )

        token = user.generate_password_reset_token()

        self.assertIsNotNone(token)
        self.assertEqual(user.password_reset_token, token)
        self.assertIsNotNone(user.password_reset_token_created_at)

 

    def test_default_user_state(self):
        """Test default flags for new users"""
        user = User.objects.create_user(
            email="default@example.com",
            password="pass123",
            organization=self.org
        )

        self.assertFalse(user.is_email_verified)
        self.assertTrue(user.is_active)  # adjust if your system disables until verification
        self.assertEqual(user.role, "member")

    def test_string_representation(self):
        """Test __str__ method"""
        user = User.objects.create_user(
            email="string@example.com",
            password="pass123",
            organization=self.org
        )

        self.assertEqual(str(user), "string@example.com")