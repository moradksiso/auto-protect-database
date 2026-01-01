#!/bin/bash

# 🚀 Auto Protect - سكريبت النشر التلقائي
# Auto Deploy Script for GitHub

echo "🚀 Auto Protect Database - Git Deploy Script"
echo "=============================================="
echo ""

# التحقق من وجود Git
if ! command -v git &> /dev/null; then
    echo "❌ Git غير مثبت. الرجاء تثبيته أولاً."
    exit 1
fi

# الانتقال لمجلد المشروع
cd "/Users/apple/Desktop/auto protect Data Base" || exit 1

# التحقق من وجود تعديلات
if git diff-index --quiet HEAD --; then
    echo "✅ لا توجد تعديلات للرفع"
    exit 0
fi

# عرض الملفات المعدلة
echo "📝 الملفات المعدلة:"
git status --short
echo ""

# طلب رسالة الـ commit
echo "💬 أدخل وصف التحديث (اضغط Enter للوصف الافتراضي):"
read -r commit_message

if [ -z "$commit_message" ]; then
    commit_message="Update $(date '+%Y-%m-%d %H:%M:%S')"
fi

echo ""
echo "🔄 جاري رفع التحديثات..."
echo ""

# إضافة جميع الملفات
git add .

# Commit
git commit -m "$commit_message"

# Push
if git push; then
    echo ""
    echo "✅ تم رفع التحديثات بنجاح!"
    echo ""
    echo "📍 للتحديث على PythonAnywhere:"
    echo "   1. افتح Bash Console"
    echo "   2. شغل: cd ~/auto-protect-db && git pull"
    echo "   3. اضغط Reload في Web tab"
else
    echo ""
    echo "❌ فشل رفع التحديثات. تحقق من:"
    echo "   - اتصال الإنترنت"
    echo "   - صلاحيات GitHub"
    echo "   - تم ربط Remote repository"
fi

echo ""
echo "=============================================="
