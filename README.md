# 🚗 Auto Protect Database

<div align="center">

![Auto Protect](https://img.shields.io/badge/Auto_Protect-Database-blue?style=for-the-badge&logo=flask)
![Python](https://img.shields.io/badge/Python-3.9+-green?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.3+-red?style=for-the-badge&logo=flask)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple?style=for-the-badge&logo=bootstrap)

**نظام إدارة شامل لشركات تغليف السيارات في المغرب**

**A comprehensive management system for car wrapping businesses in Morocco**

[🚀 Quick Start](#quick-start) | [📖 Documentation](#documentation) | [🌐 Deploy](#deployment)

</div>

---

## 📝 Overview | نظرة عامة

A complete web-based database system for managing agents, tasks, income, expenses, and performance tracking for car wrapping businesses.

## Features

### 🔐 Admin Authentication
- Secure login with Flask-Login
- Password change functionality
- Session-based access control

### 👥 Agent Management
- Create, edit, delete agents
- Store agent contact info (phone, email)
- Custom parameters for each agent
- Bulk import from Excel

### 📋 Task Management
- Create and assign tasks to agents
- Set due dates and descriptions
- Track task assignments

### 💰 Daily Purchases (Leader Page)
- Record daily purchases by agent
- Auto-calculate monthly totals
- Track purchases with dates and notes
- Car wrapping focused interface

### 📊 Daily Income Tracking
- Record income by source
- Auto-calculate monthly income totals
- Track with dates and notes
- Financial overview

### 📁 File Management
- Upload XLS/XLSX files
- Auto-parse and import agents, purchases, income
- Download individual files or all as ZIP
- Support for multiple sheet formats

### 📝 Activity Logs
- Complete audit trail of all actions
- View, add, delete log entries
- Track admin activities

### 🔑 API Token Management
- Create secure API tokens
- Token-based API authentication
- Revoke tokens anytime
- REST JSON endpoints

### 🎨 Modern UI
- Bootstrap 5 responsive design
- Clean, professional interface
- Mobile-friendly navigation
- Organized dashboard

## Quick Start

### 1. Setup Environment

```bash
cd "/Users/apple/Desktop/auto protect Data Base"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python3 -c "from app import app, db; from models import Admin; from werkzeug.security import generate_password_hash; app.app_context().push(); db.create_all(); admin = Admin(username='admin', password_hash=generate_password_hash('admin123')); db.session.add(admin); db.session.commit(); print('✓ Database ready')"
```

### 3. Run the App

```bash
export FLASK_APP=app.py
python3 app.py
```

Server starts at: **http://127.0.0.1:5000**

## Default Credentials

- **Username:** `admin`
- **Password:** `admin123`

⚠️ Change password immediately after first login!

## Project Structure

```
auto protect Data Base/
├── app.py                  # Main Flask application
├── models.py              # SQLAlchemy database models
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── app.db                 # SQLite database (auto-created)
├── uploads/               # Uploaded XLS/XLSX files
└── templates/             # HTML templates
    ├── base.html          # Base template with navbar
    ├── login.html         # Login page
    ├── admin_dashboard.html
    ├── agents.html
    ├── agent_form.html
    ├── tasks.html
    ├── leader.html        # Purchases page
    ├── income.html
    ├── logs.html
    ├── change_password.html
    ├── api_tokens.html
    └── upload_files.html
```

## Database Models

### Admin
- Secure login credentials
- Manages all operations

### Agent
- Name, phone, email
- Custom parameters (JSON)

### Task
- Title, description
- Assigned to agent
- Due date tracking

### Purchase
- Agent + amount
- Date, notes
- Monthly aggregation

### Income
- Amount, source
- Date, notes
- Monthly aggregation

### Log
- Complete audit trail
- Action + details
- Timestamp

### APIToken
- Token-based API access
- Create/revoke tokens
- Non-expiring

### FileUpload
- Track uploaded files
- Auto-import parsing

## Excel Import

Supported sheet formats for auto-import:

### Agents Sheet
| Columns | Alternative Names |
|---------|------------------|
| Name | Agent, Agente, Agent_Name |
| Phone | Telefone |
| Email | E-mail |

### Purchases Sheet
| Columns | Alternative Names |
|---------|------------------|
| Amount | Valor |
| Agent_ID | Agent |
| Date | - |
| Note | - |

### Income Sheet
| Columns | Notes |
|---------|-------|
| Amount | Required |
| Source | Required |
| Date | Optional |
| Note | Optional |

Upload Excel files via **Files → Upload XLS**.

## API Endpoints

All API endpoints require authentication (login OR API token).

### List Agents (GET)
```bash
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:5000/api/agents
```

### Create Agent (POST)
```bash
curl -X POST -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","phone":"555-1234","email":"john@example.com"}' \
  http://localhost:5000/api/agents
```

### List Tasks (GET)
```bash
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:5000/api/tasks
```

## Technologies Used

- **Backend:** Flask 2.3.3
- **Database:** SQLite + SQLAlchemy ORM
- **Auth:** Flask-Login 0.6.3
- **Frontend:** Bootstrap 5
- **Excel:** Pandas + openpyxl
- **Python:** 3.9+

## Navigation

After login, use the top navbar:
- **Dashboard** – Quick overview
- **Agents** – Manage team
- **Tasks** – Task assignments
- **Leader** – Daily purchases & monthly totals
- **Income** – Daily income & monthly totals
- **Files** – Upload/download Excel files
- **Logs** – Audit trail
- **API Tokens** – Generate API keys
- **[Admin] → Change Password** – Update credentials

## Security Notes

1. ✅ Passwords are hashed with Werkzeug
2. ✅ API tokens are random 48-char hex strings
3. ✅ All actions logged automatically
4. ✅ Login required for all pages
5. ⚠️ Change default admin password immediately
6. ⚠️ Keep API tokens secret (cannot be re-displayed)

## Troubleshooting

### Port 5000 already in use?
```bash
lsof -ti:5000 | xargs kill -9
```

### Database locked?
```bash
rm app.db
# Re-initialize database
```

### Dependencies issue?
```bash
pip install --upgrade -r requirements.txt
```

## Future Enhancements

- Email notifications
- Advanced reporting & charts
- Multi-admin support
- Role-based access control
- Data export to CSV/PDF
- Mobile app
- Webhook integrations

## Support

For issues or questions, check the logs at: **Logs page → All Logs section**

---

**Version:** 1.0  
**Created:** December 29, 2025  
**License:** MIT

