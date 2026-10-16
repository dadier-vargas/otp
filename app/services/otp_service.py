"""Servicio de generación y validación de códigos OTP."""

import random
import string
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import OtpCode

OTP_EXPIRY_MINUTES = 15


def generate_otp(db: Session, user_id: int) -> str:
    """Genera un código OTP de 6 dígitos, lo guarda en BD y lo devuelve."""
    # Invalidar OTPs anteriores del usuario
    db.query(OtpCode).filter(OtpCode.user_id == user_id, OtpCode.used == False).update({"used": True})

    code = "".join(random.choices(string.digits, k=6))
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    otp = OtpCode(user_id=user_id, code=code, expires_at=expires_at)
    db.add(otp)
    db.commit()
    return code


def verify_otp(db: Session, user_id: int, code: str) -> bool:
    """Verifica que el OTP sea válido, no usado y no expirado. Lo marca como usado si es correcto."""
    now = datetime.utcnow()
    otp = (
        db.query(OtpCode)
        .filter(
            OtpCode.user_id == user_id,
            OtpCode.code == code,
            OtpCode.used == False,
            OtpCode.expires_at > now,
        )
        .first()
    )
    if not otp:
        return False
    otp.used = True
    db.commit()
    return True
