#!/bin/bash
set -e

echo "Running Pre-flight Checks for Enterprise AI Platform..."

# 1. Check K8s Version
K8S_VERSION=$(kubectl version --short | grep Server | awk '{print $3}' | tr -d 'v')
MIN_K8S="1.27.0"
if [ "$(printf '%s\n' "$MIN_K8S" "$K8S_VERSION" | sort -V | head -n1)" = "$MIN_K8S" ]; then 
    echo "✅ K8s Version Valid ($K8S_VERSION)"
else
    echo "❌ K8s Version too old. Need >= $MIN_K8S"
    exit 1
fi

# 2. Check Tools
for tool in helm curl tar; do
    if ! command -v $tool &> /dev/null; then
        echo "❌ $tool could not be found"
        exit 1
    fi
done
echo "✅ Required CLI tools present."

# 3. Check Resources (Rough estimate)
TOTAL_CPU=$(kubectl get nodes -o jsonpath='{sum(.items[*].status.capacity.cpu)}')
if [ "$TOTAL_CPU" -lt 32 ]; then
    echo "⚠️ Warning: Total cluster CPU ($TOTAL_CPU) is less than recommended 32 cores."
else
    echo "✅ Sufficient CPU capacity."
fi

echo "Pre-flight check completed successfully."
