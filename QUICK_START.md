# Quick Start: Password Reset Feature

## 🚀 Get Started in 5 Minutes

### Step 1: Configure Email (Choose One Option)

#### Option A: Gmail (Easiest)

1. Go to your Google Account: https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Generate App Password: https://myaccount.google.com/apppasswords
4. Copy the 16-character password

#### Option B: Skip Email (Development Only)

- Leave email settings empty
- OTP will be returned in API responses when `DEBUG=True`

### Step 2: Update Environment Variables

Create or update your `.env` file:

```env
# For Gmail
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password

# Optional: Leave empty for development
# MAIL_USERNAME=
# MAIL_PASSWORD=
```

### Step 3: Test the Feature

#### Web Interface

1. Start your Flask app:

   ```bash
   cd src
   python app.py
   ```

2. Open browser: http://localhost:5000/auth/login

3. Click "Forgot Password?"

4. Follow the steps:
   - Enter your email
   - Check email for OTP (or see console in debug mode)
   - Enter OTP
   - Set new password

#### API Testing

```bash
# 1. Request OTP
curl -X POST http://localhost:5000/auth/api/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Response includes OTP in debug mode:
# {"success": true, "data": {"debug_otp": "123456"}}

# 2. Verify OTP
curl -X POST http://localhost:5000/auth/api/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "otp": "123456"}'

# Response: {"success": true, "data": {"reset_token": "eyJ..."}}

# 3. Reset Password
curl -X POST http://localhost:5000/auth/api/reset-password \
  -H "Content-Type: application/json" \
  -d '{"reset_token": "YOUR_TOKEN", "new_password": "NewPass123!"}'
```

### Step 4: Run Test Script (Optional)

```bash
python test_password_reset.py
```

Choose option 1 to check email configuration, or option 2 to test the full flow.

## 📧 Email Providers

### Gmail

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Outlook

```env
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@outlook.com
MAIL_PASSWORD=your-password
```

### Custom SMTP

```env
MAIL_SERVER=your-smtp-server.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-username
MAIL_PASSWORD=your-password
```

## 🎯 Key Features

- ✅ 6-digit OTP sent via email
- ✅ 10-minute expiration
- ✅ 5 attempt limit
- ✅ Beautiful UI with password strength indicator
- ✅ Full API support
- ✅ Works without email in debug mode

## 🔧 Troubleshooting

### Email Not Sending?

1. Check if `MAIL_USERNAME` and `MAIL_PASSWORD` are set
2. For Gmail, use App Password, not regular password
3. Check spam folder
4. In debug mode, OTP is in console/API response

### OTP Not Working?

1. Make sure you copied all 6 digits
2. Check if it expired (10 minutes)
3. Check attempt count (max 5)
4. Request a new OTP

### Can't Access Routes?

1. Make sure Flask app is running
2. Check URL: http://localhost:5000/auth/forgot-password
3. Clear browser cache/cookies

## 📚 Documentation

- **Full Setup Guide**: `PASSWORD_RESET_SETUP.md`
- **Implementation Details**: `IMPLEMENTATION_SUMMARY.md`
- **Main README**: `README.md`

## 🎉 That's It!

You're ready to use the password reset feature. For more details, check the full documentation files.
