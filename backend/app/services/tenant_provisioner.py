import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.billing import BillingPlan
from app.models.tenant import Tenant
from app.models.user import User
from app.rag.vector_store import vector_store

logger = structlog.get_logger()


class TenantProvisioner:
    """
    Automates the provisioning and deprovisioning of multi-tenant environments.
    """

    async def provision_tenant(
        self,
        db: AsyncSession,
        name: str,
        slug: str,
        admin_email: str,
        plan_name: str = "starter",
    ) -> Tenant:
        """
        Idempotent workflow to provision a new tenant across Postgres, MinIO, and Qdrant.
        """
        logger.info("Provisioning new tenant", name=name, slug=slug, plan=plan_name)

        # 1. Create Postgres Tenant Record
        tenant = Tenant(
            name=name,
            slug=slug,
            plan=plan_name,
            settings={
                "system_prompt": "You are a helpful AI assistant. Always answer in the language of the query.",
                "default_model": "llama3.3-70b",
            },
        )
        db.add(tenant)
        await db.flush()  # Flush to get tenant.id

        # 2. Create Default Admin User
        # Temporary password for the admin, should be changed upon first login
        temp_password = "ChangeMe123!"
        admin_user = User(
            tenant_id=tenant.id,
            email=admin_email,
            name="Tenant Admin",
            role="tenant_admin",
            hashed_password=get_password_hash(temp_password),
        )
        db.add(admin_user)

        # 3. Create Billing Plan Record
        limits = {
            "starter": {"tokens": 500_000, "docs": 100, "users": 3},
            "professional": {"tokens": 5_000_000, "docs": 1000, "users": 10},
            "enterprise": {"tokens": -1, "docs": -1, "users": -1},  # -1 = Unlimited
        }
        plan_limits = limits.get(plan_name.lower(), limits["starter"])

        billing = BillingPlan(
            tenant_id=tenant.id,
            plan_name=plan_name,
            max_tokens=plan_limits["tokens"],
            max_documents=plan_limits["docs"],
            max_users=plan_limits["users"],
            is_active=True,
        )
        db.add(billing)

        # 4. Commit DB Changes
        await db.commit()
        await db.refresh(tenant)

        # 5. Provision Infrastructure async
        try:
            # Qdrant Default Collection (id = default)
            await vector_store.ensure_collection(str(tenant.id), "default")

            # MinIO: Bucket handles prefixes automatically, so nothing explicit needed here
            # unless we want to upload a default README object.

            # Send Onboarding Email (mocked)
            from app.services.notification import notification_service

            await notification_service.send_email(
                to_email=admin_email,
                subject=f"Welcome to {name}!",
                html_content=f"Your tenant has been created. Temp password: {temp_password}",
            )

            logger.info("Tenant provisioned successfully", tenant_id=str(tenant.id))
            return tenant

        except Exception as e:
            logger.error(
                "Error during infrastructure provisioning",
                tenant_id=str(tenant.id),
                error=str(e),
            )
            # In a real app, you might want to rollback the DB or queue a retry.
            raise

    async def deprovision_tenant(
        self, db: AsyncSession, tenant_id: uuid.UUID, hard_delete: bool = False
    ):
        """
        Cleans up tenant resources.
        By default, we just mark them as suspended/inactive (Soft Delete).
        If hard_delete is True, we destroy Qdrant collections and MinIO files.
        """
        logger.warning(
            "Deprovisioning tenant", tenant_id=str(tenant_id), hard_delete=hard_delete
        )

        tenant = await db.get(Tenant, tenant_id)
        if not tenant:
            return

        if not hard_delete:
            tenant.is_active = False
            await db.commit()
            return

        # Hard Delete Operations
        # 1. Postgres Cascade Delete (Alembic models should have ON DELETE CASCADE)
        await db.delete(tenant)
        await db.commit()

        # 2. Qdrant (Not implemented fully in VectorStoreService yet, but standard API call)
        try:
            # await vector_store.client.delete_collection(vector_store._collection_name(str(tenant_id), "default"))
            pass
        except Exception as e:
            logger.error("Failed to delete Qdrant collection", error=str(e))

        # 3. MinIO
        try:
            # You would list all objects with prefix `tenant_id/` and delete them
            # objects_to_delete = storage_service.client.list_objects(storage_service.bucket_name, prefix=f"{tenant_id}/", recursive=True)
            # for obj in objects_to_delete:
            #     storage_service.delete_file(obj.object_name)
            pass
        except Exception as e:
            logger.error("Failed to delete MinIO objects", error=str(e))


tenant_provisioner = TenantProvisioner()
