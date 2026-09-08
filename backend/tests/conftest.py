import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Force testing configuration
os.environ["ENVIRONMENT"] = "testing"
os.environ["AUTH_MODE"] = "mock"
os.environ["AI_MODE"] = "mock"

from app.database import Base, get_db
from app.models.user import User
from app.models.buyer import Buyer
from app.main import app
from app.api.dependencies import get_current_user

# Test database URL — uses TEST_DATABASE_URL or fallback to an in-memory SQLite database
TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")

if TEST_DB_URL.startswith("sqlite"):
    test_engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    test_engine = create_engine(TEST_DB_URL, pool_pre_ping=True)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables in the test database once per test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a transactional database session per test function."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide a FastAPI test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def user_a(db_session: Session) -> User:
    """Create and return Test User A."""
    user = db_session.query(User).filter(User.firebase_uid == "mock_user_a").first()
    if not user:
        user = User(
            firebase_uid="mock_user_a",
            name="Artisan Ramesh",
            phone="+91-98765-11111",
            language="hi",
            location="Jaipur, Rajasthan",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def user_b(db_session: Session) -> User:
    """Create and return Test User B."""
    user = db_session.query(User).filter(User.firebase_uid == "mock_user_b").first()
    if not user:
        user = User(
            firebase_uid="mock_user_b",
            name="Artisan Suresh",
            phone="+91-98765-22222",
            language="en",
            location="Varanasi, Uttar Pradesh",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(user_a: User) -> dict:
    """Authentication headers for User A."""
    return {"Authorization": f"Bearer user_a"}


@pytest.fixture
def auth_headers_b(user_b: User) -> dict:
    """Authentication headers for User B."""
    return {"Authorization": f"Bearer user_b"}


@pytest.fixture
def seed_buyers(db_session: Session) -> list[Buyer]:
    """Seed sample wholesale B2B buyers into the test database."""
    buyers = [
        Buyer(
            name="Anita Verma",
            company="FabIndia Wholesale Procurement",
            email="anita.verma@fabindia.com",
            phone="+91-98111-22334",
            category="Textiles",
            location="Delhi",
            description="Procuring handloom and artisanal silk & cotton textiles.",
        ),
        Buyer(
            name="Vikram Mehta",
            company="Good Earth Retail",
            email="vikram@goodearth.in",
            phone="+91-98222-33445",
            category="Pottery",
            location="Mumbai",
            description="Seeking authentic handmade pottery, terracotta, and clay crafts.",
        ),
        Buyer(
            name="Priya Sharma",
            company="Jaypore Global Crafts",
            email="priya.sharma@jaypore.com",
            phone="+91-98333-44556",
            category="Handicrafts",
            location="Jaipur",
            description="Exquisite bamboo, wood, and brass handicrafts exporter.",
        ),
    ]
    for b in buyers:
        db_session.add(b)
    db_session.commit()
    for b in buyers:
        db_session.refresh(b)
    return buyers
