# 🚀 دليل النشر على PythonAnywhere و GitHub

## 📋 المتطلبات
- حساب GitHub (مجاني)
- حساب PythonAnywhere (مجاني)
- Git مثبت على جهازك

---

## 🔧 الجزء 1: الرفع على GitHub

### الخطوة 1: إنشاء Repository على GitHub
1. اذهب إلى: https://github.com/new
2. اسم المشروع: `auto-protect-database`
3. الوصف: `Car Wrapping Business Management System`
4. اختر: **Private** (للحماية)
5. لا تضف README (موجود بالفعل)
6. اضغط **Create repository**

### الخطوة 2: رفع المشروع
افتح Terminal وشغل:

```bash
cd "/Users/apple/Desktop/auto protect Data Base"

# تهيئة Git
git init

# إضافة جميع الملفات
git add .

# أول Commit
git commit -m "Initial commit - Auto Protect Database v1.0"

# ربط GitHub (استبدل USERNAME باسم المستخدم)
git remote add origin https://github.com/<USERNAME>/auto-protect-database.git

# رفع الملفات
git branch -M main
git push -u origin main
```

### الخطوة 3: رفع التحديثات مستقبلاً
```bash
cd "/Users/apple/Desktop/auto protect Data Base"
git add .
git commit -m "وصف التحديث"
git push
```

---

## 🌐 الجزء 2: النشر على PythonAnywhere

### الخطوة 1: إنشاء حساب
1. اذهب إلى: https://www.pythonanywhere.com/registration/register/beginner/
2. سجل حساب مجاني
3. تأكيد البريد الإلكتروني

### الخطوة 2: إنشاء Web App
1. Dashboard → **Web**
2. **Add a new web app**
3. اختر: **Manual configuration**
4. اختر: **Python 3.10**
5. اضغط **Next**

### الخطوة 3: رفع المشروع

#### طريقة 1: من GitHub (موصى بها)
افتح **Bash Console** في PythonAnywhere:

```bash
# استنساخ المشروع
cd ~
git clone https://github.com/YOUR_GITHUB_USERNAME/auto-protect-database.git auto-protect-db
cd auto-protect-db

# إنشاء Virtual Environment
python3.10 -m venv venv
source venv/bin/activate

# تثبيت المتطلبات
pip install -r requirements.txt

# إنشاء قاعدة البيانات
python3 app.py
# اضغط Ctrl+C بعد ثواني
```

#### طريقة 2: رفع مباشر
1. اذهب إلى **Files** في Dashboard
2. اضغط **Upload a file**
3. ارفع ملف ZIP للمشروع
4. Extract الملفات

### الخطوة 4: تكوين WSGI

1. اذهب إلى **Web** tab
2. في قسم **Code**:
   - **Source code:** `/home/autoprotectagadir/auto-protect-db`
   - **Working directory:** `/home/autoprotectagadir/auto-protect-db`
3. اضغط على **WSGI configuration file** link
4. **احذف** المحتوى القديم
5. **الصق** محتوى ملف `pythonanywhere_wsgi.py`
6. **Save** (اسم المستخدم محدث بالفعل في الملف)

### الخطوة 5: تكوين Virtual Environment
1. في **Web** tab
2. قسم **Virtualenv**:
3. أدخل: `/home/autoprotectagadir/auto-protect-db/venv`
4. اضغط ✓

### الخطوة 6: Static Files
في قسم **Static files**:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/autoprotectagadir/auto-protect-db/static` |

### الخطوة 7: تفعيل الموقع
1. اضغط على **Reload** (زر أخضر كبير)
2. افتح رابط الموقع: `https://autoprotectagadir.pythonanywhere.com`

---

## 🔐 الخطوة 8: إعدادات الأمان

### تغيير كلمة مرور Admin
1. اذهب إلى: `https://autoprotectagadir.pythonanywhere.com/login`
2. Username: `admin`
3. Password: `admin123`
4. Settings → Change Password
5. أدخل كلمة مرور قوية

### تحديث SECRET_KEY
1. افتح **Bash Console**
2. شغل: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
3. انسخ المفتاح الجديد
4. حدّث WSGI file بالمفتاح الجديد
5. **Reload** التطبيق

---

## 🔄 تحديث التطبيق مستقبلاً

### على GitHub:
```bash
cd "/Users/apple/Desktop/auto protect Data Base"
git add .
git commit -m "تحديث: وصف التحديث"
git push
```

### على PythonAnywhere:
```bash
# في Bash Console
cd ~/auto-protect-db
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
# ثم Reload من Web tab
```

---

## 📊 مراقبة الأخطاء

### عرض Logs
1. **Web** tab
2. **Log files** section:
   - **Error log** - أخطاء التطبيق
   - **Server log** - سجل الطلبات
   - **Access log** - الزيارات

### إعادة تشغيل التطبيق
اضغط زر **Reload** الأخضر في Web tab

---

## 🎯 نصائح مهمة

### للحساب المجاني:
- ✅ مساحة: 512 MB
- ✅ مدة تشغيل: 100 seconds/day
- ✅ قاعدة بيانات: SQLite
- ⚠️ ينام بعد 3 شهور من عدم النشاط
- ⚠️ يحتاج Reload كل يوم

### للترقية (Paid):
- 💰 $5/شهر
- ✅ Unlimited CPU time
- ✅ Always-on tasks
- ✅ MySQL/PostgreSQL databases
- ✅ Custom domain
- ✅ HTTPS included

---

## ❓ حل المشاكل الشائعة

### المشكلة: "Import Error"
**الحل:**
```bash
cd ~/auto-protect-db
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### المشكلة: "Database is locked"
**الحل:**
```bash
cd ~/auto-protect-db
rm app.db
python3 app.py  # سينشئ قاعدة جديدة
```

### المشكلة: "Static files not loading"
**الحل:**
1. تحقق من Static files mapping في Web tab
2. تأكد من المسار الصحيح
3. Reload التطبيق

### المشكلة: "500 Internal Server Error"
**الحل:**
1. افتح Error log
2. ابحث عن آخر خطأ
3. صححه في الكود
4. `git pull` على PythonAnywhere
5. Reload

---

## 📞 روابط مفيدة

- **PythonAnywhere Help:** https://help.pythonanywhere.com/
- **GitHub Docs:** https://docs.github.com/
- **Flask on PythonAnywhere:** https://help.pythonanywhere.com/pages/Flask/

---

## ✅ Checklist النشر

- [ ] تم رفع المشروع على GitHub
- [ ] تم إنشاء حساب PythonAnywhere
- [ ] تم رفع المشروع على PythonAnywhere
- [ ] تم تكوين WSGI
- [ ] تم تكوين Virtual Environment
- [ ] تم تكوين Static Files
- [ ] التطبيق يعمل بنجاح
- [ ] تم تغيير كلمة مرور Admin
- [ ] تم تحديث SECRET_KEY
- [ ] تم اختبار جميع الصفحات
- [ ] تم اختبار تسجيل الدخول
- [ ] تم اختبار إضافة/تعديل/حذف البيانات

---

## 🎉 تهانينا!

تطبيقك الآن **على الإنترنت** ويمكن الوصول إليه من أي مكان! 🌍
