import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from testcontainers.core.container import DockerContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from app.core.config import settings
from app.core.db import get_db_session
from app.main import app
from app.models.base import BaseModel


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def redis_container():
    with RedisContainer("redis:7-alpine") as redis:
        yield redis


@pytest.fixture(scope="session")
def qdrant_container():
    with DockerContainer("qdrant/qdrant:v1.10.1").with_exposed_ports(6333) as qdrant:
        yield qdrant


@pytest.fixture(autouse=True)
def override_settings(postgres_container, redis_container, qdrant_container):
    settings.DATABASE_URL = postgres_container.get_connection_url().replace(
        "postgresql+psycopg2", "postgresql+asyncpg"
    )
    settings.REDIS_URL = f"redis://{redis_container.get_container_host_ip()}:{redis_container.get_exposed_port(6379)}/0"
    settings.QDRANT_HOST = qdrant_container.get_container_host_ip()
    settings.QDRANT_PORT = int(qdrant_container.get_exposed_port(6333))
    settings.SECRET_KEY = "test_super_secret_key"
    yield


@pytest_asyncio.fixture()
async def db_session(postgres_container):
    engine = create_async_engine(settings.DATABASE_URL)

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    TestingSessionLocal = async_sessionmaker(
        autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
    )

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture()
async def client(db_session):
    async def override_get_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
