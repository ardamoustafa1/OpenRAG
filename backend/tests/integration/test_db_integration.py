import pytest
import pytest_asyncio
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from app.models.base import Base
from app.models.tenant import Tenant
from app.models.user import User


@pytest.fixture(scope="session")
def postgres_container():
    """Spins up a real PostgreSQL container for integration testing."""
    with PostgresContainer("postgres:16-alpine", dbname="test_db") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def redis_container():
    """Spins up a real Redis container for integration testing."""
    with RedisContainer("redis:7-alpine") as redis:
        yield redis


@pytest.fixture(scope="session")
def engine(postgres_container):
    """Creates a SQLAlchemy async engine connected to the Testcontainer."""
    # testcontainers provides a sync URL, we need asyncpg
    url = postgres_container.get_connection_url().replace(
        "postgresql+psycopg2", "postgresql+asyncpg"
    )
    engine = create_async_engine(url, echo=False)
    yield engine


@pytest_asyncio.fixture(scope="function")
async def db_session(engine):
    """Creates a fresh DB session for a test and rolls back after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with SessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_postgres_integration_crud(db_session: AsyncSession):
    """Verifies that we can write to and read from the real PostgreSQL DB."""
    # Create Tenant
    tenant = Tenant(name="Integration Test Corp", slug="integration-test-corp")
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)

    assert tenant.id is not None
    assert tenant.name == "Integration Test Corp"

    # Create User for Tenant
    user = User(
        tenant_id=tenant.id,
        email="admin@test.com",
        name="Admin User",
        hashed_password="hashed",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.email == "admin@test.com"
    assert user.tenant_id == tenant.id


@pytest.mark.asyncio
async def test_redis_integration(redis_container):
    """Verifies that we can connect to and use the real Redis Testcontainer."""
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    redis_url = f"redis://{host}:{port}/0"

    redis = Redis.from_url(redis_url)

    await redis.set("test_key", "test_value")
    val = await redis.get("test_key")

    assert val.decode("utf-8") == "test_value"
    await redis.close()
