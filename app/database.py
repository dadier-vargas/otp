"""Configuración de la base de datos SQLite con SQLAlchemy."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./otp_auth.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Devuelve una sesión de base de datos y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
