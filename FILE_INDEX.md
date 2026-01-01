# Auto Protect Database System - File Index

## 📂 Project Root Files

### Core Application
- **app.py** (471 lines)
  - Main Flask application
  - All routes and endpoints
  - Authentication, CRUD operations
  - Excel import logic
  - API endpoints
  
- **models.py** (70+ lines)
  - SQLAlchemy ORM models
  - Admin, Agent, Task, Purchase, Income, Log, APIToken, FileUpload
  - Database schema definitions

- **config.py** (6 lines)
  - Flask configuration
  - Database URI
  - Upload folder settings
  - Secret key management

- **requirements.txt**
  - Flask==2.3.3
  - Flask-SQLAlchemy==3.0.4
  - Flask-Login==0.6.3
  - Werkzeug==2.3.7
  - pandas==1.5.3
  - openpyxl==3.1.2
  - python-dotenv==1.0.0
  - flask-compress==1.13
  - Flask-WTF==1.1.1

### Documentation
- **README.md** (300+ lines)
  - Complete feature documentation
  - Quick start instructions
  - Database models overview
  - Excel import formats
  - API endpoint examples
  - Technologies used
  - Troubleshooting guide

- **QUICK_START.md** (200+ lines)
  - Step-by-step setup
  - Dashboard overview
  - Common task examples
  - API usage examples
  - Troubleshooting Q&A

- **IMPLEMENTATION_COMPLETE.md** (400+ lines)
  - Project summary
  - Complete feature list
  - Security checklist
  - Testing information
  - Deployment notes

### Database
- **app.db**
  - SQLite database (auto-created on first run)
  - Contains all data: admin, agents, tasks, purchases, income, logs, tokens

---

## 🎨 Templates (14 HTML files)

### Base Layout
- **base.html**
  - Master template with Bootstrap navbar
  - Navigation menu with dropdown user profile
  - Flash message display
  - Footer

- **_bootstrap_head.html**
  - Bootstrap 5 CDN includes

### Authentication
- **login.html**
  - Admin login form
  - Centered card design
  - Bootstrap validation

### Dashboard & Navigation
- **admin_dashboard.html**
  - Main dashboard after login
  - Agent quick view
  - File uploads listing
  - Recent tasks
  - Quick action buttons

### Agent Management
- **agents.html**
  - Agent list table
  - Add/Edit/Delete buttons
  - Responsive table design
  - Sorting support

- **agent_form.html**
  - Add/Edit agent form
  - Name, phone, email, params fields
  - Form validation
  - Cancel/Save buttons

### Task Management
- **tasks.html**
  - Create task form
  - Agent selection dropdown
  - Due date input
  - Description textarea
  - Recent tasks list

### Financial Tracking
- **leader.html** (Purchases)
  - Daily purchase entry form
  - Agent dropdown
  - Amount + date input
  - Monthly totals auto-calculated
  - Recent purchases table (last 50)
  - Car wrapping themed

- **income.html** (Income)
  - Daily income entry form
  - Source + amount input
  - Date selection
  - Monthly totals auto-calculated
  - Recent income table (last 50)

### File Management
- **upload_files.html**
  - File upload form
  - Format info (.xls, .xlsx)
  - Auto-import guidance
  - Single file input

### Logging
- **logs.html**
  - Manual log entry form
  - Action + detail fields
  - Complete audit log table
  - Delete action buttons
  - Timestamp display

### Account Management
- **change_password.html**
  - Current password input
  - New password with confirmation
  - Validation (6+ chars)
  - Cancel/Save buttons

### API Management
- **api_tokens.html**
  - Token creation form
  - Descriptive name input
  - Existing tokens table
  - Status badges (active/revoked)
  - Token display (one-time on creation)
  - Revoke button
  - API usage example

---

## 📁 Directories

### /uploads/
- Stores uploaded Excel files
- Auto-created on first file upload
- Contains .xls and .xlsx files
- Referenced in FileUpload database model

### /venv/
- Python virtual environment
- All installed packages
- Separate from system Python
- Can be deleted and recreated from requirements.txt

### /templates/
- 14 HTML template files
- Bootstrap 5 responsive design
- Form validation
- Flash message support
- Dynamic content with Jinja2

### /__pycache__/
- Auto-generated Python cache files
- Safe to delete
- Recreated on next run

---

## 📊 Statistics

| Item | Count |
|------|-------|
| Python Files | 3 |
| HTML Templates | 14 |
| Database Models | 8 |
| API Endpoints | 2 |
| Routes | 22+ |
| Documentation Files | 4 |
| Total Lines of Code | 500+ |
| Dependencies | 9 |

---

## 🔄 Data Flow

```
User
  ↓
Login (templates/login.html)
  ↓
app.py [routes]
  ↓
models.py [database]
  ↓
app.db [SQLite]
  ↓
Dashboard (templates/admin_dashboard.html)
  ↓
Agents / Tasks / Purchases / Income / Files / Logs
  ↓
Database Updates → Audit Logs
```

---

## 🚀 Quick Commands

### Start Server
```bash
cd "/Users/apple/Desktop/auto protect Data Base"
source venv/bin/activate
python3 app.py
```

### Access Application
```
http://127.0.0.1:5000
```

### Reset Database
```bash
rm app.db
python3 app.py  # Recreates with defaults
```

### View Database
```bash
python3 -c "from app import db; from models import *; import sqlite3; conn = sqlite3.connect('app.db'); print('Tables:', [row[0] for row in conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall()])"
```

---

## 📝 File Descriptions Summary

| File | Purpose | Size |
|------|---------|------|
| app.py | Main Flask app + all routes | 471 lines |
| models.py | Database models | 70 lines |
| config.py | Configuration | 6 lines |
| requirements.txt | Dependencies | 9 packages |
| README.md | Feature docs | 300+ lines |
| QUICK_START.md | Quick reference | 200+ lines |
| IMPLEMENTATION_COMPLETE.md | Project summary | 400+ lines |
| login.html | Login page | ~30 lines |
| admin_dashboard.html | Main dashboard | ~50 lines |
| agents.html | Agent list | ~25 lines |
| agent_form.html | Agent form | ~20 lines |
| tasks.html | Task management | ~30 lines |
| leader.html | Purchase tracking | ~40 lines |
| income.html | Income tracking | ~40 lines |
| logs.html | Activity logs | ~45 lines |
| api_tokens.html | Token management | ~50 lines |
| change_password.html | Password change | ~25 lines |
| upload_files.html | File upload | ~20 lines |
| base.html | Base template | ~45 lines |
| _bootstrap_head.html | Bootstrap CDN | ~2 lines |

---

**Last Updated:** December 29, 2025  
**Status:** Complete & Functional  
**Version:** 1.0
