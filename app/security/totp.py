"""
TOTP (Time-based One-Time Password) - Two-Factor Authentication
"""
import pyotp
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
from typing import Tuple, Optional
import secrets
import logging

logger = logging.getLogger(__name__)


class TOTPManager:
    """
    Gestiona la autenticación de dos factores con TOTP.
    Compatible con Google Authenticator, Authy, etc.
    """
    
    # Almacenamiento en memoria (usar DB en producción)
    _user_secrets = {}  # user_id -> {secret, enabled, backup_codes}
    
    ISSUER_NAME = "Onboarding System"
    DIGITS = 6
    INTERVAL = 30  # segundos
    
    @classmethod
    def generate_secret(cls) -> str:
        """Genera un secreto TOTP aleatorio."""
        return pyotp.random_base32()
    
    @classmethod
    def setup_totp(cls, user_id: int, username: str) -> dict:
        """
        Inicia la configuración de 2FA para un usuario.
        
        Args:
            user_id: ID del usuario
            username: Email o nombre de usuario
        
        Returns:
            dict con secret, qr_code_uri, qr_code_svg, backup_codes
        """
        # Generar secreto
        secret = cls.generate_secret()
        
        # Generar códigos de respaldo
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        
        # Almacenar (no activado aún)
        cls._user_secrets[user_id] = {
            "secret": secret,
            "enabled": False,
            "backup_codes": backup_codes,
            "backup_codes_used": []
        }
        
        # Crear TOTP
        totp = pyotp.TOTP(secret, digits=cls.DIGITS, interval=cls.INTERVAL)
        
        # URI para apps de autenticación
        provisioning_uri = totp.provisioning_uri(
            name=username,
            issuer_name=cls.ISSUER_NAME
        )
        
        # Generar QR code como SVG
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Crear imagen QR como base64
        img_buffer = BytesIO()
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(img_buffer, format='PNG')
        qr_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        
        logger.info(f"TOTP setup initiated for user {user_id}")
        
        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri,
            "qr_code_base64": f"data:image/png;base64,{qr_base64}",
            "backup_codes": backup_codes
        }
    
    @classmethod
    def verify_and_enable(cls, user_id: int, code: str) -> bool:
        """
        Verifica un código TOTP y habilita 2FA si es correcto.
        Se usa durante el setup inicial.
        
        Args:
            user_id: ID del usuario
            code: Código TOTP de 6 dígitos
        
        Returns:
            True si el código es válido y 2FA fue habilitado
        """
        if user_id not in cls._user_secrets:
            return False
        
        user_data = cls._user_secrets[user_id]
        secret = user_data["secret"]
        
        totp = pyotp.TOTP(secret, digits=cls.DIGITS, interval=cls.INTERVAL)
        
        # Verificar con ventana de tolerancia de 1 intervalo
        if totp.verify(code, valid_window=1):
            user_data["enabled"] = True
            logger.info(f"TOTP enabled for user {user_id}")
            return True
        
        return False
    
    @classmethod
    def verify_code(cls, user_id: int, code: str) -> bool:
        """
        Verifica un código TOTP durante el login.
        
        Args:
            user_id: ID del usuario
            code: Código TOTP de 6 dígitos
        
        Returns:
            True si el código es válido
        """
        if user_id not in cls._user_secrets:
            return False
        
        user_data = cls._user_secrets[user_id]
        
        if not user_data["enabled"]:
            return True  # 2FA no habilitado, pasar
        
        secret = user_data["secret"]
        totp = pyotp.TOTP(secret, digits=cls.DIGITS, interval=cls.INTERVAL)
        
        if totp.verify(code, valid_window=1):
            logger.info(f"TOTP verified for user {user_id}")
            return True
        
        logger.warning(f"TOTP verification failed for user {user_id}")
        return False
    
    @classmethod
    def verify_backup_code(cls, user_id: int, code: str) -> bool:
        """
        Verifica un código de respaldo.
        Cada código solo puede usarse una vez.
        
        Args:
            user_id: ID del usuario
            code: Código de respaldo
        
        Returns:
            True si el código es válido y no ha sido usado
        """
        if user_id not in cls._user_secrets:
            return False
        
        user_data = cls._user_secrets[user_id]
        code_upper = code.upper().replace("-", "").replace(" ", "")
        
        if code_upper in user_data["backup_codes"] and code_upper not in user_data["backup_codes_used"]:
            user_data["backup_codes_used"].append(code_upper)
            logger.info(f"Backup code used for user {user_id}")
            return True
        
        return False
    
    @classmethod
    def is_enabled(cls, user_id: int) -> bool:
        """Verifica si el usuario tiene 2FA habilitado."""
        if user_id not in cls._user_secrets:
            return False
        return cls._user_secrets[user_id]["enabled"]
    
    @classmethod
    def disable_totp(cls, user_id: int, code: str) -> bool:
        """
        Deshabilita 2FA para un usuario.
        Requiere un código válido para confirmar.
        
        Args:
            user_id: ID del usuario
            code: Código TOTP actual
        
        Returns:
            True si 2FA fue deshabilitado
        """
        if user_id not in cls._user_secrets:
            return False
        
        # Verificar código antes de deshabilitar
        if not cls.verify_code(user_id, code):
            return False
        
        del cls._user_secrets[user_id]
        logger.info(f"TOTP disabled for user {user_id}")
        return True
    
    @classmethod
    def regenerate_backup_codes(cls, user_id: int) -> Optional[list]:
        """
        Regenera los códigos de respaldo.
        
        Returns:
            Lista de nuevos códigos de respaldo
        """
        if user_id not in cls._user_secrets:
            return None
        
        new_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        cls._user_secrets[user_id]["backup_codes"] = new_codes
        cls._user_secrets[user_id]["backup_codes_used"] = []
        
        logger.info(f"Backup codes regenerated for user {user_id}")
        return new_codes
    
    @classmethod
    def get_remaining_backup_codes(cls, user_id: int) -> int:
        """Retorna la cantidad de códigos de respaldo restantes."""
        if user_id not in cls._user_secrets:
            return 0
        
        user_data = cls._user_secrets[user_id]
        total = len(user_data["backup_codes"])
        used = len(user_data["backup_codes_used"])
        return total - used
