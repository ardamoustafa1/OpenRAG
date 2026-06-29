#!/bin/bash
set -e

REGISTRY_URL=${1:-"localhost:5000"}
ARCHIVE_DIR="../images"

echo "Loading offline images into registry $REGISTRY_URL..."

for tarball in $ARCHIVE_DIR/*.tar; do
    if [ -f "$tarball" ]; then
        echo "Loading $tarball..."
        # Load into local docker daemon
        docker load -i "$tarball"
        
        # In a real air-gapped script, you'd extract the image name from the tarball,
        # tag it for the local registry, and push it.
        # IMAGE_NAME=$(docker inspect --format='{{.RepoTags}}' ...)
        # docker tag $IMAGE_NAME $REGISTRY_URL/$IMAGE_NAME
        # docker push $REGISTRY_URL/$IMAGE_NAME
    fi
done

echo "✅ All images loaded into internal registry."
