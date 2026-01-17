# 🚀 دليل النشر الأول على PythonAnywhere

## المشكلة
المشروع غير موجود على PythonAnywhere - يجب استنساخه من GitHub أولاً

---

## ✅ الحل: خطوات النشر الكاملة

### الخطوة 1: استنساخ المشروع من GitHub

في PythonAnywhere Bash Console، شغّل:

```bash
cd ~
git clone https://github.com/moradksiso/auto-protect-database.git
cd auto-protect-database
```

---

### الخطوة 2: إنشاء البيئة الافتراضية

```bash
python3.10 -m venv venv
source venv/bin/activate
```

---

### الخطوة 3: تثبيت المكتبات

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### الخطوة 4: إعداد قاعدة البيانات

```bash
python3 -c "from app import db, create_tables; create_tables()"
```

---

### الخطوة 5: إعداد Web App

1. اذهب إلى تبويب **Web**
2. اضغط **Add a new web app**
3. اختر **Manual configuration**
4. اختر **Python 3.10**

---

### الخطوة 6: ضبط إعدادات Web App

في صفحة Web configuration:

#### A. Source code:
```
/home/autoprotectagadir/auto-protect-database
```

#### B. Working directory:
```
/home/autoprotectagadir/auto-protect-database
```

#### C. Virtualenv:
```
/home/autoprotectagadir/auto-protect-database/venv
```

#### D. WSGI configuration file:
اضغط على الرابط الأزرق للملف، واستبدل المحتوى بـ:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/autoprotectagadir/auto-protect-database'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variable
os.environ['FLASK_APP'] = 'app.py'

# Import Flask app
from app import app as application
```

احفظ الملف (Ctrl+S أو زر Save)

---

### الخطوة 7: إعداد Static Files

في نفس صفحة Web configuration، أضف:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/autoprotectagadir/auto-protect-database/static` |

---

### الخطوة 8: Reload التطبيق

اضغط الزر الأخضر الكبير **Reload** في أعلى الصفحة

---

### الخطوة 9: اختبار التطبيق

افتح: `https://autoprotectagadir.pythonanywhere.com`

البيانات الافتراضية:
- Username: `admin`
- Password: `admin123`

---

## 🔄 للتحديثات المستقبلية

بعد النشر الأول، للتحديث فقط:

```bash
cd ~/auto-protect-database
git pull origin main
```

ثم اضغط **Reload** في تبويب Web

---

## 📝 ملاحظات مهمة

### تغيير اسم المستخدم في التعليمات
إذا كان اسم المستخدم مختلف عن `autoprotectagadir`، استبدله في جميع المسارات

### ملفات قاعدة البيانات
- سيتم إنشاء `instance/database.db` تلقائياً
- ستحتوي على حساب admin افتراضي

### السجلات (Logs)
للتحقق من الأخطاء، في تبويب Web:
- اضغط **Error log**
- اضغط **Server log**

---

## 🐛 حل المشاكل الشائعة

### خطأ "No module named 'flask'"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### خطأ "Application is not callable"
تأكد من WSGI file يحتوي على `from app import app as application`

### الصفحة لا تفتح
1. تحقق من Error log
2. تأكد من Reload التطبيق
3. تأكد من جميع المسارات صحيحة

### Static files لا تعمل
تأكد من إضافة `/static/` mapping في Web configuration

---

## ✅ قائمة التحقق النهائية

- [ ] استنساخ المشروع من GitHub
- [ ] إنشاء البيئة الافتراضية
- [ ] تثبيت المكتبات
- [ ] إنشاء قاعدة البيانات
- [ ] إعداد Web App
- [ ] ضبط WSGI file
- [ ] إضافة Static files mapping
- [ ] Reload التطبيق
- [ ] اختبار تسجيل الدخول

---

## 🎉 بعد الانتهاء

التطبيق سيكون متاحاً على:
`https://autoprotectagadir.pythonanywhere.com`

جميع الميزات الجديدة متوفرة:
- ✅ نظام الخصم في المداخيل
- ✅ الفواتير المحدثة
- ✅ التقارير الشاملة
- ✅ لوحات التحكم المحسنة

---

## 🔍 التحقق من نجاح التحديثات

### للتأكد أن التحديثات ظهرت:

1. **افتح صفحة المداخيل:**
   - سجل دخول للتطبيق
   - اذهب إلى "المداخيل"
   - يجب أن ترى حقول جديدة:
     - الثمن الأصلي
     - الخصم
     - الثمن النهائي
     - وصف الخصم

2. **تحقق من الفواتير:**
   - افتح أي فاتورة
   - يجب أن ترى الخصم (إذا كان موجود)
   - يجب أن ترى الثمن النهائي

3. **تحقق من Favicon:**
   - انظر إلى تبويب المتصفح
   - يجب أن ترى أيقونة خضراء مع "AP"

### إذا لم تظهر التحديثات:

1. **أعد تحميل الصفحة بقوة:**
   - Windows/Linux: Ctrl+Shift+R
   - Mac: Cmd+Shift+R

2. **تحقق من Error Log:**
   - Web tab → Error log
   - ابحث عن أخطاء باللون الأحمر

3. **أعد تشغيل قاعدة البيانات:**
   ```bash
   cd ~/auto-protect-database
   source venv/bin/activate
   python3 -c "from app import create_tables; create_tables()"
   ```
   ثم Reload من Web tab

4. **تحقق من تحديث Git:**
   ```bash
   cd ~/auto-protect-database
   git log --oneline -5
   ```
   يجب أن ترى آخر التحديثات
