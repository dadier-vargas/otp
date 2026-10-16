"""Esquemas Pydantic para validación de datos de entrada y salida."""

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Datos para registrar un nuevo usuario."""

    email: EmailStr
    password: str
    full_name: str

    model_config = {"json_schema_extra": {"example": {"email": "user@example.com", "password": "secret123", "full_name": "Juan Pérez"}}}


class UserLogin(BaseModel):
    """Datos para iniciar sesión."""

    email: EmailStr
    password: str


class OtpVerify(BaseModel):
    """Datos para verificar el OTP."""

    email: EmailStr
    code: str


class UserProfileUpdate(BaseModel):
    """Datos para actualizar el perfil."""

    full_name: str | None = None


class UserOut(BaseModel):
    """Datos de usuario que se devuelven en respuestas."""

    id: int
    email: str
    full_name: str

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    """Token JWT devuelto tras verificar OTP."""

    access_token: str
    token_type: str = "bearer"


class MessageOut(BaseModel):
    """Respuesta genérica de mensaje."""

    message: str
