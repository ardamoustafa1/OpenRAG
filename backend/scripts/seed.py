import asyncio
import os
import sys
import uuid

import structlog

# Add the /app directory to sys.path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import async_session_maker

from app.core.security import get_password_hash
from app.models.tenant import Tenant
from app.models.user import User

logger = structlog.get_logger()


async def seed():
    async with async_session_maker() as session:
        # Create Tenant
        tenant_id = uuid.uuid4()
        tenant = Tenant(
            id=tenant_id,
            name="Acme Corp",
            slug="acme-corp",
            plan="enterprise",
            settings={},
        )
        session.add(tenant)

        # Create Admin User
        admin_user = User(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            email="admin@openrag.local",
            name="Admin User",
            role="admin",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        session.add(admin_user)

        await session.commit()
        logger.info(
            "Successfully seeded database with admin@openrag.local / password123"
        )


if __name__ == "__main__":
    asyncio.run(seed())
