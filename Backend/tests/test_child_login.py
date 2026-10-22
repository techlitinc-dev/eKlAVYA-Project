#!/usr/bin/env python3
"""
Test Child Login API

This script tests the child login functionality including:
- Child login with username and password
- Child token refresh
- Child logout
- Child profile retrieval

Usage:
    python test_child_login.py

Requirements:
    - pytest (for running tests)
    - requests (for HTTP requests)
    - Environment variables set for JWT_SECRET and FIREBASE credentials

Author: Mentor AI Team
Version: 1.0.0
"""

import os
import json
import requests
import pytest
from typing import Dict, Any

# Configuration
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TEST_CHILD_USERNAME = os.getenv("TEST_CHILD_USERNAME", "teststudent123")
TEST_CHILD_PASSWORD = os.getenv("TEST_CHILD_PASSWORD", "TestPass123")


def test_child_login():
    """Test child login endpoint"""
    print("Testing child login...")
    
    url = f"{BASE_URL}/login/child"
    data = {
        "username": TEST_CHILD_USERNAME,
        "password": TEST_CHILD_PASSWORD
    }
    
    try:
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Child login successful!")
            print(f"   Child ID: {result.get('child_id')}")
            print(f"   Username: {result.get('username')}")
            print(f"   Name: {result.get('name')}")
            print(f"   Is Student: {result.get('is_student')}")
            print(f"   Token expires in: {result.get('expires_in')} seconds")
            return result
        else:
            print(f"❌ Child login failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ Error during child login test: {e}")
        return None


def test_child_token_refresh(refresh_token: str):
    """Test child token refresh endpoint"""
    print("\nTesting child token refresh...")
    
    url = f"{BASE_URL}/token/refresh/child"
    data = {
        "refresh_token": refresh_token
    }
    
    try:
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Child token refresh successful!")
            print(f"   New token received (length: {len(result.get('token', ''))})")
            print(f"   Token expires in: {result.get('expires_in')} seconds")
            return result
        else:
            print(f"❌ Child token refresh failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ Error during child token refresh test: {e}")
        return None


def test_child_profile(access_token: str):
    """Test child profile retrieval endpoint"""
    print("\nTesting child profile retrieval...")
    
    url = f"{BASE_URL}/me/child"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Child profile retrieval successful!")
            print(f"   Child ID: {result.get('child_id')}")
            print(f"   Name: {result.get('name')}")
            print(f"   Username: {result.get('username')}")
            print(f"   Age: {result.get('age')}")
            print(f"   Grade: {result.get('grade')}")
            print(f"   Current Level: {result.get('current_level')}")
            return result
        else:
            print(f"❌ Child profile retrieval failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ Error during child profile test: {e}")
        return None


def test_child_logout(access_token: str):
    """Test child logout endpoint"""
    print("\nTesting child logout...")
    
    url = f"{BASE_URL}/logout/child"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.post(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Child logout successful!")
            print(f"   Message: {result.get('message')}")
            return True
        else:
            print(f"❌ Child logout failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error during child logout test: {e}")
        return False


def test_invalid_credentials():
    """Test child login with invalid credentials"""
    print("\nTesting child login with invalid credentials...")
    
    url = f"{BASE_URL}/login/child"
    data = {
        "username": "invalid_user",
        "password": "wrong_password"
    }
    
    try:
        response = requests.post(url, json=data)
        
        if response.status_code == 401:
            print("✅ Invalid credentials properly rejected!")
            return True
        else:
            print(f"❌ Invalid credentials test failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error during invalid credentials test: {e}")
        return False


def test_invalid_token():
    """Test child profile with invalid token"""
    print("\nTesting child profile with invalid token...")
    
    url = f"{BASE_URL}/me/child"
    headers = {
        "Authorization": "Bearer invalid_token_here"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 401:
            print("✅ Invalid token properly rejected!")
            return True
        else:
            print(f"❌ Invalid token test failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error during invalid token test: {e}")
        return False


def main():
    """Run all child login tests"""
    print("🚀 Starting Child Login API Tests")
    print(f"   Base URL: {BASE_URL}")
    print(f"   Test Username: {TEST_CHILD_USERNAME}")
    print("=" * 50)
    
    # Test 1: Invalid credentials
    test_invalid_credentials()
    
    # Test 2: Valid login
    login_result = test_child_login()
    
    if not login_result:
        print("\n❌ Cannot proceed with further tests due to login failure")
        return
    
    access_token = login_result.get('token')
    refresh_token = login_result.get('refresh_token')
    
    # Test 3: Get child profile
    profile_result = test_child_profile(access_token)
    
    # Test 4: Token refresh
    refresh_result = test_child_token_refresh(refresh_token)
    
    if refresh_result:
        new_access_token = refresh_result.get('token')
        # Test profile with new token
        test_child_profile(new_access_token)
    
    # Test 5: Invalid token
    test_invalid_token()
    
    # Test 6: Logout
    logout_success = test_child_logout(access_token)
    
    # Test 7: Try to use token after logout
    if logout_success:
        print("\nTesting token usage after logout...")
        test_child_profile(access_token)
    
    print("\n" + "=" * 50)
    print("🏁 Child Login API Tests Complete")


if __name__ == "__main__":
    main()