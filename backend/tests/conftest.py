"""
conftest.py — Pytest shared fixtures.
Sets up a test database and TestClient with overridden dependencies.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.connection import get_db
from app.database.base import Base

import os
import urllib.parse

# URL encode the password because it contains '@' which breaks SQLAlchemy URL parsing
TEST_DB_PASSWORD = os.getenv("TEST_DB_PASSWORD", "NovaTicket@2024!")
DB_PASSWORD = urllib.parse.quote_plus(TEST_DB_PASSWORD)

# --- Test Database Configuration ---
# We use a separate database 'novaticket_test' on the same SQL Server
# Use 'sqlserver' as hostname when running inside Docker, 'localhost' for local dev
TEST_DB_HOST = os.getenv("TEST_DB_HOST", "localhost")

TEST_DATABASE_URL = (
    f"mssql+pyodbc://sa:{DB_PASSWORD}@{TEST_DB_HOST}:1433/novaticket_test"
    "?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes"
)

# Create SQLAlchemy engine for test DB
engine = create_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Creates tables at the beginning of the test session and drops them at the end.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """
    Yields a fresh database session for each test and rolls back changes after.
    Using transactions for each test keeps them isolated and fast.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """
    TestClient for FastAPI app with overridden `get_db` dependency.
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
        
    # Clear overrides after the test
    app.dependency_overrides.clear()
