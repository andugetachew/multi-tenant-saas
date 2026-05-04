import pyotp
import qrcode
from io import BytesIO
import base64
from django.core.cache import cache


class TwoFactorAuth:
    @staticmethod
    def generate_secret(user):
        secret = pyotp.random_base32()
        cache.set(f"2fa_secret_{user.id}", secret, timeout=300)
        return secret

    @staticmethod
    def get_qr_code(user, secret):
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=user.email, issuer_name="SaaS Platform")

        qr = qrcode.make(uri)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{qr_base64}"

    @staticmethod
    def verify_code(user, code):
        secret = cache.get(f"2fa_secret_{user.id}")
        if not secret:
            return False

        totp = pyotp.TOTP(secret)
        return totp.verify(code)
