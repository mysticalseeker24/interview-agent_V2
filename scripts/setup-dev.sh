#!/bin/bash

# TalentSync Development Setup Script
# This script sets up the development environment for TalentSync

set -e

echo "🚀 Setting up TalentSync development environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create environment files from examples
echo "📝 Creating environment files..."
for service in user-service interview-service resume-service media-service transcription-service feedback-service admin-service; do
    if [ ! -f "services/$service/.env" ]; then
        cp "services/$service/.env.example" "services/$service/.env"
        echo "✅ Created .env file for $service"
    else
        echo "ℹ️  .env file already exists for $service"
    fi
done

# Build and start services
echo "🔧 Building and starting services..."
cd infra
docker-compose up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
services=("user-service:8001" "interview-service:8002" "resume-service:8003" "media-service:8004" "transcription-service:8005" "feedback-service:8006" "admin-service:8007")

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if curl -f "http://localhost:$port/health" &> /dev/null; then
        echo "✅ $name is healthy"
    else
        echo "❌ $name is not responding"
    fi
done

echo "🎉 TalentSync development environment is ready!"
echo "📖 Access the API documentation at:"
echo "   - User Service: http://localhost:8001/docs"
echo "   - Interview Service: http://localhost:8002/docs"
echo "   - Resume Service: http://localhost:8003/docs"
echo "   - Media Service: http://localhost:8004/docs"
echo "   - Transcription Service: http://localhost:8005/docs"
echo "   - Feedback Service: http://localhost:8006/docs"
echo "   - Admin Service: http://localhost:8007/docs"
echo "🔧 API Gateway: http://localhost"
