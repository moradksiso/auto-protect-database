# Quick Start Guide

## 1️⃣ First Time Setup (2 minutes)

```bash
cd "/Users/apple/Desktop/auto protect Data Base"
source venv/bin/activate
```

## 2️⃣ Start the Server

```bash
python3 app.py
```

You'll see:
```
* Running on http://127.0.0.1:5000
```

## 3️⃣ Login

Open browser → **http://127.0.0.1:5000**

- Username: `admin`
- Password: `admin123`

**Change password immediately!** (Admin → Change Password)

---

## Dashboard Overview

After login, you'll see:

### Left Panel
- **Agents** – Manage team members
  - Add/Edit/Delete agents
  - Store contact info

### Center Panel
- **Files** – Upload Excel files
  - Auto-imports agents, purchases, income
  - Download files individually or as ZIP

### Right Panel
- **Recent Tasks** – Quick view
  - Create new tasks
  - Assign to agents

---

## Common Tasks

### 📋 Add an Agent
1. Navigate to **Agents**
2. Click **+ Add Agent**
3. Enter name, phone, email
4. Click **Save**

### 📁 Upload Purchases/Income Data
1. Prepare Excel file with columns:
   - For purchases: Name, Amount, Date, Note
   - For income: Amount, Source, Date, Note
2. Go to **Files → Upload XLS**
3. Select file → Click **Upload**
4. Data auto-imports to **Leader** and **Income** pages

### 💰 Record Daily Purchase
1. Go to **Leader**
2. Select agent from dropdown
3. Enter amount, date, note
4. Click **Add Purchase**
5. View monthly total on right side

### 💵 Record Daily Income
1. Go to **Income**
2. Enter amount, source
3. Enter date and optional note
4. Click **Add Income**
5. View monthly total on right side

### 📝 Create Task for Agent
1. Go to **Tasks**
2. Enter title, select agent
3. Set due date (optional)
4. Add description (optional)
5. Click **Create Task**

### 🔑 Generate API Token
1. Go to **API Tokens**
2. Enter token name (e.g., "Mobile App")
3. Click **Create Token**
4. Copy token immediately (shown only once!)
5. Use in API calls with: `Authorization: Token YOUR_TOKEN`

### 📊 View Activity Logs
1. Go to **Logs**
2. See all actions with timestamps
3. Add manual log entry if needed
4. Delete old entries to clean up

---

## API Examples

### Get all agents
```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:5000/api/agents
```

### Create new agent via API
```bash
curl -X POST \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"John","phone":"555-1234"}' \
  http://localhost:5000/api/agents
```

### Get all tasks
```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:5000/api/tasks
```

---

## Troubleshooting

**Q: Server won't start?**
```bash
# Kill any existing process on port 5000
lsof -ti:5000 | xargs kill -9
python3 app.py
```

**Q: Forgot password?**
- Delete `app.db`
- Restart server
- Login with defaults again: `admin` / `admin123`

**Q: Excel import didn't work?**
- Check column names match expected format
- Ensure no empty rows before data
- Try uploading again

**Q: API token not working?**
- Copy the exact token (shown only once)
- Use format: `Authorization: Token YOUR_TOKEN`
- Check token isn't revoked in **API Tokens** page

---

## File Locations

- Database: `/Users/apple/Desktop/auto protect Data Base/app.db`
- Uploads: `/Users/apple/Desktop/auto protect Data Base/uploads/`
- Logs: View in app under **Logs** tab

---

## Next Steps

1. ✅ Change admin password
2. ✅ Add your team (agents)
3. ✅ Upload initial data or start recording
4. ✅ Create tasks for agents
5. ✅ Generate API token if needed
6. ✅ Bookmark http://localhost:5000 for quick access

---

Enjoy managing your car wrapping company! 🚗
