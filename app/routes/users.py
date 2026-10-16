"""Endpoints de usuario: ver y actualizar perfil (rutas protegidas)."""

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserOut, UserProfileUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile", response_model=UserOut)
def get_profile(request: Request, db: Session = Depends(get_db)):
    """Devuelve el perfil del usuario autenticado."""
    user_id = int(request.state.user_id)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.put("/profile", response_model=UserOut)
def update_profile(data: UserProfileUpdate, request: Request, db: Session = Depends(get_db)):
    """Actualiza el perfil del usuario autenticado."""
    user_id = int(request.state.user_id)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if data.full_name is not None:
        user.full_name = data.full_name

    db.commit()
    db.refresh(user)
    return user
