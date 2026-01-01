#!/bin/bash

# 🚀 سكريبت الإعداد الأولي للنشر
# Initial Setup Script for GitHub & PythonAnywhere

echo "🚀 Auto Protect Database - Initial Setup"
echo "========================================="
echo ""

cd "/Users/apple/Desktop/auto protect Data Base" || exit 1

# التحقق من Git
if ! command -v git &> /dev/null; then
    echo "❌ Git غير مثبت. الرجاء تثبيته من: https://git-scm.com/"
    exit 1
fi

echo "✅ Git مثبت"
echo ""

# تهيئة Git إذا لم يكن موجود
if [ ! -d ".git" ]; then
    echo "🔧 تهيئة Git repository..."
    git init
    git branch -M main
    echo "✅ تم تهيئة Git"
else
    echo "✅ Git repository موجود بالفعل"
fi

echo ""
echo "📝 الآن أدخل معلومات GitHub الخاصة بك:"
echo ""

# طلب اسم المستخدم
read -p "📌 اسم المستخدم على GitHub: " github_username

if [ -z "$github_username" ]; then
    echo "❌ اسم المستخدم مطلوب!"
    exit 1
fi

# طلب اسم المشروع
read -p "📌 اسم المشروع (اضغط Enter للافتراضي: auto-protect-database): " repo_name

if [ -z "$repo_name" ]; then
    repo_name="auto-protect-database"
fi

echo ""
echo "🔗 جاري ربط GitHub repository..."

# إزالة remote قديم إن وجد
git remote remove origin 2>/dev/null

# إضافة remote جديد
git remote add origin "https://github.com/$github_username/$repo_name.git"

echo "✅ تم ربط: https://github.com/$github_username/$repo_name.git"
echo ""

# إضافة جميع الملفات
echo "📦 جاري إضافة الملفات..."
git add .

# أول commit
echo "💾 جاري حفظ النسخة الأولى..."
git commit -m "Initial commit - Auto Protect Database v1.0

✨ المميزات:
- نظام إدارة شركة تغليف السيارات
- لوحة تحكم للمشرف والموظفين
- إدارة المهام والمشتريات والمداخيل
- تقارير الأداء
- دعم اللغة العربية والإنجليزية
- تصميم متجاوب لجميع الأجهزة

🔐 الأمان:
- Debug mode معطل
- SECRET_KEY قوي
- Production ready"

echo "✅ تم حفظ النسخة"
echo ""

# رفع على GitHub
echo "🚀 جاري الرفع على GitHub..."
echo ""
echo "⚠️  ستحتاج لإدخال:"
echo "   - Username: $github_username"
echo "   - Password: Personal Access Token (ليس كلمة المرور العادية)"
echo ""
echo "📝 للحصول على Token:"
echo "   1. اذهب إلى: https://github.com/settings/tokens"
echo "   2. Generate new token (classic)"
echo "   3. اختر: repo (full control)"
echo "   4. انسخ الـ token واستخدمه كـ password"
echo ""

if git push -u origin main; then
    echo ""
    echo "✅✅✅ تم الرفع على GitHub بنجاح! ✅✅✅"
    echo ""
    echo "🔗 رابط المشروع: https://github.com/$github_username/$repo_name"
    echo ""
    echo "📋 الخطوات التالية:"
    echo "   1. اذهب إلى: https://github.com/$github_username/$repo_name"
    echo "   2. تأكد من رؤية جميع الملفات"
    echo "   3. اتبع دليل DEPLOY_GUIDE.md للنشر على PythonAnywhere"
    echo ""
    echo "🎉 رائع! المشروع الآن على GitHub"
else
    echo ""
    echo "❌ فشل الرفع. تحقق من:"
    echo "   1. تم إنشاء repository على GitHub باسم: $repo_name"
    echo "   2. استخدمت Personal Access Token وليس كلمة المرور"
    echo "   3. Token له صلاحية repo"
    echo ""
    echo "🔄 للمحاولة مرة أخرى شغل:"
    echo "   git push -u origin main"
fi

echo ""
echo "========================================="
