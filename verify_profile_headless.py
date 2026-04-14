
import requests
import sys

BASE_URL = "http://127.0.0.1:5000"
SESSION = requests.Session()

def register_and_login():
    # 1. Register
    print("1. Registering new user...")
    reg_data = {
        "name": "Headless Test",
        "email": "headless@example.com",
        "password": "password"
    }
    try:
        r = SESSION.post(f"{BASE_URL}/auth/register", data=reg_data)
    except Exception as e:
        print(f"Registration request failed: {e}")
        return

    # 2. Login
    print("2. Logging in...")
    login_data = {
        "email": "headless@example.com",
        "password": "password"
    }
    r = SESSION.post(f"{BASE_URL}/auth/login", data=login_data)
    
    if "dashboard" in r.url or r.status_code == 200:
        print("   Login successful.")
    else:
        print(f"   Login failed. URL: {r.url}, Status: {r.status_code}")
        # We might continue if already logged in or registered
        
def verify_initial_profile():
    print("3. Checking initial profile...")
    r = SESSION.get(f"{BASE_URL}/user/profile")
    text = r.text
    
    # Check for Name and Address
    if "Headless Test" in text:
        print("   Name found.")
    else:
        print("   Name NOT found.")
        
    if "Address" in text:
        print("   Address label found.")
    else:
        print("   Address label NOT found (Code update might be missing).")

def update_profile():
    print("4. Updating profile...")
    new_data = {
        "name": "Headless Updated",
        "email": "headless@example.com",
        "address": "999 Digital Avenue"
    }
    r = SESSION.post(f"{BASE_URL}/user/edit_profile", data=new_data)
    
    # Check if redirected to profile
    if "profile" in r.url:
        print("   Update posted, redirected to profile.")
    else:
        print(f"   Update failed? URL: {r.url}")

def verify_updated_profile():
    print("5. Verifying updates...")
    r = SESSION.get(f"{BASE_URL}/user/profile")
    text = r.text
    
    success = True
    if "Headless Updated" in text:
        print("   ✅ Name updated correctly.")
    else:
        print("   ❌ Name update failed.")
        success = False
        
    if "999 Digital Avenue" in text:
        print("   ✅ Address updated correctly.")
    else:
        print("   ❌ Address update failed.")
        success = False
        
    if success:
        print("\nSUCCESS: Profile update logic verified!")
    else:
        print("\nFAILURE: Verification failed.")
        print("Response text dump:")
        # Print first 2000 chars to avoid overwhelming output but capture traceback
        print(text[:2000])

if __name__ == "__main__":
    try:
        register_and_login()
        verify_initial_profile()
        update_profile()
        verify_updated_profile()
    except Exception as e:
        print(f"An error occurred: {e}")
