import uuid
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.dependencies import get_current_tenant, get_current_user, get_db_session
from app.main import app
from app.models.billing import TenantSubscription

pytestmark = pytest.mark.asyncio


async def test_billing_unconfigured(
    mock_db_session, mock_current_user, mock_current_tenant
):
    original_key = settings.STRIPE_API_KEY
    settings.STRIPE_API_KEY = None

    mock_current_user.role = "tenant_admin"
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_tenant] = lambda: mock_current_tenant

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/billing/portal")
        assert response.status_code == 503
        assert "Billing service is not configured" in response.json()["detail"]
    finally:
        settings.STRIPE_API_KEY = original_key
        app.dependency_overrides.clear()


async def test_get_current_plan_found_and_not_found(
    mock_db_session, mock_current_user, mock_current_tenant
):
    mock_current_user.role = "tenant_admin"
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_tenant] = lambda: mock_current_tenant

    try:
        # 1. Not found
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = None
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            res_404 = await client.get("/api/v1/billing/current-plan")
        assert res_404.status_code == 404

        # 2. Found
        sub = TenantSubscription(
            id=uuid.uuid4(),
            tenant_id=mock_current_tenant.id,
            plan_id=uuid.uuid4(),
            stripe_subscription_id="sub_123",
            stripe_customer_id="cus_123",
            status="active",
        )
        mock_scalars.first.return_value = sub
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            res_200 = await client.get("/api/v1/billing/current-plan")
        assert res_200.status_code == 200
    finally:
        app.dependency_overrides.clear()


async def test_create_stripe_portal_success_and_failures(
    mock_db_session, mock_current_user, mock_current_tenant
):
    original_key = settings.STRIPE_API_KEY
    settings.STRIPE_API_KEY = "sk_test_mock"

    mock_current_user.role = "tenant_admin"
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    app.dependency_overrides[get_current_tenant] = lambda: mock_current_tenant

    try:
        # 1. No customer ID in DB or tenant settings
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        mock_current_tenant.settings = {}
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            res_400 = await client.post("/api/v1/billing/portal")
        assert res_400.status_code == 400

        # 2. Success using customer ID from settings
        mock_current_tenant.settings = {"stripe_customer_id": "cus_123"}
        with patch(
            "stripe.billing_portal.Session.create",
            return_value=MagicMock(url="https://portal.stripe.com/test"),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                res_200 = await client.post("/api/v1/billing/portal")
            assert res_200.status_code == 200
            assert res_200.json()["url"] == "https://portal.stripe.com/test"
    finally:
        settings.STRIPE_API_KEY = original_key
        app.dependency_overrides.clear()


async def test_stripe_webhook_processing(mock_db_session):
    original_secret = settings.STRIPE_WEBHOOK_SECRET
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
    app.dependency_overrides[get_db_session] = lambda: mock_db_session

    try:
        # 1. Invalid signature
        with patch("stripe.Webhook.construct_event", side_effect=Exception("bad sig")):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                res_400 = await client.post(
                    "/api/v1/billing/webhook",
                    content=b"{}",
                    headers={"stripe-signature": "sig"},
                )
            assert res_400.status_code == 400

        # 2. customer.subscription.deleted event
        mock_event_del = {
            "type": "customer.subscription.deleted",
            "data": {"object": {"customer": "cus_del"}},
        }
        with patch("stripe.Webhook.construct_event", return_value=mock_event_del):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                res_del = await client.post(
                    "/api/v1/billing/webhook",
                    content=b"{}",
                    headers={"stripe-signature": "sig"},
                )
            assert res_del.status_code == 200
            mock_db_session.commit.assert_called()

        # 3. invoice.paid event
        mock_event_paid = {
            "type": "invoice.paid",
            "data": {
                "object": {
                    "customer": "cus_paid",
                    "lines": {"data": [{"period": {"end": 1700000000}}]},
                }
            },
        }
        with patch("stripe.Webhook.construct_event", return_value=mock_event_paid):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                res_paid = await client.post(
                    "/api/v1/billing/webhook",
                    content=b"{}",
                    headers={"stripe-signature": "sig"},
                )
            assert res_paid.status_code == 200
    finally:
        settings.STRIPE_WEBHOOK_SECRET = original_secret
        app.dependency_overrides.clear()
