#!/bin/bash
set -e

# Configuration
VM_NAME="video-searching-api"
ZONE="us-central1-a"
GCLOUD="source ~/google-cloud-sdk/path.zsh.inc && gcloud"

echo "🚀 Deploying Video Searching Agent..."

# Step 1: Create tarball
echo "📦 Creating tarball..."
tar --exclude='.venv' --exclude='.git' --exclude='__pycache__' \
    --exclude='*.pyc' --exclude='.env' --exclude='.mypy_cache' \
    --exclude='.pytest_cache' --exclude='.ruff_cache' \
    -czf /tmp/video-searching-agent.tar.gz .

# Step 2: Copy to VM
echo "📤 Copying to VM..."
eval "$GCLOUD compute scp /tmp/video-searching-agent.tar.gz $VM_NAME:~ --zone=$ZONE"

# Step 3: Deploy on VM
echo "🔨 Building and deploying on VM..."
eval "$GCLOUD compute ssh $VM_NAME --zone=$ZONE --command='
    cd ~/app &&
    tar -xzf ~/video-searching-agent.tar.gz &&
    sudo docker stop video-api 2>/dev/null || true &&
    sudo docker rm video-api 2>/dev/null || true &&
    sudo docker build -t video-searching-agent . &&
    sudo docker run -d \
        --name video-api \
        --restart=unless-stopped \
        -p 80:8000 \
        --env-file .env \
        video-searching-agent
'"

# Step 4: Health check
echo "🏥 Running health check..."
VM_IP=$(eval "$GCLOUD compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)'")

sleep 5
for i in {1..6}; do
    if curl -sf "http://$VM_IP/api/v1/health" > /dev/null; then
        echo "✅ Deployment successful! API is healthy at http://$VM_IP"
        exit 0
    fi
    echo "Waiting for API to start... (attempt $i/6)"
    sleep 5
done

echo "❌ Health check failed"
exit 1
