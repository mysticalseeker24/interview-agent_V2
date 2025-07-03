#!/bin/bash

# TalentSync Cleanup Script
# Stops all services and cleans up Docker resources

set -e

echo "🧹 Cleaning up TalentSync environment..."

# Stop and remove containers
echo "🛑 Stopping services..."
cd infra
docker-compose down

# Remove unused Docker resources
echo "🗑️  Removing unused Docker resources..."
docker system prune -f

# Remove volumes (optional - uncomment if needed)
# echo "📦 Removing volumes..."
# docker volume prune -f

echo "✅ Cleanup complete!"
