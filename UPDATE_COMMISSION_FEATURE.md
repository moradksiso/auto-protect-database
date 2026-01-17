# 🔄 تحديث ميزة عمولة الموظف على PythonAnywhere

## ⚠️ المشكلة الحالية:
تم إضافة ميزة عمولة الموظف محلياً، لكن PythonAnywhere لم يتم تحديثه بعد.

---

## ✅ الحل الكامل خطوة بخطوة:

### 1️⃣ تحديث الكود من GitHub:

في PythonAnywhere Bash Console:

```bash
cd ~/auto-protect-db
git pull origin main
```

**ستظهر رسالة مثل:**
```
Updating 58a03c9..5ad89ec
Fast-forward
 app.py                   | 23 +++++++++++++++----
 models.py                |  2 ++
 templates/tasks.html     | 24 +++++++++++++++++++
 templates/edit_task.html | 16 +++++++++++++
 COMMISSION_FEATURE.md    | 182 +++++++++++++++++
 5 files changed, 242 insertions(+), 5 deletions(-)
```

---

### 2️⃣ تحديث قاعدة البيانات:

**الطريقة الأولى (تلقائي):**

```bash
cd ~/auto-protect-db
source venv/bin/activate
python3 << 'EOF'
from app import app
with app.app_context():
    print("Database will be updated automatically on next page load")
EOF
```

**الطريقة الثانية (يدوي - إذا لم تعمل الأولى):**

```bash
cd ~/auto-protect-db
source venv/bin/activate
python3 << 'EOF'
from app import app, db
from sqlalchemy import text

with app.app_context():
    with db.engine.connect() as conn:
        # التحقق من الحقول الموجودة
        result = conn.execute(text("PRAGMA table_info(task)"))
        columns = [row[1] for row in result]
        
        # إضافة حقل agent_commission إذا لم يكن موجود
        if 'agent_commission' not in columns:
            conn.execute(text("ALTER TABLE task ADD COLUMN agent_commission REAL DEFAULT 0.0"))
            conn.commit()
            print("✅ تم إضافة agent_commission")
        else:
            print("✓ agent_commission موجود")
            
        # إضافة حقل show_commission_in_invoice إذا لم يكن موجود
        if 'show_commission_in_invoice' not in columns:
            conn.execute(text("ALTER TABLE task ADD COLUMN show_commission_in_invoice INTEGER DEFAULT 0"))
            conn.commit()
            print("✅ تم إضافة show_commission_in_invoice")
        else:
            print("✓ show_commission_in_invoice موجود")
            
print("✅ قاعدة البيانات محدثة!")
EOF
```

---

### 3️⃣ إعادة تحميل التطبيق:

1. اذهب لتبويب **Web** في PythonAnywhere
2. اضغط الزر الأخضر **Reload** 🟢
3. انتظر "All done!"

---

### 4️⃣ اختبار الميزة:

#### أ) صفحة المهام:
1. افتح: https://autoprotectagadir.pythonanywhere.com/tasks
2. أضف مهمة جديدة مع عمولة
3. تحقق من الخيارات:
   - **عمولة الموظف:** أدخل المبلغ (مثال: 100)
   - **إظهار العمولة في الفاتورة:** ✓ أو ✗

#### ب) تقرير الأداء:
1. افتح: https://autoprotectagadir.pythonanywhere.com/reports/performance
2. يجب أن ترى عمود **"عمولة الموظف (هذا الشهر)"**
3. يجب أن تظهر العمولات المضافة

---

## 📋 التحقق من نجاح التحديث:

### اختبار سريع في PythonAnywhere Console:

```bash
cd ~/auto-protect-db
source venv/bin/activate
python3 << 'EOF'
from app import app, Task
with app.app_context():
    # فحص آخر مهمة
    task = Task.query.order_by(Task.id.desc()).first()
    if task:
        print(f"Task ID: {task.id}")
        print(f"Agent Commission: {task.agent_commission}")
        print(f"Show in Invoice: {task.show_commission_in_invoice}")
    else:
        print("No tasks found")
EOF
```

**النتيجة المتوقعة:**
```
Task ID: 1
Agent Commission: 0.0
Show in Invoice: False
```

---

## 🐛 حل المشاكل:

### المشكلة: الحقول لا تظهر في الواجهة

**الحل:**
1. امسح Cache المتصفح: `Ctrl+Shift+R`
2. تحقق من Error Log في PythonAnywhere

### المشكلة: خطأ عند إضافة مهمة

**الحل:**
```bash
cd ~/auto-protect-db
source venv/bin/activate
python3 -c "from app import app; print('App loads OK')"
```

إذا ظهر خطأ، أرسل لي نص الخطأ

### المشكلة: قاعدة البيانات لم تتحدث

**الحل:**
```bash
cd ~/auto-protect-db
sqlite3 app.db "PRAGMA table_info(task);"
```

يجب أن ترى `agent_commission` و `show_commission_in_invoice` في القائمة

---

## 🎯 الميزات الجديدة بعد التحديث:

### 1. إضافة عمولة في المهام:
- ✅ حقل "عمولة الموظف" في إضافة مهمة جديدة
- ✅ حقل "عمولة الموظف" في إضافة سريعة
- ✅ حقل "عمولة الموظف" في تعديل المهمة

### 2. التحكم في إظهار العمولة:
- ✅ checkbox "إظهار العمولة في الفاتورة"
- ✅ إذا كان مفعّل: تظهر في الفاتورة
- ✅ إذا كان معطّل: لا تظهر (لكن تُحسب في التقارير)

### 3. تقرير الأداء المحدث:
- ✅ عمود "عمولة الموظف (هذا الشهر)"
- ✅ حساب إجمالي العمولات
- ✅ عرض عمولة كل موظف منفصلة

---

## 📝 ملاحظات مهمة:

### 1. المهام القديمة:
- المهام الموجودة ستكون عمولتها = 0
- يمكن تعديلها وإضافة عمولة

### 2. الفواتير:
- العمولة تظهر فقط إذا تم تفعيل الخيار
- لا تؤثر على حسابات الشركة

### 3. التقارير:
- تُحسب العمولات دائماً
- تظهر في تقرير الأداء
- لا تؤثر على صافي الربح

---

## ✨ مثال عملي:

### سيناريو 1: عمولة مع إظهار في الفاتورة
```
عنوان المهمة: تغليف 5 سيارات
عمولة الموظف: 500 درهم
إظهار في الفاتورة: ✓

النتيجة:
- ستظهر في الفاتورة: "عمولة الموظف: 500 درهم"
- تُحسب في تقرير الأداء
```

### سيناريو 2: عمولة بدون إظهار في الفاتورة
```
عنوان المهمة: تغليف 3 سيارات
عمولة الموظف: 300 درهم
إظهار في الفاتورة: ✗

النتيجة:
- لن تظهر في الفاتورة
- تُحسب في تقرير الأداء فقط
```

---

## 🚀 الأوامر الكاملة للنسخ واللصق:

```bash
# 1. التحديث من GitHub
cd ~/auto-protect-db
git pull origin main

# 2. تحديث قاعدة البيانات
source venv/bin/activate
python3 -c "from app import app; print('✅ Ready to reload')"

# 3. ثم اذهب لتبويب Web واضغط Reload
```

---

## ✅ قائمة التحقق النهائية:

- [ ] تحديث الكود: `git pull origin main`
- [ ] تحديث قاعدة البيانات (تلقائي عند أول تشغيل)
- [ ] Reload التطبيق
- [ ] مسح Cache المتصفح
- [ ] اختبار إضافة مهمة بعمولة
- [ ] التحقق من تقرير الأداء
- [ ] اختبار الفاتورة مع/بدون عمولة

---

**بعد هذه الخطوات، ستعمل ميزة العمولة بشكل كامل!** 🎉
