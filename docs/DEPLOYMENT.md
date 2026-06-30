# Production Deployment Guide

The Enterprise RAG Platform is built to be deployed on any CNCF-certified Kubernetes cluster. This guide details the steps required to deploy the system securely with High Availability (HA).

## 1. Prerequisites

- Kubernetes Cluster (v1.28+)
- Helm 3.x
- **cert-manager** installed (for TLS).
- **External Secrets Operator** (optional, but highly recommended).
- **NVIDIA GPU Nodes** (Required if using vLLM for local LLM inference).

---

## 2. Helm Configuration (`values.yaml`)

The platform is distributed as an umbrella Helm chart (`infra/helm/ai-platform`). Before deploying, customize your `values.yaml` file.

### Overriding Resource Limits & GPUs
If you are deploying local models via `vLLM`, you must ensure your Kubernetes cluster has GPU node pools and the NVIDIA device plugin installed.

```yaml
vllm:
  enabled: true
  model: "Qwen/Qwen2.5-72B-Instruct-AWQ"
  gpuNodeSelector:
    accelerator: nvidia-gpu
  resources:
    limits:
      nvidia.com/gpu: "2" # Number of GPUs to allocate to vLLM
```

### High Availability (HPA)
The API and Frontend can automatically scale based on CPU pressure. Ensure `metrics-server` is running in your cluster.

```yaml
backend:
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 20
    targetCPUUtilizationPercentage: 75
```

---

## 3. Secrets Management

Do **not** commit sensitive keys (e.g., `SECRET_KEY`, `MINIO_SECRET_KEY`) in plain text to your repository. 

### Method A: Native Kubernetes Secrets (Simpler)
Before installing the Helm chart, create a secret manually:

```bash
kubectl create secret generic ai-platform-secret \
  --from-literal=SECRET_KEY=$(openssl rand -hex 32) \
  --from-literal=POSTGRES_PASSWORD=SuperSecure123 \
  --from-literal=MINIO_SECRET_KEY=MinioAdminKey!
```
Ensure your `values.yaml` points the deployment to read from `ai-platform-secret`.

### Method B: External Secrets Operator (Enterprise Standard)
Integrate with AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault. Create an `ExternalSecret` custom resource:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: platform-secrets
spec:
  refreshInterval: "1h"
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: ai-platform-secret # The secret name the Helm chart expects
  data:
  - secretKey: SECRET_KEY
    remoteRef:
      key: openrag/prod/api
      property: SECRET_KEY
```

---

## 4. TLS & Ingress Configuration

The Helm chart includes a `traefik` IngressRoute configuration. You must have `cert-manager` configured to issue certificates automatically (e.g., via Let's Encrypt).

Update your `values.yaml`:

```yaml
ingress:
  enabled: true
  className: "traefik"
  tls:
    enabled: true
    secretName: "platform-tls-secret" # cert-manager will populate this
  hosts:
    backend: "api.yourcompany.com"
    frontend: "app.yourcompany.com"
```

Create a `Certificate` CRD pointing to your ClusterIssuer:

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: openrag-cert
spec:
  secretName: platform-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - "app.yourcompany.com"
  - "api.yourcompany.com"
```

---

## 5. Deployment Execution

Once `values.yaml` is configured and secrets are primed, deploy the stack:

```bash
helm upgrade --install openrag infra/helm/ai-platform \
  -f values-prod.yaml \
  --namespace openrag-prod \
  --create-namespace \
  --atomic \
  --timeout 10m
```

Check the status of all pods:

```bash
kubectl get pods -n openrag-prod -w
```

## 6. Post-Deployment (Migrations)

Wait for the `postgresql` pod to reach `Running` state, then execute Alembic migrations inside one of the backend pods:

```bash
BACKEND_POD=$(kubectl get pods -n openrag-prod -l app.kubernetes.io/component=backend -o jsonpath='{.items[0].metadata.name}')

kubectl exec -it $BACKEND_POD -n openrag-prod -- alembic upgrade head
```

The system is now live and ready to accept traffic.
