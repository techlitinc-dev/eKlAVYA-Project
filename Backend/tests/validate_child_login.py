#!/usr/bin/env python3
"""
Validate Child Login Implementation

This script validates the child login implementation by checking:
- Import errors in models and services
- Syntax validation
- Basic functionality testing

Usage:
    python3 validate_child_login.py

Author: Mentor AI Team
Version: 1.0.0
"""

import sys
import traceback
from typing import Dict, Any

def validate_imports():
    """Test that all imports work correctly"""
    print("🔍 Testing imports...")
    
    try:
        # Test model imports
        from models.login_models import ChildLoginRequest, LoginResponse, TokenResponse, LogoutResponse
        print("✅ Login models imported successfully")
        
        # Test service imports
        from services.login_service import login_child, refresh_child_access_token, logout_child
        print("✅ Login services imported successfully")
        
        # Test token service imports
        from services.token_service import generate_student_access_token, generate_student_refresh_token, verify_student_refresh_token
        print("✅ Token services imported successfully")
        
        # Test router imports
        from routers.login_router import router
        print("✅ Login router imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        traceback.print_exc()
        return False


def validate_model_validation():
    """Test that model validation works correctly"""
    print("\n🔍 Testing model validation...")
    
    try:
        from models.login_models import ChildLoginRequest
        
        # Test valid data
        valid_data = {
            "username": "teststudent123",
            "password": "TestPass123"
        }
        request = ChildLoginRequest(**valid_data)
        print("✅ Valid child login request created successfully")
        
        # Test invalid data
        invalid_data = {
            "username": "a",  # Too short
            "password": "123"  # Too short
        }
        try:
            ChildLoginRequest(**invalid_data)
            print("❌ Invalid data should have failed validation")
            return False
        except Exception:
            print("✅ Invalid data properly rejected by validation")
        
        return True
        
    except Exception as e:
        print(f"❌ Model validation error: {e}")
        traceback.print_exc()
        return False


def validate_token_generation():
    """Test that token generation works correctly"""
    print("\n🔍 Testing token generation...")
    
    try:
        from services.token_service import generate_student_access_token, generate_student_refresh_token
        
        # Test access token generation
        access_token = generate_student_access_token(
            child_id="test_child_123",
            username="teststudent",
            name="Test Student"
        )
        print("✅ Student access token generated successfully")
        print(f"   Token length: {len(access_token)}")
        
        # Test refresh token generation
        refresh_token = generate_student_refresh_token(
            child_id="test_child_123",
            username="teststudent"
        )
        print("✅ Student refresh token generated successfully")
        print(f"   Refresh token length: {len(refresh_token)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Token generation error: {e}")
        traceback.print_exc()
        return False


def validate_service_functions():
    """Test that service functions are callable"""
    print("\n🔍 Testing service functions...")
    
    try:
        from services.login_service import login_child, refresh_child_access_token, logout_child
        
        # Check that functions exist and are callable
        assert callable(login_child), "login_child is not callable"
        assert callable(refresh_child_access_token), "refresh_child_access_token is not callable"
        assert callable(logout_child), "logout_child is not callable"
        
        print("✅ All service functions are callable")
        return True
        
    except Exception as e:
        print(f"❌ Service function validation error: {e}")
        traceback.print_exc()
        return False


def validate_router_endpoints():
    """Test that router endpoints are defined"""
    print("\n🔍 Testing router endpoints...")
    
    try:
        from routers.login_router import router
        
        # Check that router has expected routes
        routes = [route for route in router.routes if hasattr(route, 'path')]
        route_paths = [route.path for route in routes]
        
        expected_routes = [
            "/login/child",
            "/token/refresh/child", 
            "/logout/child",
            "/me/child"
        ]
        
        for expected_route in expected_routes:
            if expected_route in route_paths:
                print(f"✅ Route {expected_route} found")
            else:
                print(f"❌ Route {expected_route} not found")
                return False
        
        print(f"✅ Total routes found: {len(routes)}")
        return True
        
    except Exception as e:
        print(f"❌ Router validation error: {e}")
        traceback.print_exc()
        return False


def main():
    """Run all validation tests"""
    print("🚀 Starting Child Login Implementation Validation")
    print("=" * 60)
    
    tests = [
        ("Import Validation", validate_imports),
        ("Model Validation", validate_model_validation),
        ("Token Generation", validate_token_generation),
        ("Service Functions", validate_service_functions),
        ("Router Endpoints", validate_router_endpoints)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validations passed! Child login implementation is ready.")
        return 0
    else:
        print("⚠️  Some validations failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())