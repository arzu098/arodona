import pyotp
import qrcode
import io
import base64
import secrets
import string
from typing import Tuple, List

def generate_totp_secret() -> str:
    """Generate a new TOTP secret"""
    return pyotp.random_base32()

def generate_backup_codes(count: int = 8) -> List[str]:
    """Generate backup codes for 2FA recovery"""
    alphabet = string.ascii_uppercase + string.digits
    return [
        ''.join(secrets.choice(alphabet) for _ in range(8))
        for _ in range(count)
    ]

def get_totp_uri(secret: str, email: str, issuer: str = "Your App") -> str:
    """Get the TOTP URI for QR code generation"""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(email, issuer_name=issuer)

def generate_qr_code(uri: str) -> str:
    """Generate QR code as base64 image"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

def verify_totp_code(secret: str, code: str) -> bool:
    """Verify a TOTP code"""
    totp = pyotp.TOTP(secret)
    return totp.verify(code)