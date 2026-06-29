#!/bin/bash
set -e

echo "Initiating platform upgrade..."

# 1. Trigger backup before upgrade
velero backup create pre-upgrade-$(date +%s) --include-namespaces ai-platform --wait

# 2. Atomic Helm Upgrade
echo "Upgrading Helm Release..."
helm upgrade ai-platform ../../helm/ai-platform \
  --namespace ai-platform \
  --reuse-values \
  --atomic \
  --timeout 15m

# 3. Alembic Migrations
echo "Running database migrations..."
BACKEND_POD=$(kubectl get pods -n ai-platform -l app.kubernetes.io/name=backend -o jsonpath="{.items[0].metadata.name}")
kubectl exec -n ai-platform $BACKEND_POD -- alembic upgrade head

echo "✅ Upgrade completed successfully."
