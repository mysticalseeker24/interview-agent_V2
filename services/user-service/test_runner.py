#!/usr/bin/env python3
"""
Test runner for TalentSync User Service.

This script runs the integration tests against the live Supabase backend.
Make sure to set the required environment variables before running.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from dotenv import load_dotenv

def check_environment():
    """Check that required environment variables are set."""
    # Load environment variables from .env file
    service_dir = Path(__file__).parent
    env_file = service_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")
    else:
        print(f"⚠️  No .env file found at {env_file}")
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY", 
        "SUPABASE_SERVICE_ROLE_KEY",
        "SECRET_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file or environment.")
        return False
    
    # Set default test values if not provided
    if not os.getenv("TEST_EMAIL"):
        os.environ["TEST_EMAIL"] = "saksham.mishra2402@gmail.com"
    if not os.getenv("TEST_PASSWORD"):
        os.environ["TEST_PASSWORD"] = "TestPass123"
    if not os.getenv("TEST_FULL_NAME"):
        os.environ["TEST_FULL_NAME"] = "Saksham Mishra"
    
    print("✅ Environment variables configured")
    return True

def run_tests(test_type="all", verbose=False):
    """Run the specified test suite."""
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if test_type == "auth":
        cmd.append("tests/test_auth.py")
    elif test_type == "users":
        cmd.append("tests/test_users.py")
    elif test_type == "integration":
        cmd.append("tests/test_integration.py")
    else:
        cmd.append("tests/")
    
    print(f"🚀 Running {test_type} tests...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("✅ All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed with exit code {e.returncode}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run TalentSync User Service tests")
    parser.add_argument(
        "--type", 
        choices=["all", "auth", "users", "integration"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Change to the service directory
    service_dir = Path(__file__).parent
    os.chdir(service_dir)
    
    # Load environment variables early
    env_file = service_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    print("🧪 TalentSync User Service Test Runner")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Run tests
    success = run_tests(args.type, args.verbose)
    
    if success:
        print("\n🎉 Test run completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Test run failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 