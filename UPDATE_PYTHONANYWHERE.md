# 🔄 دليل التحديث على PythonAnywhere

## ✅ تم رفع الكود إلى GitHub بنجاح!
**Repository:** https://github.com/moradksiso/auto-protect-database

---

## 📋 خطوات التحديث على PythonAnywhere

### الطريقة الأولى: عبر PythonAnywhere Console

1. **تسجيل الدخول إلى PythonAnywhere**
   - اذهب إلى: https://www.pythonanywhere.com
   - سجل دخولك

2. **افتح Bash Console**
   - اذهب إلى تبويب **Consoles**
   - اضغط **Bash** لفتح terminal جديد

3. **حدّث الكود من GitHub**
   ```bash
   cd ~/auto-protect-database
   git pull origin main
   ```

4. **⚠️ مهم جداً: أعد تحميل التطبيق**
   - اذهب إلى تبويب **Web**
   - ابحث عن التطبيق الخاص بك
   - اضغط زر **Reload** الأخضر الكبير في أعلى الصفحة
   - انتظر حتى تظهر رسالة "All done!"

5. **امسح Cache المتصفح**
   - Windows/Linux: اضغط **Ctrl+Shift+R**
   - Mac: اضغط **Cmd+Shift+R**

6. **✅ تم!** زر موقعك للتأكد من التحديثات

---

### الطريقة الثانية: عبر واجهة PythonAnywhere

1. اذهب إلى **Files** tab
2. افتح مجلد `auto-protect-database`
3. اضغط **Open Bash console here**
4. شغل: `git pull origin main`
5. ارجع لتبويب **Web** واضغط **Reload**

---

## 🆕 التحديثات الجديدة المضافة

### ميزة الخصم في المداخيل
- ✅ حقل الخصم (Discount)
- ✅ وصف الخصم (Discount Description)
- ✅ حساب تلقائي للمبلغ النهائي
- ✅ عرض الخصم في الفواتير
- ✅ تحديث لوحات التحكم لاستخدام المبلغ النهائي
- ✅ تصدير Excel مع تفاصيل الخصم

### قاعدة البيانات
- ✅ تم إضافة حقول جديدة للجدول Income:
  - `discount` (REAL)
  - `discount_description` (TEXT)
- ✅ Migration تلقائي عند التشغيل

---

## 🔍 التحقق من التحديث

بعد Reload، تحقق من:
1. صفحة المداخيل `/income` - يجب أن ترى حقول الخصم
2. إضافة مدخول جديد - اختبر حقل الخصم
3. الفواتير - تحقق من ظهور الخصم
4. لوحة التحكم - تأكد من الحسابات الصحيحة

---

## ⚠️ ملاحظات مهمة

1. **قاعدة البيانات**: Migration سيتم تلقائياً عند أول تشغيل
2. **الملفات المرفوعة**: لن تتأثر بالتحديث
3. **النسخ الاحتياطي**: يُنصح بعمل backup قبل التحديث

---

## 🐛 حل المشاكل

### ⛔ التحديثات لم تظهر بعد git pull؟

**السبب:** لم يتم إعادة تشغيل التطبيق

**الحل (الأهم):**
1. اذهب إلى تبويب **Web** في PythonAnywhere
2. اضغط زر **Reload** الأخضر الكبير في أعلى الصفحة
3. انتظر حتى تظهر رسالة "All done!" أو "Reloaded successfully"
4. في المتصفح، أعد تحميل الصفحة بـ **Ctrl+Shift+R** (لمسح الكاش)

### إذا واجهت خطأ عند git pull:
```bash
git stash
git pull origin main
git stash pop
```

### إذا ظهر خطأ في قاعدة البيانات (no such column):
```bash
cd ~/auto-protect-database
source venv/bin/activate
python3 -c "from app import create_tables; create_tables()"
```
ثم اذهب لتبويب Web واضغط Reload

### إذا لم تظهر التحديثات بعد كل ذلك:
1. تحقق من **Error log** في تبويب Web
2. تحقق من **Server log** في تبويب Web
3. ابحث عن أخطاء باللون الأحمر
4. تأكد أن git pull أظهر تحديثات جديدة

---

## 📞 الدعم

- **GitHub Issues**: https://github.com/moradksiso/auto-protect-database/issues
- **PythonAnywhere Help**: https://help.pythonanywhere.com

---

## 🎉 تم بنجاح!

التطبيق الآن يحتوي على:
- ✅ ميزة الخصم الكاملة
- ✅ حسابات محدثة
- ✅ فواتير محسّنة
- ✅ تقارير شاملة

**رابط التطبيق:** https://your-username.pythonanywhere.com
