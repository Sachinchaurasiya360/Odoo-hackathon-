# Quick MongoDB Setup for Windows

## Problem
Your Flask app cannot connect to MongoDB because it's not installed or running.

## ✅ RECOMMENDED SOLUTION: MongoDB Atlas (Free Cloud Database)

This is the **fastest and easiest** option - no installation needed!

### Steps:

1. **Create Free Account**
   - Go to: https://www.mongodb.com/cloud/atlas/register
   - Sign up with email or Google

2. **Create Free Cluster**
   - Choose "Free" tier (M0)
   - Select a region close to you
   - Click "Create Cluster" (takes 3-5 minutes)

3. **Create Database User**
   - Go to "Database Access" in left menu
   - Click "Add New Database User"
   - Username: `admin`
   - Password: `admin123` (or your choice)
   - Click "Add User"

4. **Allow Network Access**
   - Go to "Network Access" in left menu
   - Click "Add IP Address"
   - Click "Allow Access from Anywhere" (for development)
   - Click "Confirm"

5. **Get Connection String**
   - Go to "Database" in left menu
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string (looks like):
     ```
     mongodb+srv://admin:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
     ```

6. **Update Your .env File**
   - Open `f:\Odoo-hackathon-\.env`
   - Replace the MongoDB URI:
     ```env
     MONGODB_URI=mongodb+srv://admin:admin123@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
     ```
   - Replace `<password>` with your actual password
   - Replace `cluster0.xxxxx` with your actual cluster address

7. **Run Your App**
   ```bash
   cd f:\Odoo-hackathon-\src
   python app.py
   ```

**Done!** Your app will now connect to MongoDB Atlas.

---

## Alternative: Install MongoDB Locally

If you prefer local installation:

### Option 1: MongoDB Community Server

1. **Download**
   - Visit: https://www.mongodb.com/try/download/community
   - Select: Windows, Latest Version
   - Download MSI installer

2. **Install**
   - Run the installer
   - Choose "Complete" installation
   - Install as a Windows Service (recommended)
   - Install MongoDB Compass (optional GUI)

3. **Verify Installation**
   ```powershell
   mongod --version
   ```

4. **Start MongoDB Service**
   ```powershell
   net start MongoDB
   ```

5. **Run Your App**
   ```bash
   cd f:\Odoo-hackathon-\src
   python app.py
   ```

### Option 2: MongoDB with Chocolatey

If you have Chocolatey package manager:

```powershell
# Install Chocolatey first if needed
# Then install MongoDB
choco install mongodb

# Start MongoDB
net start MongoDB
```

### Option 3: Docker (If you install Docker)

1. **Install Docker Desktop**
   - Download from: https://www.docker.com/products/docker-desktop

2. **Run MongoDB Container**
   ```powershell
   docker run -d -p 27017:27017 --name mongodb mongo:latest
   ```

3. **Verify**
   ```powershell
   docker ps
   ```

---

## ⚡ QUICK START (Recommended)

**Use MongoDB Atlas** - it's free, fast, and requires no installation!

1. Create account at https://www.mongodb.com/cloud/atlas/register
2. Create free cluster
3. Get connection string
4. Update `.env` file
5. Run app

**Total time: 5-10 minutes**

---

## Troubleshooting

### Error: "Connection refused"
- MongoDB is not running
- Start MongoDB service: `net start MongoDB`

### Error: "Authentication failed"
- Check username/password in connection string
- Ensure user has proper permissions

### Error: "Network timeout"
- Check firewall settings
- For Atlas: Ensure IP is whitelisted

---

## Next Steps After Setup

Once MongoDB is connected:

1. **Run the app**:
   ```bash
   cd f:\Odoo-hackathon-\src
   python app.py
   ```

2. **Access the application**:
   - Open browser: http://localhost:5000
   - Register a new user
   - Start using the inventory system!

3. **Create sample data** (optional):
   - Create warehouses
   - Add products
   - Create receipts
   - Test workflows

---

## Need Help?

If you're still having issues:

1. Check the error message carefully
2. Verify MongoDB is running: `mongosh` (should connect without errors)
3. Check your `.env` file has correct connection string
4. Ensure no firewall is blocking port 27017

**Recommended**: Use MongoDB Atlas for the easiest setup experience!
