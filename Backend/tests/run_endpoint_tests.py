#!/usr/bin/env python3
"""
Endpoint Test Runner

This script runs the comprehensive endpoint test suite and provides
detailed reporting of results and issues found.

Usage:
    python run_endpoint_tests.py

Author: Mentor AI Team
Version: 1.0.0
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('.env')

def run_test_suite():
    """Run the comprehensive test suite"""
    print("🚀 Starting Mentor AI Platform Endpoint Testing")
    print("=" * 60)
    
    # Check if required environment variables are set
    print("\n🔍 Checking environment...")
    
    required_vars = [
        "API_BASE_URL",
        "TEST_EMAIL",
        "TEST_PASSWORD",
        "TEST_PHONE",
        "TEST_CHILD_USERNAME",
        "TEST_CHILD_PASSWORD"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("   Please set these variables and run again")
        return False
    
    print("✅ All required environment variables are set")
    
    # Run the comprehensive test suite
    print("\n🧪 Running comprehensive test suite...")
    print("-" * 60)
    
    try:
        # Run the test suite
        result = subprocess.run([
            sys.executable, 
            "tests/test_all_endpoints.py"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print(result.stdout)
        
        if result.returncode != 0:
            print(f"\n❌ Test suite failed with exit code: {result.returncode}")
            print("\nStderr:")
            print(result.stderr)
            return False
        else:
            print("\n✅ Test suite completed successfully")
            return True
    
    except Exception as e:
        print(f"\n❌ Error running test suite: {e}")
        return False

def check_server_status():
    """Check if the server is running"""
    print("\n🔍 Checking server status...")
    
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    health_url = f"{base_url}/health"
    
    try:
        import requests
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            print("✅ Server is running and accessible")
            return True
        else:
            print(f"⚠️  Server returned status {response.status_code}")
            print("   Please ensure the server is running")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("   Please start the server before running tests")
        return False

def generate_test_report():
    """Generate a detailed test report"""
    print("\n📄 Generating test report...")
    
    report = {
        "test_run": {
            "timestamp": datetime.now().isoformat(),
            "platform": "Mentor AI EdTech Platform",
            "test_type": "Comprehensive Endpoint Testing"
        },
        "environment": {
            var: os.getenv(var, "NOT_SET") 
            for var in [
                "API_BASE_URL",
                "TEST_EMAIL",
                "TEST_PASSWORD",
                "TEST_PHONE",
                "TEST_CHILD_USERNAME",
                "TEST_CHILD_PASSWORD"
            ]
        },
        "issues_found": [],
        "recommendations": []
    }
    
    # Save report
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Test report saved to: {report_file}")
        return report_file
    except Exception as e:
        print(f"❌ Error saving test report: {e}")
        return None

def main():
    """Main function"""
    print("Mentor AI Platform - Endpoint Test Runner")
    print("=" * 60)
    
    # Check server status
    if not check_server_status():
        print("\n❌ Server is not running. Please start the server and try again.")
        return 1
    
    # Run test suite
    if not run_test_suite():
        print("\n❌ Test suite failed. Please check the errors above.")
        return 1
    
    # Generate report
    report_file = generate_test_report()
    
    print("\n" + "=" * 60)
    print("🏁 Endpoint Testing Complete!")
    
    if report_file:
        print(f"📄 Detailed report available at: {report_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())