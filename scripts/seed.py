import asyncio
import os
import sys

# Ensure backend directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from passlib.context import CryptContext
from sqlalchemy import text
from app.core.db import async_session_factory
from app.models import Tenant, User, BillingPlan, DocumentCollection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_database():
    """Seeds the database with initial plans, tenants, users, and collections."""
    print("Starting database seeding...")

    async with async_session_factory() as session:
        # 1. Create Billing Plans
        print("Creating Billing Plans...")
        plans = [
            BillingPlan(
                name="Free",
                max_users=1,
                max_documents=10,
                max_tokens_per_month=100000,
                max_collections=1,
                price_usd_monthly=0.0
            ),
            BillingPlan(
                name="Professional",
                max_users=10,
                max_documents=500,
                max_tokens_per_month=5000000,
                max_collections=10,
                price_usd_monthly=49.0
            ),
            BillingPlan(
                name="Enterprise",
                max_users=9999,
                max_documents=99999,
                max_tokens_per_month=999999999,
                max_collections=9999,
                price_usd_monthly=499.0
            )
        ]
        session.add_all(plans)
        await session.commit()
        
        # We need to temporarily disable RLS or just run without tenant_id context
        # because the seed script creates tenants and their users globally.
        # By default, connection has no app.current_tenant_id set, 
        # so queries normally fail RLS. 
        # But wait, our RLS says `USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID)`
        # If the variable isn't set, it evaluates to NULL.
        # RLS policies with NULL evaluate to false.
        # However, if we connect as the table owner (postgres default user), we bypass RLS by default.
        # Let's assume the script runs as 'postgres' superuser which bypasses RLS.

        # 2. Create Tenants
        print("Creating Tenants...")
        tenants_data = [
            {"name": "Acme Corp", "slug": "acme", "plan": "Professional"},
            {"name": "Globex Inc", "slug": "globex", "plan": "Enterprise"},
            {"name": "StartUp LLC", "slug": "startup", "plan": "Free"}
        ]
        
        tenants = []
        for t in tenants_data:
            tenant = Tenant(name=t["name"], slug=t["slug"], plan=t["plan"])
            session.add(tenant)
            tenants.append(tenant)
        
        await session.commit()

        # 3. Create Users & Collections for each tenant
        for i, tenant in enumerate(tenants):
            print(f"Creating data for Tenant: {tenant.name}")
            
            # Admin User
            admin = User(
                tenant_id=tenant.id,
                email=f"admin@{tenant.slug}.com",
                name="Admin User",
                role="tenant_admin",
                hashed_password=pwd_context.hash("AdminPassword123!")
            )
            
            # Normal User
            user = User(
                tenant_id=tenant.id,
                email=f"user@{tenant.slug}.com",
                name="Normal User",
                role="editor",
                hashed_password=pwd_context.hash("UserPassword123!")
            )
            session.add_all([admin, user])
            
            # Flush to get user IDs
            await session.flush()

            # Collection
            collection = DocumentCollection(
                tenant_id=tenant.id,
                name="General Knowledge Base",
                description="Default collection for company documents",
                created_by=admin.id
            )
            session.add(collection)

        await session.commit()
        print("Database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
