# 📚 Auto Protect API Documentation v1.75

## 🔐 Authentication

جميع طلبات API تتطلب Token للمصادقة:

```bash
Authorization: Bearer YOUR_TOKEN_HERE
```

### إنشاء Token جديد

1. افتح: https://autoprotectagadir.pythonanywhere.com/api_tokens
2. أدخل اسم Token
3. انسخ Token (يظهر مرة واحدة فقط)
4. استخدمه في جميع الطلبات

---

## 📊 Endpoints الأساسية

### 1. معلومات التطبيق

**GET** `/api/info`

احصل على معلومات التطبيق والإحصائيات العامة

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://autoprotectagadir.pythonanywhere.com/api/info
```

**Response:**
```json
{
  "app_name": "Auto Protect Database",
  "version": "1.75",
  "database": {
    "agents": 10,
    "tasks": 45,
    "purchases": 30,
    "income": 50,
    "files": 12
  },
  "timestamp": "2026-01-17T14:30:00"
}
```

---

### 2. إحصائيات شاملة

**GET** `/api/statistics?month=01&year=2026`

احصل على إحصائيات مالية وتشغيلية

**Parameters:**
- `month` (optional): رقم الشهر (01-12)
- `year` (optional): السنة (مثال: 2026)

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "https://autoprotectagadir.pythonanywhere.com/api/statistics?month=01&year=2026"
```

**Response:**
```json
{
  "period": "2026-01",
  "agents": {
    "total": 10,
    "active": 7
  },
  "tasks": {
    "total": 45,
    "pending": 10,
    "in_progress": 15,
    "completed": 20
  },
  "financial": {
    "total_purchases": 50000.00,
    "total_income": 150000.00,
    "profit": 100000.00,
    "purchases_count": 30,
    "income_count": 50
  }
}
```

---

## 👥 إدارة الموظفين (Agents)

### عرض جميع الموظفين

**GET** `/api/agents`

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://autoprotectagadir.pythonanywhere.com/api/agents
```

**Response:**
```json
{
  "count": 10,
  "agents": [
    {
      "id": 1,
      "name": "محمد أحمد",
      "phone": "0612345678",
      "email": "mohamed@example.com",
      "created_at": "2026-01-01T10:00:00"
    }
  ]
}
```

### إضافة موظف جديد

**POST** `/api/agents`

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "أحمد محمد",
    "phone": "0612345678",
    "email": "ahmed@example.com"
  }' \
  https://autoprotectagadir.pythonanywhere.com/api/agents
```

**Response:**
```json
{
  "success": true,
  "agent": {
    "id": 11,
    "name": "أحمد محمد",
    "phone": "0612345678",
    "email": "ahmed@example.com"
  }
}
```

### عرض تفاصيل موظف محدد

**GET** `/api/agents/:id`

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://autoprotectagadir.pythonanywhere.com/api/agents/1
```

**Response:**
```json
{
  "id": 1,
  "name": "محمد أحمد",
  "phone": "0612345678",
  "email": "mohamed@example.com",
  "created_at": "2026-01-01T10:00:00",
  "tasks_count": 15,
  "purchases_count": 8,
  "income_count": 20
}
```

### تحديث موظف

**PUT** `/api/agents/:id`

```bash
curl -X PUT \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "محمد أحمد المحدث",
    "phone": "0698765432"
  }' \
  https://autoprotectagadir.pythonanywhere.com/api/agents/1
```

### حذف موظف

**DELETE** `/api/agents/:id`

```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://autoprotectagadir.pythonanywhere.com/api/agents/1
```

### تقرير أداء موظف

**GET** `/api/agents/:id/performance?month=01&year=2026`

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "https://autoprotectagadir.pythonanywhere.com/api/agents/1/performance?month=01&year=2026"
```

**Response:**
```json
{
  "agent": {
    "id": 1,
    "name": "محمد أحمد",
    "phone": "0612345678",
    "email": "mohamed@example.com"
  },
  "period": "2026-01",
  "tasks": {
    "total": 15,
    "completed": 10,
    "pending": 3,
    "in_progress": 2
  },
  "financial": {
    "purchases": 5000.00,
    "income": 25000.00,
    "commission": 2500.00
  }
}
```

---

## 📋 إدارة المهام (Tasks)

### عرض جميع المهام

**GET** `/api/tasks?status=completed&agent_id=1`

**Parameters:**
- `status` (optional): pending, in_progress, completed
- `agent_id` (optional): رقم الموظف

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "https://autoprotectagadir.pythonanywhere.com/api/tasks?status=completed"
```

**Response:**
```json
{
  "count": 20,
  "tasks": [
    {
      "id": 1,
      "title": "تأمين سيارة",
      "description": "تأمين شامل",
      "status": "completed",
      "price": 5000.00,
      "agent_commission": 500.00,
      "agent": {
        "id": 1,
        "name": "محمد أحمد"
      },
      "created_at": "2026-01-10T10:00:00",
      "completed_at": "2026-01-15T14:00:00",
      "due_date": "2026-01-20T00:00:00"
    }
  ]
}
```

### إضافة مهمة جديدة

**POST** `/api/tasks`

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "تأمين سيارة جديدة",
    "description": "تأمين ضد الغير",
    "agent_id": 1,
    "price": 3000,
    "agent_commission": 300,
    "status": "pending"
  }' \
  https://autoprotectagadir.pythonanywhere.com/api/tasks
```

### تحديث مهمة

**PUT** `/api/tasks/:id`

```bash
curl -X PUT \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "price": 3500
  }' \
  https://autoprotectagadir.pythonanywhere.com/api/tasks/1
```

### حذف مهمة

**DELETE** `/api/tasks/:id`

```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://autoprotectagadir.pythonanywhere.com/api/tasks/1
```

---

## 💰 إدارة المشتريات (Purchases)

### عرض جميع المشتريات

**GET** `/api/purchases?agent_id=1&month=01&year=2026`

**Parameters:**
- `agent_id` (optional): رقم الموظف
- `month` (optional): الشهر
- `year` (optional): السنة

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "https://autoprotectagadir.pythonanywhere.com/api/purchases?month=01&year=2026"
```

**Response:**
```json
{
  "count": 30,
  "total_amount": 50000.00,
  "purchases": [
    {
      "id": 1,
      "description": "شراء لوازم مكتبية",
      "amount": 500.00,
      "agent": {
        "id": 1,
        "name": "محمد أحمد"
      },
      "created_at": "2026-01-10T10:00:00"
    }
  ]
}
```

### إضافة مشترى جديد

**POST** `/api/purchases`

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "شراء معدات",
    "amount": 1500,
    "agent_id": 1
  }' \
  https://autoprotectagadir.pythonanywhere.com/api/purchases
```

### تحديث مشترى

**PUT** `/api/purchases/:id`

### حذف مشترى

**DELETE** `/api/purchases/:id`

---

## 💵 إدارة المداخيل (Income)

### عرض جميع المداخيل

**GET** `/api/income?agent_id=1&month=01&year=2026`

```bash
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  "https://autoprotectagadir.pythonanywhere.com/api/income?month=01&year=2026"
```

**Response:**
```json
{
  "count": 50,
  "total_amount": 150000.00,
  "income": [
    {
      "id": 1,
      "description": "تأمين سيارة",
      "amount": 5000.00,
      "discount": 500.00,
      "discount_description": "خصم عميل مميز",
      "final_amount": 4500.00,
      "agent": {
        "id": 1,
        "name": "محمد أحمد"
      },
      "created_at": "2026-01-10T10:00:00"
    }
  ]
}
```

### إضافة مدخول جديد

**POST** `/api/income`

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "تأمين شامل",
    "amount": 6000,
    "discount": 600,
    "discount_description": "خصم 10%",
    "agent_id": 1
  }' \
  https://autoprotectagadir.pythonanywhere.com/api/income
```

### تحديث مدخول

**PUT** `/api/income/:id`

### حذف مدخول

**DELETE** `/api/income/:id`

---

## 📝 أمثلة على الاستخدام

### مثال Python

```python
import requests

API_URL = "https://autoprotectagadir.pythonanywhere.com/api"
TOKEN = "your_token_here"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# عرض جميع الموظفين
response = requests.get(f"{API_URL}/agents", headers=headers)
agents = response.json()
print(f"عدد الموظفين: {agents['count']}")

# إضافة مهمة جديدة
new_task = {
    "title": "تأمين سيارة",
    "description": "تأمين شامل",
    "agent_id": 1,
    "price": 5000,
    "agent_commission": 500
}
response = requests.post(f"{API_URL}/tasks", json=new_task, headers=headers)
print(response.json())

# الحصول على إحصائيات
response = requests.get(f"{API_URL}/statistics?month=01&year=2026", headers=headers)
stats = response.json()
print(f"الربح: {stats['financial']['profit']}")
```

### مثال JavaScript (Node.js)

```javascript
const axios = require('axios');

const API_URL = 'https://autoprotectagadir.pythonanywhere.com/api';
const TOKEN = 'your_token_here';

const headers = {
  'Authorization': `Bearer ${TOKEN}`,
  'Content-Type': 'application/json'
};

// عرض جميع الموظفين
axios.get(`${API_URL}/agents`, { headers })
  .then(response => {
    console.log(`عدد الموظفين: ${response.data.count}`);
  });

// إضافة موظف جديد
axios.post(`${API_URL}/agents`, {
  name: 'أحمد محمد',
  phone: '0612345678',
  email: 'ahmed@example.com'
}, { headers })
  .then(response => {
    console.log('تم إضافة الموظف:', response.data);
  });
```

---

## ⚠️ معالجة الأخطاء

### أكواد الحالة (Status Codes)

- `200` - نجح الطلب
- `201` - تم الإنشاء بنجاح
- `400` - خطأ في البيانات المرسلة
- `401` - فشل المصادقة (Token غير صحيح)
- `404` - العنصر غير موجود

### مثال على رد خطأ

```json
{
  "error": "name required"
}
```

---

## 🔒 الأمان

1. **احتفظ بـ Token في مكان آمن**
2. **لا تشارك Token مع الآخرين**
3. **استخدم HTTPS دائماً**
4. **قم بإلغاء Token إذا تم اختراقه**

---

## 📞 الدعم

للمزيد من المساعدة:
- الموقع: https://autoprotectagadir.pythonanywhere.com
- الإعدادات: https://autoprotectagadir.pythonanywhere.com/settings
- API Tokens: https://autoprotectagadir.pythonanywhere.com/api_tokens

---

**النسخة:** 1.75  
**آخر تحديث:** 17 يناير 2026
