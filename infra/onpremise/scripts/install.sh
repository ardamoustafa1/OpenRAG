#!/bin/bash
set -e

echo "======================================"
echo "Enterprise AI Platform Installer"
echo "======================================"

read -p "Enter Base Domain (e.g., platform.internal.corp): " DOMAIN
read -p "Enter Super Admin Email: " ADMIN_EMAIL

# Generate secure secrets
JWT_SECRET=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -base64 16)

echo "Deploying Helm Chart..."
helm upgrade --install ai-platform ../../helm/ai-platform \
  --namespace ai-platform --create-namespace \
  --set ingress.hosts.tenantWildcard="*.$DOMAIN" \
  --set postgresql.auth.password="$DB_PASSWORD" \
  --wait --timeout 10m

echo "✅ Installation Complete."
echo "Access the admin panel at: https://admin.$DOMAIN"
echo "Initial Admin User: $ADMIN_EMAIL"
