"""Endpoints de autenticación: register, login, verify-otp, refresh, logout, resend-otp."""

import os
from datetime import datetime, timedelta

import jwt
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, LoginSession
from app.schemas import UserCreate, UserLogin, OtpVerify, TokenOut, MessageOut
from app.services.otp_service import generate_otp, verify_otp
from app.services.email_service import send_otp_email

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_jwt(user_id: int) -> tuple[str, datetime]:
    """Crea un token JWT con expiración y lo devuelve junto con su fecha de expiración."""
    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expires_at}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, expires_at


@router.post("/register", response_model=MessageOut, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario con email único y contraseña hasheada."""
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    password_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    user = User(email=data.email, password_hash=password_hash, full_name=data.full_name)
    db.add(user)
    db.commit()
    return {"message": "Usuario registrado correctamente"}


@router.post("/login", response_model=MessageOut)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Autentica al usuario y envía un OTP por correo electrónico."""
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not bcrypt.checkpw(data.password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    code = generate_otp(db, user.id)

    try:
        send_otp_email(user.email, code)
    except Exception:
        # En producción se loguearía el error sin exponer detalles
        pass

    return {"message": f"OTP enviado a {user.email}"}


@router.post("/verify-otp", response_model=TokenOut)
def verify_otp_endpoint(data: OtpVerify, db: Session = Depends(get_db)):
    """Verifica el OTP y devuelve un token JWT si es válido."""
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not verify_otp(db, user.id, data.code):
        raise HTTPException(status_code=400, detail="OTP inválido o expirado")

    token, expires_at = create_jwt(user.id)
    session = LoginSession(user_id=user.id, token=token, expires_at=expires_at)
    db.add(session)
    db.commit()

    return {"access_token": token}


@router.post("/refresh", response_model=TokenOut)
def refresh(request: Request, db: Session = Depends(get_db)):
    """Refresca el JWT actual por uno nuevo (requiere autenticación)."""
    user_id = int(request.state.user_id)
    old_token = request.state.token

    # Revocar sesión anterior
    db.query(LoginSession).filter(LoginSession.token == old_token).delete()

    token, expires_at = create_jwt(user_id)
    session = LoginSession(user_id=user_id, token=token, expires_at=expires_at)
    db.add(session)
    db.commit()

    return {"access_token": token}


@router.post("/logout", response_model=MessageOut)
def logout(request: Request, db: Session = Depends(get_db)):
    """Cierra la sesión revocando el token JWT actual."""
    token = request.state.token
    db.query(LoginSession).filter(LoginSession.token == token).delete()
    db.commit()
    return {"message": "Sesión cerrada correctamente"}


@router.post("/resend-otp", response_model=MessageOut)
def resend_otp(data: UserLogin, db: Session = Depends(get_db)):
    """Reenvía un nuevo OTP al correo del usuario (requiere credenciales válidas)."""
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not bcrypt.checkpw(data.password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    code = generate_otp(db, user.id)
    try:
        send_otp_email(user.email, code)
    except Exception:
        pass

    return {"message": f"OTP reenviado a {user.email}"}
