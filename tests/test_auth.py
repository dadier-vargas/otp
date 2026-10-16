"""Tests unitarios y de integración para el sistema de autenticación OTP."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
import bcrypt

from app.models import User, OtpCode
from app.services.otp_service import generate_otp, verify_otp


# =============================================================================
# TESTS UNITARIOS (mínimo 5)
# =============================================================================


class TestOtpService:
    """Tests unitarios del servicio OTP."""

    def test_generate_otp_returns_6_digits(self, db):
        """El OTP generado debe ser de exactamente 6 dígitos."""
        user = User(email="u@test.com", password_hash="x", full_name="Test")
        db.add(user)
        db.commit()

        code = generate_otp(db, user.id)

        assert len(code) == 6
        assert code.isdigit()

    def test_generate_otp_saves_to_db(self, db):
        """El OTP debe guardarse en la base de datos."""
        user = User(email="u@test.com", password_hash="x", full_name="Test")
        db.add(user)
        db.commit()

        generate_otp(db, user.id)

        otp = db.query(OtpCode).filter(OtpCode.user_id == user.id).first()
        assert otp is not None
        assert otp.used is False

    def test_generate_otp_invalidates_previous(self, db):
        """Generar un nuevo OTP debe invalidar el anterior."""
        user = User(email="u@test.com", password_hash="x", full_name="Test")
        db.add(user)
        db.commit()

        generate_otp(db, user.id)
        generate_otp(db, user.id)

        active = db.query(OtpCode).filter(OtpCode.user_id == user.id, OtpCode.used == False).count()
        assert active == 1

    def test_verify_otp_valid(self, db):
        """Un OTP válido y no expirado debe verificarse correctamente."""
        user = User(email="u@test.com", password_hash="x", full_name="Test")
        db.add(user)
        db.commit()

        code = generate_otp(db, user.id)
        result = verify_otp(db, user.id, code)

        assert result is True

    def test_verify_otp_wrong_code(self, db):
        """Un código incorrecto debe fallar la verificación."""
        user = User(email="u@test.com", password_hash="x", full_name="Test")
        db.add(user)
        db.commit()

        generate_otp(db, user.id)
        result = verify_otp(db, user.id, "000000")

        assert result is False

    def test_verify_otp_expired(self, db):
        """Un OTP expirado debe fallar la verificación."""
        user = User(email="u@test.com", password_hash="x", full_name="Test")
        db.add(user)
        db.commit()

        # Crear OTP ya expirado
        expired_otp = OtpCode(
            user_id=user.id,
            code="123456",
            expires_at=datetime.utcnow() - timedelta(minutes=1),
        )
        db.add(expired_otp)
        db.commit()

        result = verify_otp(db, user.id, "123456")
        assert result is False

    def test_verify_otp_used(self, db):
        """Un OTP ya usado no debe poder verificarse de nuevo."""
        user = User(email="u@test.com", password_hash="x", full_name="Test")
        db.add(user)
        db.commit()

        code = generate_otp(db, user.id)
        verify_otp(db, user.id, code)  # Primera vez: OK
        result = verify_otp(db, user.id, code)  # Segunda vez: debe fallar

        assert result is False


# =============================================================================
# TESTS DE INTEGRACIÓN (mínimo 3)
# =============================================================================


class TestAuthEndpoints:
    """Tests de integración de los endpoints de autenticación."""

    def test_register_success(self, client):
        """POST /auth/register debe crear un usuario y devolver 201."""
        response = client.post(
            "/auth/register",
            json={"email": "nuevo@test.com", "password": "pass123", "full_name": "Nuevo Usuario"},
        )
        assert response.status_code == 201
        assert "registrado" in response.json()["message"]

    def test_register_duplicate_email(self, client):
        """Registrar con email duplicado debe devolver 400."""
        data = {"email": "dup@test.com", "password": "pass123", "full_name": "Usuario"}
        client.post("/auth/register", json=data)
        response = client.post("/auth/register", json=data)
        assert response.status_code == 400

    @patch("app.routes.auth.send_otp_email")
    def test_login_sends_otp(self, mock_email, client):
        """POST /auth/login debe enviar el OTP y devolver 200."""
        client.post(
            "/auth/register",
            json={"email": "login@test.com", "password": "pass123", "full_name": "User"},
        )
        response = client.post("/auth/login", json={"email": "login@test.com", "password": "pass123"})
        assert response.status_code == 200
        assert "OTP enviado" in response.json()["message"]

    @patch("app.routes.auth.send_otp_email")
    def test_verify_otp_and_get_token(self, mock_email, client, db):
        """Verificar OTP válido debe devolver un JWT."""
        client.post(
            "/auth/register",
            json={"email": "otp@test.com", "password": "pass123", "full_name": "User"},
        )
        client.post("/auth/login", json={"email": "otp@test.com", "password": "pass123"})

        user = db.query(User).filter(User.email == "otp@test.com").first()
        otp = db.query(OtpCode).filter(OtpCode.user_id == user.id, OtpCode.used == False).first()

        response = client.post("/auth/verify-otp", json={"email": "otp@test.com", "code": otp.code})
        assert response.status_code == 200
        assert "access_token" in response.json()

    @patch("app.routes.auth.send_otp_email")
    def test_protected_route_without_token(self, mock_email, client):
        """Acceder a ruta protegida sin token debe devolver 401."""
        response = client.get("/users/profile")
        assert response.status_code == 401

    @patch("app.routes.auth.send_otp_email")
    def test_logout_revokes_token(self, mock_email, client, db):
        """POST /auth/logout debe revocar el token y el acceso posterior debe fallar."""
        client.post(
            "/auth/register",
            json={"email": "logout@test.com", "password": "pass123", "full_name": "User"},
        )
        client.post("/auth/login", json={"email": "logout@test.com", "password": "pass123"})

        user = db.query(User).filter(User.email == "logout@test.com").first()
        otp = db.query(OtpCode).filter(OtpCode.user_id == user.id, OtpCode.used == False).first()

        token_res = client.post("/auth/verify-otp", json={"email": "logout@test.com", "code": otp.code})
        token = token_res.json()["access_token"]

        logout_res = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert logout_res.status_code == 200
