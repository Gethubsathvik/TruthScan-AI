import pytest
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.database import Base
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

TEST_DB_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
    try:
        if os.path.exists("test.db"):
            os.remove("test.db")
    except PermissionError:
        pass

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def mock_search_results():
    return [
        {
            "url": "https://example.com/article1",
            "title": "Example News Article",
            "snippet": "This is a test snippet about the claim.",
            "score": 0.9,
            "published_date": "2024-01-01"
        },
        {
            "url": "https://gov.example.com/announcement",
            "title": "Official Government Announcement",
            "snippet": "Official statement regarding the matter.",
            "score": 0.95,
            "published_date": "2024-01-02"
        }
    ]

@pytest.fixture
def sample_claim():
    return {
        "text": "NASA discovered life on Mars in 2026.",
        "subject": "NASA",
        "action": "discovered",
        "object": "life on Mars",
        "location": "Mars",
        "date_time": "2026",
        "numerical_values": "2026",
        "entities": "NASA, Mars",
        "certainty_level": "medium"
    }

@pytest.fixture
def sample_source():
    return {
        "url": "https://nasa.gov/news",
        "title": "NASA News",
        "domain": "nasa.gov",
        "source_type": "primary",
        "publisher": "NASA",
        "publication_date": "2024-01-01",
        "credibility_score": 0.9,
        "is_independent": True
    }
