"""Middleware de autenticación JWT: valida el token en rutas protegidas."""

import os
from datetime import datetime

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

import jwt

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"

# Rutas que NO requieren autenticación
PUBLIC_PATHS = {
    "/auth/register",
    "/auth/login",
    "/auth/verify-otp",
    "/auth/resend-otp",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware que valida JWT en rutas protegidas."""

    async def dispatch(self, request: Request, call_next):
        """Valida el token JWT antes de pasar la petición al handler."""
        if request.url.path in PUBLIC_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse({"detail": "Token requerido"}, status_code=401)

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            request.state.user_id = payload["sub"]
            request.state.token = token
        except jwt.ExpiredSignatureError:
            return JSONResponse({"detail": "Token expirado"}, status_code=401)
        except jwt.InvalidTokenError:
            return JSONResponse({"detail": "Token inválido"}, status_code=401)

        return await call_next(request)
