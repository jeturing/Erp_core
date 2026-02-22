"""
Email Verification — Steam-style alphanumeric token sent to email after password check.

Flow:
  1. User submits email+password → backend validates credentials
  2. If email_verify required → returns requires_email_verify=True
  3. Backend generates 6-char alphanumeric token, sends to email
  4. User enters token → POST /api/auth/verify-email-token
  5. If valid → JWT issued, login complete

Configurable per role:
  - partner/tenant: ALWAYS required
  - admin: optional (toggle require_email_verify on admin_users)
"""
import hashlib
import logging
import secrets
import string
from datetime import datetime, timedelta

from ..models.database import EmailVerificationToken, SessionLocal

logger = logging.getLogger(__name__)

# Token config
TOKEN_LENGTH = 6
TOKEN_TTL_MINUTES = 5
TOKEN_CHARS = string.ascii_uppercase + string.digits  # A-Z + 0-9


def generate_token() -> str:
    """Generate a 6-character alphanumeric token (uppercase + digits)."""
    return "".join(secrets.choice(TOKEN_CHARS) for _ in range(TOKEN_LENGTH))


def hash_token(token: str) -> str:
    """SHA-256 hash of token for storage."""
    return hashlib.sha256(token.upper().encode()).hexdigest()


def create_verification_token(
    email: str,
    user_type: str,
    user_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> str:
    """
    Create and store a verification token. Returns the plain token.
    Invalidates any previous unused tokens for this email.
    """
    token = generate_token()
    token_h = hash_token(token)
    expires = datetime.utcnow() + timedelta(minutes=TOKEN_TTL_MINUTES)

    db = SessionLocal()
    try:
        # Invalidate previous tokens for this email
        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.email == email,
            EmailVerificationToken.is_used == False,
        ).update({"is_used": True, "used_at": datetime.utcnow()})

        record = EmailVerificationToken(
            email=email,
            token=token,  # stored for admin debug, never exposed via API
            token_hash=token_h,
            user_type=user_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires,
        )
        db.add(record)
        db.commit()
        logger.info(f"Email verification token created for {email} (type={user_type})")
        return token
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create verification token: {e}")
        raise
    finally:
        db.close()


def verify_token(email: str, token: str) -> bool:
    """
    Verify a token. Returns True if valid and not expired.
    Marks as used on success.
    """
    token_h = hash_token(token.upper().strip())

    db = SessionLocal()
    try:
        record = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.email == email,
            EmailVerificationToken.token_hash == token_h,
            EmailVerificationToken.is_used == False,
            EmailVerificationToken.expires_at > datetime.utcnow(),
        ).first()

        if not record:
            return False

        record.is_used = True
        record.used_at = datetime.utcnow()
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to verify token: {e}")
        return False
    finally:
        db.close()


def send_verification_email(email: str, token: str, user_type: str = "tenant") -> dict:
    """Send the verification token via email using the email service."""
    from ..services.email_service import send_email, _base_template

    # Format token with spaces for readability: "AB3 K9Z"
    formatted = f"{token[:3]} {token[3:]}"

    content = f"""
    <h2 style="color: #e74c3c; margin-top: 0;">Código de verificación 🔐</h2>
    <p>Se ha solicitado acceso a tu cuenta. Ingresa el siguiente código para completar el inicio de sesión:</p>

    <div style="background: #1a1a2e; border-radius: 12px; padding: 32px; margin: 24px 0; text-align: center;
                border: 2px solid #e74c3c;">
      <p style="font-family: 'Courier New', monospace; font-size: 36px; font-weight: 700;
                letter-spacing: 12px; color: #fff; margin: 0;">
        {formatted}
      </p>
      <p style="color: #999; font-size: 12px; margin: 12px 0 0;">
        Válido por {TOKEN_TTL_MINUTES} minutos
      </p>
    </div>

    <div style="background: #1a1a2e; border-radius: 8px; padding: 16px; margin: 16px 0;
                border-left: 4px solid #f39c12;">
      <p style="color: #f39c12; font-size: 13px; margin: 0;">
        ⚠️ Si no solicitaste este código, ignora este mensaje y cambia tu contraseña.
      </p>
    </div>

    <p style="color: #999; font-size: 12px;">
      Este código es de un solo uso y expira en {TOKEN_TTL_MINUTES} minutos.
      No compartas este código con nadie.
    </p>
    """

    return send_email(
        to_email=email,
        subject=f"🔐 Código de verificación: {formatted} — SAJET",
        html_body=_base_template(content),
        text_body=f"Tu código de verificación SAJET: {formatted}\nVálido por {TOKEN_TTL_MINUTES} minutos.",
        email_type="login_verification",
    )
