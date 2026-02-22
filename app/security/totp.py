"""
TOTP (Time-based One-Time Password) - Two-Factor Authentication
Los secrets se persisten en BD (columnas en Customer/Partner, o SystemConfig para admin).
"""
import pyotp
import qrcode
from io import BytesIO
import base64
import json
from typing import Optional
import secrets
import logging

logger = logging.getLogger(__name__)


def _get_db():
    """Import lazy para evitar circular imports."""
    from ..models.database import Customer, Partner, SessionLocal, get_config, set_config
    return Customer, Partner, SessionLocal, get_config, set_config


class TOTPManager:
    """
    Gestiona la autenticación de dos factores con TOTP.
    Compatible con Google Authenticator, Authy, etc.
    Persiste los secrets en BD, no en memoria.

    Mapeo user_id:
    - 0 → admin (SystemConfig)
    - > 0 → intenta Customer primero, luego Partner
    """

    ISSUER_NAME = "Sajet ERP"
    DIGITS = 6
    INTERVAL = 30

    # ── Helpers privados de persistencia ──────────────────────────────────────

    @classmethod
    def _load(cls, user_id: int) -> Optional[dict]:
        """Carga datos TOTP del usuario desde BD."""
        Customer, Partner, SessionLocal, get_config, _ = _get_db()

        if user_id == 0:
            raw = get_config("admin_totp_config")
            return json.loads(raw) if raw else None

        session = SessionLocal()
        try:
            # Intentar Customer
            obj = session.query(Customer).filter(Customer.id == user_id).first()
            if obj and obj.totp_secret:
                return {
                    "secret": obj.totp_secret,
                    "enabled": bool(obj.totp_enabled),
                    "backup_codes": json.loads(obj.totp_backup_codes or "[]"),
                    "backup_codes_used": json.loads(obj.totp_backup_codes_used or "[]"),
                    "_model": "customer",
                }
            # Intentar Partner
            obj = session.query(Partner).filter(Partner.id == user_id).first()
            if obj and obj.totp_secret:
                return {
                    "secret": obj.totp_secret,
                    "enabled": bool(obj.totp_enabled),
                    "backup_codes": json.loads(obj.totp_backup_codes or "[]"),
                    "backup_codes_used": json.loads(obj.totp_backup_codes_used or "[]"),
                    "_model": "partner",
                }
            return None
        finally:
            session.close()

    @classmethod
    def _save(cls, user_id: int, data: dict):
        """Persiste datos TOTP del usuario en BD."""
        Customer, Partner, SessionLocal, get_config, set_config = _get_db()

        if user_id == 0:
            payload = {k: v for k, v in data.items() if not k.startswith("_")}
            set_config("admin_totp_config", json.dumps(payload), category="security", is_secret=True)
            return

        session = SessionLocal()
        try:
            obj = session.query(Customer).filter(Customer.id == user_id).first()
            model = "customer"
            if obj is None:
                obj = session.query(Partner).filter(Partner.id == user_id).first()
                model = "partner"
            if obj is None:
                logger.error(f"Cannot save TOTP — user_id {user_id} not found in Customer or Partner")
                return
            obj.totp_secret = data.get("secret")
            obj.totp_enabled = data.get("enabled", False)
            obj.totp_backup_codes = json.dumps(data.get("backup_codes", []))
            obj.totp_backup_codes_used = json.dumps(data.get("backup_codes_used", []))
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving TOTP for user {user_id}: {e}")
        finally:
            session.close()

    @classmethod
    def _delete(cls, user_id: int):
        """Elimina datos TOTP del usuario de BD."""
        Customer, Partner, SessionLocal, get_config, set_config = _get_db()

        if user_id == 0:
            set_config("admin_totp_config", "", category="security", is_secret=True)
            return

        session = SessionLocal()
        try:
            for Model in (Customer, Partner):
                obj = session.query(Model).filter(Model.id == user_id).first()
                if obj and obj.totp_secret:
                    obj.totp_secret = None
                    obj.totp_enabled = False
                    obj.totp_backup_codes = None
                    obj.totp_backup_codes_used = None
                    session.commit()
                    return
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting TOTP for user {user_id}: {e}")
        finally:
            session.close()

    # ── API pública ──────────────────────────────────────────────────────────

    @classmethod
    def generate_secret(cls) -> str:
        return pyotp.random_base32()

    @classmethod
    def setup_totp(cls, user_id: int, username: str) -> dict:
        """Inicia la configuración de 2FA: genera secret + QR + backup codes."""
        secret = cls.generate_secret()
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]

        data = {
            "secret": secret,
            "enabled": False,
            "backup_codes": backup_codes,
            "backup_codes_used": [],
        }
        cls._save(user_id, data)

        totp = pyotp.TOTP(secret, digits=cls.DIGITS, interval=cls.INTERVAL)
        provisioning_uri = totp.provisioning_uri(name=username, issuer_name=cls.ISSUER_NAME)

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img_buffer = BytesIO()
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(img_buffer, format="PNG")
        qr_base64 = base64.b64encode(img_buffer.getvalue()).decode()

        logger.info(f"TOTP setup initiated for user {user_id}")
        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri,
            "qr_code_base64": f"data:image/png;base64,{qr_base64}",
            "backup_codes": backup_codes,
        }

    @classmethod
    def verify_and_enable(cls, user_id: int, code: str) -> bool:
        """Verifica código TOTP y habilita 2FA si es correcto."""
        data = cls._load(user_id)
        if not data:
            return False
        totp = pyotp.TOTP(data["secret"], digits=cls.DIGITS, interval=cls.INTERVAL)
        if totp.verify(code, valid_window=1):
            data["enabled"] = True
            cls._save(user_id, data)
            logger.info(f"TOTP enabled for user {user_id}")
            return True
        return False

    @classmethod
    def verify_code(cls, user_id: int, code: str) -> bool:
        """Verifica un código TOTP durante el login."""
        data = cls._load(user_id)
        if not data or not data.get("enabled"):
            return True  # 2FA no habilitado → pasar
        totp = pyotp.TOTP(data["secret"], digits=cls.DIGITS, interval=cls.INTERVAL)
        if totp.verify(code, valid_window=1):
            logger.info(f"TOTP verified for user {user_id}")
            return True
        logger.warning(f"TOTP verification failed for user {user_id}")
        return False

    @classmethod
    def verify_backup_code(cls, user_id: int, code: str) -> bool:
        """Verifica un código de respaldo (cada uno de un solo uso)."""
        data = cls._load(user_id)
        if not data:
            return False
        code_upper = code.upper().replace("-", "").replace(" ", "")
        if code_upper in data["backup_codes"] and code_upper not in data["backup_codes_used"]:
            data["backup_codes_used"].append(code_upper)
            cls._save(user_id, data)
            logger.info(f"Backup code used for user {user_id}")
            return True
        return False

    @classmethod
    def is_enabled(cls, user_id: int) -> bool:
        """Verifica si el usuario tiene 2FA habilitado."""
        data = cls._load(user_id)
        return bool(data and data.get("enabled"))

    @classmethod
    def disable_totp(cls, user_id: int, code: str) -> bool:
        """Deshabilita 2FA (requiere código válido)."""
        if not cls.verify_code(user_id, code):
            return False
        cls._delete(user_id)
        logger.info(f"TOTP disabled for user {user_id}")
        return True

    @classmethod
    def regenerate_backup_codes(cls, user_id: int) -> Optional[list]:
        """Regenera los códigos de respaldo."""
        data = cls._load(user_id)
        if not data:
            return None
        new_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        data["backup_codes"] = new_codes
        data["backup_codes_used"] = []
        cls._save(user_id, data)
        logger.info(f"Backup codes regenerated for user {user_id}")
        return new_codes

    @classmethod
    def get_remaining_backup_codes(cls, user_id: int) -> int:
        """Retorna la cantidad de códigos de respaldo restantes."""
        data = cls._load(user_id)
        if not data:
            return 0
        total = len(data.get("backup_codes", []))
        used = len(data.get("backup_codes_used", []))
        return total - used
