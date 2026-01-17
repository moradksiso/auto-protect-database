#!/bin/bash
# Update PythonAnywhere Deployment Script
# تشغيل هذا السكريبت لتحديث التطبيق على PythonAnywhere

echo "🚀 Starting PythonAnywhere Update..."
echo "=================================="

# Username - قم بتغييره إلى اسم المستخدم الخاص بك
USERNAME="your_pythonanywhere_username"

echo "📝 Instructions for updating on PythonAnywhere:"
echo ""
echo "1️⃣  Login to PythonAnywhere: https://www.pythonanywhere.com"
echo ""
echo "2️⃣  Go to: Consoles → Start a new Bash console"
echo ""
echo "3️⃣  Run these commands in PythonAnywhere console:"
echo ""
echo "   cd ~/$USERNAME"
echo "   git pull origin main"
echo ""
echo "4️⃣  Reload your web app:"
echo "   - Go to: Web tab"
echo "   - Click: Reload button"
echo ""
echo "✅ Done! Your app will be updated with:"
echo "   - Discount feature for Income"
echo "   - Discount feature for Purchases (if applicable)"
echo "   - Updated database schema"
echo ""
echo "=================================="
echo "📌 GitHub Repository:"
echo "   https://github.com/moradksiso/auto-protect-database"
echo ""
