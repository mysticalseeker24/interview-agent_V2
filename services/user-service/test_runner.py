#!/usr/bin/env python3
"""
Test runner script for User Service.

Usage:
    python test_runner.py              # Run all tests
    python test_runner.py auth         # Run auth tests only
    python test_runner.py users        # Run users tests only
    python test_runner.py integration  # Run integration tests only
    python test_runner.py --coverage   # Run tests with coverage report
"""
import subprocess
import sys
import os
from pathlib import Path

# Ensure we're in the correct directory
service_dir = Path(__file__).parent
os.chdir(service_dir)

# Set environment variables for testing
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "15"


def run_command(cmd):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode


def main():
    """Main test runner function."""
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg == "--coverage":
            # Run all tests with coverage
            cmd = ["python", "-m", "pytest", "tests/", "-v", "--cov=app", "--cov-report=html", "--cov-report=term"]
        elif arg == "auth":
            # Run auth tests only
            cmd = ["python", "-m", "pytest", "tests/test_auth.py", "-v"]
        elif arg == "users":
            # Run users tests only
            cmd = ["python", "-m", "pytest", "tests/test_users.py", "-v"]
        elif arg == "integration":
            # Run integration tests only
            cmd = ["python", "-m", "pytest", "tests/test_integration.py", "-v"]
        elif arg in ["--help", "-h"]:
            print(__doc__)
            return 0
        else:
            print(f"Unknown argument: {arg}")
            print(__doc__)
            return 1
    else:
        # Run all tests
        cmd = ["python", "-m", "pytest", "tests/", "-v"]
    
    return run_command(cmd)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
