#!/usr/bin/env python
"""
TalentSync Health Check Script

This script checks the health of all TalentSync services and provides detailed status information.
It can be used to verify that all components of the system are running correctly.
"""

import sys
import json
import requests
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Tuple, List, Optional, Any
from dataclasses import dataclass
import time
import os

# Service configuration with descriptions and dependencies
@dataclass
class ServiceInfo:
    url: str
    description: str
    port: int
    dependencies: List[str] = None
    additional_endpoints: Dict[str, str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.additional_endpoints is None:
            self.additional_endpoints = {}

# Define the service architecture
SERVICES = {
    "User Service": ServiceInfo(
        url="http://localhost:8001/api/v1/health",
        description="Authentication & profile management",
        port=8001,
        dependencies=[],
        additional_endpoints={
            "Docs": "http://localhost:8001/docs",
            "API Status": "http://localhost:8001/api/v1/health"
        }
    ),
    "Media Service": ServiceInfo(
        url="http://localhost:8002/api/v1/health",
        description="Audio/video handling",
        port=8002,
        dependencies=["User Service"],
        additional_endpoints={
            "Docs": "http://localhost:8002/docs",
            "API Status": "http://localhost:8002/api/v1/health"
        }
    ),
    "Interview Service": ServiceInfo(
        url="http://localhost:8003/api/v1/health", 
        description="Core interview orchestration",
        port=8003,
        dependencies=["User Service", "Media Service"],
        additional_endpoints={
            "Docs": "http://localhost:8003/docs",
            "Database": "http://localhost:8003/api/v1/health/database",
            "Vector DB": "http://localhost:8003/api/v1/health/vector"
        }
    ),
    "Resume Service": ServiceInfo(
        url="http://localhost:8004/api/v1/health",
        description="Resume parsing & storage",
        port=8004,
        dependencies=["User Service"],
        additional_endpoints={
            "Docs": "http://localhost:8004/docs",
            "API Status": "http://localhost:8004/api/v1/health"
        }
    ),
    "Transcription Service": ServiceInfo(
        url="http://localhost:8005/api/v1/health",
        description="Speech-to-text & text-to-speech",
        port=8005, 
        dependencies=["Media Service"],
        additional_endpoints={
            "Docs": "http://localhost:8005/docs",
            "API Status": "http://localhost:8005/api/v1/health"
        }
    ),
    "Feedback Service": ServiceInfo(
        url="http://localhost:8006/api/v1/health",
        description="Post-interview analytics",
        port=8006,
        dependencies=["Interview Service", "Transcription Service"],
        additional_endpoints={
            "Docs": "http://localhost:8006/docs",
            "API Status": "http://localhost:8006/api/v1/health"
        }
    ),
    "Frontend": ServiceInfo(
        url="http://localhost:3000",
        description="React web application",
        port=3000,
        dependencies=["Nginx Proxy"]
    ),
    "Nginx Proxy": ServiceInfo(
        url="http://localhost/health",
        description="API gateway & reverse proxy",
        port=80,
        dependencies=[]
    ),
}

@dataclass
class ServiceResult:
    name: str
    is_healthy: bool
    message: str
    response_time: float
    details: Optional[Dict[str, Any]] = None

def check_service(name: str, service: ServiceInfo) -> ServiceResult:
    """Check if a service is healthy and get response details."""
    start_time = time.time()
    try:
        response = requests.get(service.url, timeout=5)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            # Try to parse JSON details if available
            details = None
            try:
                if response.text and response.text.strip():
                    details = response.json()
            except json.JSONDecodeError:
                details = {"text": response.text[:100]}
                
            return ServiceResult(
                name=name, 
                is_healthy=True, 
                message=f"✓ {response.status_code} ({response_time*1000:.0f}ms)",
                response_time=response_time,
                details=details
            )
        else:
            return ServiceResult(
                name=name, 
                is_healthy=False, 
                message=f"✗ {response.status_code}: {response.text[:100]}",
                response_time=response_time
            )
    except requests.exceptions.RequestException as e:
        response_time = time.time() - start_time
        return ServiceResult(
            name=name, 
            is_healthy=False, 
            message=f"✗ Connection Error: {str(e)[:100]}",
            response_time=response_time
        )

def check_all_services(verbose: bool = False) -> List[ServiceResult]:
    """Check health of all services in parallel."""
    results = []
    
    with ThreadPoolExecutor(max_workers=len(SERVICES)) as executor:
        future_to_service = {
            executor.submit(check_service, name, service): name
            for name, service in SERVICES.items()
        }
        
        for future in as_completed(future_to_service):
            results.append(future.result())
    
    return sorted(results, key=lambda x: x.name)

def get_service_start_command(name: str) -> str:
    """Get the command to start a service if it's down."""
    if name == "Frontend":
        return "cd frontend && npm start"
    elif name == "Nginx Proxy":
        return "docker-compose up -d nginx"
    elif "Service" in name:
        service_name = name.lower().replace(" ", "-")
        return f"docker-compose up -d {service_name}"
    else:
        return "docker-compose up -d"

def print_service_details(name: str, service: ServiceInfo, result: ServiceResult):
    """Print detailed information about a service."""
    status_color = "\033[92m" if result.is_healthy else "\033[91m"  # Green or Red
    reset_color = "\033[0m"
    
    print(f"\n{status_color}{'=' * 50}{reset_color}")
    print(f"{status_color}Service: {name} (Port: {service.port}){reset_color}")
    print(f"{status_color}{'=' * 50}{reset_color}")
    print(f"Description: {service.description}")
    print(f"Health URL: {service.url}")
    print(f"Status: {result.message}")
    print(f"Response Time: {result.response_time*1000:.2f}ms")
    
    if service.dependencies:
        print(f"Dependencies: {', '.join(service.dependencies)}")
    
    if service.additional_endpoints:
        print("\nAdditional Endpoints:")
        for name, url in service.additional_endpoints.items():
            print(f"- {name}: {url}")
    
    if result.details:
        print("\nResponse Details:")
        try:
            print(json.dumps(result.details, indent=2))
        except:
            print(str(result.details))
    
    if not result.is_healthy:
        print(f"\nTroubleshooting:")
        print(f"- Check if the service is running: docker-compose ps | grep {name.lower().replace(' ', '-')}")
        print(f"- View service logs: docker-compose logs {name.lower().replace(' ', '-')}")
        print(f"- Restart the service: {get_service_start_command(name)}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Check health of TalentSync services')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed information')
    parser.add_argument('-s', '--service', help='Check specific service')
    args = parser.parse_args()
    
    print("\n📊 TalentSync Service Health Check")
    print("=" * 50)
    
    if args.service:
        # Check specific service
        if args.service not in SERVICES:
            print(f"Error: Service '{args.service}' not found")
            print(f"Available services: {', '.join(SERVICES.keys())}")
            return 1
            
        service = SERVICES[args.service]
        result = check_service(args.service, service)
        print_service_details(args.service, service, result)
        return 0 if result.is_healthy else 1
    
    # Check all services
    results = check_all_services(args.verbose)
    healthy_count = sum(1 for result in results if result.is_healthy)
    
    # Print results in a nice table
    max_name_length = max(len(result.name) for result in results)
    
    for result in results:
        status_symbol = "✓" if result.is_healthy else "✗"
        status_color = "\033[92m" if result.is_healthy else "\033[91m"  # Green or Red
        reset_color = "\033[0m"
        
        print(f"{result.name:<{max_name_length + 2}} {status_color}{status_symbol} {result.message}{reset_color}")
    
    print("=" * 50)
    print(f"Status: {healthy_count}/{len(SERVICES)} services healthy")
    
    if args.verbose:
        print("\nDetailed Service Information:")
        for result in results:
            if not result.is_healthy or args.verbose:
                service_info = SERVICES[result.name]
                print_service_details(result.name, service_info, result)
    
    if healthy_count == len(SERVICES):
        print("\n✅ All systems operational!")
        return 0
    else:
        print("\n⚠️ Some services are not healthy!")
        
        # Suggest how to fix issues
        print("\nTroubleshooting steps:")
        print("1. Make sure Docker is running")
        print("2. Check if all services are up: docker-compose ps")
        print("3. View service logs: docker-compose logs [service-name]")
        print("4. Restart all services: docker-compose down && docker-compose up -d")
        print("5. Run with --verbose flag for more details on each service")
        
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCheck cancelled by user")
        sys.exit(130)
