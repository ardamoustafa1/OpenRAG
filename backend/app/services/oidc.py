from authlib.integrations.starlette_client import OAuth
from fastapi import Request
from starlette.config import Config

# This is a dynamic factory approach for multi-tenant OIDC.
# Normally, Authlib uses a static Config, but for multi-tenant,
# we configure OAuth dynamically per request/tenant.


class OIDCService:
    def __init__(self):
        # We can store instances of oauth per tenant or dynamically create them
        self.oauth_clients = {}

    def get_client(self, tenant_slug: str, oidc_settings: dict):
        """
        Retrieves or creates an Authlib client for a specific tenant based on their settings.
        oidc_settings should contain:
        - client_id
        - client_secret
        - server_metadata_url (Discovery URL)
        """
        if tenant_slug not in self.oauth_clients:
            oauth = OAuth(Config(environ=oidc_settings))
            oauth.register(
                name=tenant_slug,
                client_id=oidc_settings.get("client_id"),
                client_secret=oidc_settings.get("client_secret"),
                server_metadata_url=oidc_settings.get("server_metadata_url"),
                client_kwargs={"scope": "openid email profile"},
            )
            self.oauth_clients[tenant_slug] = getattr(oauth, tenant_slug)

        return self.oauth_clients[tenant_slug]

    async def generate_login_url(self, client, request: Request, redirect_uri: str):
        """Generates the authorization URL to redirect the user."""
        return await client.authorize_redirect(request, redirect_uri)

    async def verify_callback(self, client, request: Request):
        """Exchanges the authorization code for an access token and user info."""
        token = await client.authorize_access_token(request)
        userinfo = token.get("userinfo")
        # userinfo typically contains: sub, name, email, etc.
        return userinfo


oidc_service = OIDCService()
