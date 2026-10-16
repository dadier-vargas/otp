"""Aplicación principal FastAPI con middleware de autenticación."""

from fastapi import FastAPI
from app.database import engine, Base
from app.middleware import AuthMiddleware
from app.routes import auth, users

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Autenticación OTP",
    description="API REST de autenticación de dos factores con FastAPI, SQLAlchemy y OTP por correo.",
    version="1.0.0",
)

# Middleware de autenticación JWT
app.add_middleware(AuthMiddleware)

# Rutas
app.include_router(auth.router)
app.include_router(users.router)


@app.get("/")
def root():
    """Endpoint raíz de verificación de estado."""
    return {"status": "ok", "message": "API de autenticación OTP funcionando"}
