# Sistema de Autenticación OTP - FastAPI

API REST de autenticación de dos factores con FastAPI, SQLAlchemy (SQLite) y OTP enviado por correo electrónico.

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración

1. Copia `.env.example` a `.env` y completa las variables:
```bash
cp .env.example .env
```

2. Edita `.env` con tus credenciales SMTP (Gmail recomendado, usar App Password).

## Ejecutar el servidor

```bash
uvicorn app.main:app --reload
```

La API estará disponible en `http://localhost:8000`  
Documentación interactiva: `http://localhost:8000/docs`

## Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| POST | `/auth/register` | Registrar usuario | No |
| POST | `/auth/login` | Login + envío OTP | No |
| POST | `/auth/verify-otp` | Verificar OTP → JWT | No |
| POST | `/auth/refresh` | Refrescar token | Sí |
| POST | `/auth/logout` | Cerrar sesión | Sí |
| POST | `/auth/resend-otp` | Reenviar OTP | No |
| GET | `/users/profile` | Ver perfil | Sí |
| PUT | `/users/profile` | Actualizar perfil | Sí |

## Flujo de autenticación

1. `POST /auth/register` → Crear cuenta
2. `POST /auth/login` → Envía OTP al correo
3. `POST /auth/verify-otp` → Retorna JWT
4. Usar JWT en header: `Authorization: Bearer <token>`

## Tests

```bash
pytest tests/ -v
```

## Despliegue (Render / Railway)

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
