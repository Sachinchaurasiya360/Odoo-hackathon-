"""
Test script for OTP-based password reset functionality.

This script demonstrates how to test the password reset flow
programmatically.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.database import db
from config.settings import get_config
from modules.auth.service import AuthService


def test_password_reset_flow():
    """Test the complete password reset flow."""
    
    print("=" * 60)
    print("Testing OTP-Based Password Reset")
    print("=" * 60)
    
    # Initialize services
    config = get_config()
    db.initialize(config.MONGODB_URI, config.MONGODB_DB_NAME)
    auth_service = AuthService()
    
    # Test email (replace with a valid test email)
    test_email = "test@example.com"
    
    print(f"\n1. Testing password reset request for: {test_email}")
    try:
        result = auth_service.request_password_reset(test_email)
        print(f"   ✓ Success: {result['message']}")
        
        if config.DEBUG and result.get('debug_otp'):
            print(f"   📧 OTP (debug mode): {result['debug_otp']}")
            otp = result['debug_otp']
        else:
            print("   📧 Check your email for the OTP")
            otp = input("   Enter OTP from email: ").strip()
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    print(f"\n2. Testing OTP verification")
    try:
        result = auth_service.verify_otp(test_email, otp)
        print(f"   ✓ Success: {result['message']}")
        reset_token = result['reset_token']
        print(f"   🔑 Reset token generated (length: {len(reset_token)})")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    print(f"\n3. Testing password reset")
    new_password = "NewTestPassword123!"
    try:
        result = auth_service.reset_password(reset_token, new_password)
        print(f"   ✓ Success: {result['message']}")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    print("\n" + "=" * 60)
    print("✓ All password reset tests passed!")
    print("=" * 60)
    print("\nYou can now:")
    print("1. Try logging in with the new password")
    print("2. Test the web interface at /auth/forgot-password")
    print("3. Test the API endpoints")


def test_email_configuration():
    """Test email configuration."""
    
    print("=" * 60)
    print("Testing Email Configuration")
    print("=" * 60)
    
    config = get_config()
    
    print(f"\nMail Server: {config.MAIL_SERVER}")
    print(f"Mail Port: {config.MAIL_PORT}")
    print(f"Mail TLS: {config.MAIL_USE_TLS}")
    print(f"Mail Username: {config.MAIL_USERNAME}")
    print(f"Mail Password: {'*' * len(config.MAIL_PASSWORD) if config.MAIL_PASSWORD else 'NOT SET'}")
    print(f"Default Sender: {config.MAIL_DEFAULT_SENDER}")
    print(f"OTP Expiry: {config.OTP_EXPIRY_MINUTES} minutes")
    
    if not config.MAIL_USERNAME or not config.MAIL_PASSWORD:
        print("\n⚠️  Warning: Email credentials not configured!")
        print("   In DEBUG mode, OTP will be returned in API response.")
        print("   For production, configure email settings in .env file.")
    else:
        print("\n✓ Email credentials configured")
    
    print("=" * 60)


def show_api_examples():
    """Show API usage examples."""
    
    print("\n" + "=" * 60)
    print("API Usage Examples")
    print("=" * 60)
    
    print("\n1. Request Password Reset:")
    print("""
    curl -X POST http://localhost:5000/auth/api/forgot-password \\
      -H "Content-Type: application/json" \\
      -d '{"email": "user@example.com"}'
    """)
    
    print("\n2. Verify OTP:")
    print("""
    curl -X POST http://localhost:5000/auth/api/verify-otp \\
      -H "Content-Type: application/json" \\
      -d '{"email": "user@example.com", "otp": "123456"}'
    """)
    
    print("\n3. Reset Password:")
    print("""
    curl -X POST http://localhost:5000/auth/api/reset-password \\
      -H "Content-Type: application/json" \\
      -d '{"reset_token": "your-reset-token", "new_password": "NewPassword123!"}'
    """)
    
    print("=" * 60)


if __name__ == "__main__":
    print("\n🔐 Password Reset Test Suite\n")
    
    # Show menu
    print("Select test option:")
    print("1. Test email configuration")
    print("2. Test password reset flow (requires valid user email)")
    print("3. Show API examples")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        test_email_configuration()
    elif choice == "2":
        test_password_reset_flow()
    elif choice == "3":
        show_api_examples()
    elif choice == "4":
        print("Goodbye!")
    else:
        print("Invalid choice!")
