#!/usr/bin/env python3
"""
Script to create a test parent and student account for testing
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

def create_test_accounts():
    """Create test parent and student accounts"""
    
    print("\n" + "="*70)
    print("CREATE TEST ACCOUNTS FOR STUDENT LOGIN")
    print("="*70)
    
    # Test data
    parent_data = {
        "name": "Test Parent",
        "mobile_number": "9876543210",
        "email_address": "testparent@example.com",
        "password": "TestParent123!",
        "repeat_password": "TestParent123!"
    }
    
    student_data = {
        "name": "Test Student",
        "age": 17,
        "grade": 12,
        "current_level": "intermediate",
        "username": "test_student",
        "password": "TestStudent123!"
    }
    
    print("\n📝 Test Account Details:")
    print("-" * 70)
    print(f"Parent Email: {parent_data['email_address']}")
    print(f"Parent Password: {parent_data['password']}")
    print(f"Student Username: {student_data['username']}")
    print(f"Student Password: {student_data['password']}")
    print("-" * 70)
    
    # Step 1: Register Parent
    print("\n\n🔹 Step 1: Registering Parent...")
    print("-" * 70)
    
    register_url = f"{BASE_URL}/auth/register/simple"
    try:
        response = requests.post(register_url, params=parent_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("✅ Parent registered successfully!")
            parent_response = response.json()
            parent_id = parent_response.get('parent_id')
            print(f"Parent ID: {parent_id}")
        else:
            print(f"❌ Registration failed: {response.json()}")
            if "already exists" in str(response.json()):
                print("\n💡 Parent already exists. Trying to login...")
                # Try to login instead
                login_response = requests.post(
                    f"{BASE_URL}/auth/login/email",
                    json={
                        "email": parent_data['email_address'],
                        "password": parent_data['password']
                    }
                )
                if login_response.status_code == 200:
                    parent_response = login_response.json()
                    parent_id = parent_response.get('parent_id')
                    print(f"✅ Logged in successfully! Parent ID: {parent_id}")
                else:
                    print("❌ Login also failed. Please check credentials.")
                    return
            else:
                return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Step 2: Login to get token
    print("\n\n🔹 Step 2: Logging in as Parent...")
    print("-" * 70)
    
    login_url = f"{BASE_URL}/auth/login/email"
    try:
        response = requests.post(
            login_url,
            json={
                "email": parent_data['email_address'],
                "password": parent_data['password']
            }
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            login_response = response.json()
            token = login_response.get('token')
            parent_id = login_response.get('parent_id')
            print(f"Token received: {token[:20]}...")
        else:
            print(f"❌ Login failed: {response.json()}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Step 3: Create Child Profile
    print("\n\n🔹 Step 3: Creating Child Profile...")
    print("-" * 70)
    
    child_url = f"{BASE_URL}/onboarding/child"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"parent_id": parent_id}
    
    try:
        response = requests.post(
            child_url,
            json=student_data,
            headers=headers,
            params=params
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("✅ Child profile created successfully!")
            child_response = response.json()
            child_id = child_response.get('child_id')
            print(f"Child ID: {child_id}")
            print(f"Username: {child_response.get('username')}")
        else:
            print(f"❌ Child profile creation failed: {response.json()}")
            if "already has a child" in str(response.json()):
                print("\n💡 Child profile already exists. That's okay!")
            else:
                return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Step 4: Test Student Login
    print("\n\n🔹 Step 4: Testing Student Login...")
    print("-" * 70)
    
    student_login_url = f"{BASE_URL}/auth/login/student"
    try:
        response = requests.post(
            student_login_url,
            json={
                "username": student_data['username'],
                "password": student_data['password']
            }
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Student login successful!")
            student_response = response.json()
            print(f"Student ID: {student_response.get('student_id')}")
            print(f"Username: {student_response.get('username')}")
            print(f"Name: {student_response.get('name')}")
            print(f"Is Student: {student_response.get('is_student')}")
        else:
            print(f"❌ Student login failed: {response.json()}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Success!
    print("\n\n" + "="*70)
    print("✅ SUCCESS! Test accounts created and verified!")
    print("="*70)
    print("\n📋 Use these credentials to login:")
    print("-" * 70)
    print("\n🔹 Parent Login (http://localhost:3000/auth):")
    print(f"   Email: {parent_data['email_address']}")
    print(f"   Password: {parent_data['password']}")
    print("\n🔹 Student Login (http://localhost:3000/auth):")
    print(f"   Username: {student_data['username']}")
    print(f"   Password: {student_data['password']}")
    print("\n💡 Remember: Parents use EMAIL, Students use USERNAME")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        create_test_accounts()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
