#!/bin/bash

# TalentSync Code Quality Script
# Runs linting, formatting, and tests across all services

set -e

echo "🔍 Running code quality checks for TalentSync..."

# Services to check
services=("user-service" "interview-service" "resume-service" "media-service" "transcription-service" "feedback-service" "admin-service")

for service in "${services[@]}"; do
    echo "🔧 Checking $service..."
    
    if [ -d "services/$service" ]; then
        cd "services/$service"
        
        # Check if pyproject.toml exists
        if [ -f "pyproject.toml" ]; then
            echo "  📦 Installing dependencies..."
            poetry install --quiet
            
            echo "  🎨 Running Black formatter..."
            poetry run black --check app/ || {
                echo "  ⚠️  Formatting issues found, fixing..."
                poetry run black app/
            }
            
            echo "  📋 Running isort..."
            poetry run isort --check-only app/ || {
                echo "  ⚠️  Import order issues found, fixing..."
                poetry run isort app/
            }
            
            echo "  🔍 Running flake8..."
            poetry run flake8 app/
            
            echo "  🧪 Running tests..."
            if [ -d "tests" ]; then
                poetry run pytest tests/ -v --cov=app --cov-report=term-missing
            else
                echo "  ℹ️  No tests directory found"
            fi
            
            echo "  ✅ $service checks complete"
        else
            echo "  ❌ No pyproject.toml found for $service"
        fi
        
        cd ../..
    else
        echo "  ❌ Service directory not found: $service"
    fi
done

echo "🎉 Code quality checks completed!"
