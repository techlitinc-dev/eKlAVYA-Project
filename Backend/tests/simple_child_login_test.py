#!/usr/bin/env python3
"""
Simple Child Login Test

This script performs basic testing of child login functionality
without complex validation framework.

Usage:
    python3 simple_child_login_test.py
"""

import sys
import os

def test_imports():
    """Test basic imports"""
    print("🔍 Testing imports...")
    
    try:
        from models.login_models import ChildLoginRequest, LoginResponse
        print("✅ ChildLoginRequest and LoginResponse imported successfully")
        
        from services.login_service import login_child, refresh_child_access_token, logout_child
        print("✅ Child login services imported successfully")
        
        from services.token_service import generate_student_access_token, generate_student_refresh_token
        print("✅ Student token services imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_model_creation():
    """Test model creation and validation"""
    print("\n🔍 Testing model creation...")
    
    try:
        from models.login_models import ChildLoginRequest
        
        # Test valid data
        valid_data = {
            "username": "teststudent123",
            "password": "TestPass123"
        }
        request = ChildLoginRequest(**valid_data)
        print(f"✅ Valid ChildLoginRequest created: username={request.username}")
        
        # Test invalid username
        try:
            invalid_data = {
                "username": "ab",  # Too short
                "password": "TestPass123"
            }
            ChildLoginRequest(**invalid_data)
            print("❌ Invalid username should have failed")
            return False
        except Exception:
            print("✅ Invalid username properly rejected")
        
        # Test invalid password
        try:
            invalid_data = {
                "username": "teststudent123",
                "password": "123"  # Too short
            }
            ChildLoginRequest(**invalid_data)
            print("❌ Invalid password should have failed")
            return False
        except Exception:
            print("✅ Invalid password properly rejected")
        
        return True
        
    except Exception as e:
        print(f"❌ Model creation error: {e}")
        return False

def test_token_generation():
    """Test token generation"""
    print("\n🔍 Testing token generation...")
    
    try:
        from services.token_service import generate_student_access_token, generate_student_refresh_token
        
        # Test access token generation
        access_token = generate_student_access_token(
            child_id="test_child_123",
            username="teststudent",
            name="Test Student"
        )
        print(f"✅ Access token generated (length: {len(access_token)})")
        
        # Test refresh token generation
        refresh_token = generate_student_refresh_token(
            child_id="test_child_123",
            username="teststudent"
        )
        print(f"✅ Refresh token generated (length: {len(refresh_token)})")
        
        return True
        
    except Exception as e:
        print(f"❌ Token generation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Simple Child Login Implementation Test")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Model Creation Test", test_model_creation),
        ("Token Generation Test", test_token_generation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Child login implementation is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())