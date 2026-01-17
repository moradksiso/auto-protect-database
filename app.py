import os
import io
import zipfile
import secrets
from datetime import datetime

import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, send_file, jsonify, g, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import text

from models import db, Admin, Agent, Task, FileUpload, Purchase, Income, Log, APIToken, ServiceType, CarType
import config
from translations import get_translation

app = Flask(__name__)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['VERSION'] = '1.75'  # Application version

# ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# init database
db.init_app(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# One-time startup flag
_startup_done = False

@login_manager.user_loader
def load_user(user_id):
    # user_id is prefixed: "admin:<id>" or "agent:<id>"
    try:
        kind, raw_id = str(user_id).split(":", 1)
        _id = int(raw_id)
        if kind == 'admin':
            return db.session.get(Admin, _id)
        if kind == 'agent':
            return db.session.get(Agent, _id)
    except Exception:
        pass
    return None


@app.before_request
def create_tables():
    global _startup_done
    if _startup_done:
        return
    _startup_done = True
    
    db.create_all()
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin', password_hash=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()

    # Lightweight migration: ensure agent login columns exist
    try:
        with db.engine.begin() as conn:
            # Agent table migrations
            cols = conn.exec_driver_sql("PRAGMA table_info(agent)").fetchall()
            names = {row[1] for row in cols}
            statements = []
            if 'username' not in names:
                statements.append("ALTER TABLE agent ADD COLUMN username TEXT")
            if 'password_hash' not in names:
                statements.append("ALTER TABLE agent ADD COLUMN password_hash TEXT")
            if 'is_active' not in names:
                statements.append("ALTER TABLE agent ADD COLUMN is_active INTEGER DEFAULT 1")
            for stmt in statements:
                conn.exec_driver_sql(stmt)
            conn.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_username ON agent(username) WHERE username IS NOT NULL")
            
            # Income table migration: add agent_id, customer_name, service_type, car_type, invoice_number, discount, discount_description
            income_cols = conn.exec_driver_sql("PRAGMA table_info(income)").fetchall()
            income_names = {row[1] for row in income_cols}
            income_statements = []
            if 'agent_id' not in income_names:
                income_statements.append("ALTER TABLE income ADD COLUMN agent_id INTEGER")
            if 'customer_name' not in income_names:
                income_statements.append("ALTER TABLE income ADD COLUMN customer_name TEXT")
            if 'service_type' not in income_names:
                income_statements.append("ALTER TABLE income ADD COLUMN service_type TEXT")
            if 'car_type' not in income_names:
                income_statements.append("ALTER TABLE income ADD COLUMN car_type TEXT")
            if 'invoice_number' not in income_names:
                income_statements.append("ALTER TABLE income ADD COLUMN invoice_number TEXT")
            if 'discount' not in income_names:
                income_statements.append("ALTER TABLE income ADD COLUMN discount REAL DEFAULT 0.0")
            if 'discount_description' not in income_names:
                income_statements.append("ALTER TABLE income ADD COLUMN discount_description TEXT")
            for stmt in income_statements:
                conn.exec_driver_sql(stmt)
            
            # Task table migration: add completed, completed_at, income_id, car_count, agent_commission, show_commission_in_invoice
            task_cols = conn.exec_driver_sql("PRAGMA table_info(task)").fetchall()
            task_names = {row[1] for row in task_cols}
            task_statements = []
            if 'completed' not in task_names:
                task_statements.append("ALTER TABLE task ADD COLUMN completed INTEGER DEFAULT 0")
            if 'completed_at' not in task_names:
                task_statements.append("ALTER TABLE task ADD COLUMN completed_at TEXT")
            if 'income_id' not in task_names:
                task_statements.append("ALTER TABLE task ADD COLUMN income_id INTEGER")
            if 'car_count' not in task_names:
                task_statements.append("ALTER TABLE task ADD COLUMN car_count INTEGER DEFAULT 0")
            if 'agent_commission' not in task_names:
                task_statements.append("ALTER TABLE task ADD COLUMN agent_commission REAL DEFAULT 0.0")
            if 'show_commission_in_invoice' not in task_names:
                task_statements.append("ALTER TABLE task ADD COLUMN show_commission_in_invoice INTEGER DEFAULT 0")
            for stmt in task_statements:
                conn.exec_driver_sql(stmt)
        
        db.engine.dispose()
    except Exception:
        pass


@app.before_request
def set_language():
    """Set language for current request"""
    if 'lang' not in session:
        session['lang'] = 'ar'  # Default to Arabic
    g.lang = session.get('lang', 'ar')
    g.t = lambda key: get_translation(key, g.lang)


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            login_user(admin)
            flash('Logged in')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')


# Agent login (separate endpoint)
@app.route('/agent/login', methods=['GET', 'POST'])
def agent_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        agent = Agent.query.filter_by(username=username, is_active=True).first()
        if agent and agent.password_hash and check_password_hash(agent.password_hash, password):
            login_user(agent)
            flash('Logged in as agent')
            return redirect(url_for('agent_dashboard'))
        flash('Invalid agent credentials')
    return render_template('agent_login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/toggle_language')
def toggle_language():
    """Toggle between Arabic and English"""
    current_lang = session.get('lang', 'ar')
    session['lang'] = 'en' if current_lang == 'ar' else 'ar'
    return redirect(request.referrer or url_for('index'))


@app.route('/admin')
@login_required
def admin_dashboard():
    from datetime import date
    from dateutil.relativedelta import relativedelta
    
    agents = Agent.query.all()
    files = FileUpload.query.order_by(FileUpload.uploaded_at.desc()).limit(5).all()
    tasks = Task.query.order_by(Task.assigned_at.desc()).limit(10).all()
    
    # Current month stats
    today = date.today()
    first_day = today.replace(day=1)
    
    # Purchases this month
    purchases_month = Purchase.query.filter(Purchase.date >= first_day).all()
    total_purchases = sum(p.amount for p in purchases_month)
    
    # Income this month (with discount applied)
    income_month = Income.query.filter(Income.date >= first_day).all()
    total_income = sum((i.amount - (i.discount or 0)) for i in income_month)
    
    # Profit
    profit = total_income - total_purchases
    
    # Open tasks
    open_tasks = Task.query.filter(Task.due_date >= today).count()
    overdue_tasks = Task.query.filter(Task.due_date < today).count()
    
    # Top performing agent
    agent_stats = {}
    for p in purchases_month:
        if p.agent_id:
            agent_stats[p.agent_id] = agent_stats.get(p.agent_id, 0) + p.amount
    
    top_agent = None
    if agent_stats:
        top_agent_id = max(agent_stats, key=agent_stats.get)
        top_agent = Agent.query.get(top_agent_id)
    
    stats = {
        'total_purchases': total_purchases,
        'total_income': total_income,
        'profit': profit,
        'open_tasks': open_tasks,
        'overdue_tasks': overdue_tasks,
        'top_agent': top_agent,
        'agents_count': len(agents)
    }
    
    return render_template('admin_dashboard.html', agents=agents, files=files, tasks=tasks, stats=stats)


# Agent CRUD
@app.route('/agents')
@login_required
def agents_list():
    agents = Agent.query.all()
    return render_template('agents.html', agents=agents)


@app.route('/reports/performance')
@login_required
def performance_report():
    """Performance report for all agents - displays data only without profit calculations"""
    from datetime import date
    
    agents = Agent.query.all()
    report_data = []
    
    for agent in agents:
        today = date.today()
        first_day = today.replace(day=1)
        
        # Company income (not agent income) - for display only
        incomes = Income.query.filter_by(agent_id=agent.id).all()
        total_company_income = sum((i.amount - (i.discount or 0)) for i in incomes)
        
        # This month company income - for display only
        month_incomes = Income.query.filter(
            Income.agent_id == agent.id,
            Income.date >= first_day
        ).all()
        month_company_income = sum((i.amount - (i.discount or 0)) for i in month_incomes)
        
        # Agent commission from completed tasks
        completed_tasks = Task.query.filter(
            Task.agent_id == agent.id,
            Task.completed == True
        ).all()
        total_agent_commission = sum(t.agent_commission or 0 for t in completed_tasks)
        
        # This month agent commission
        month_tasks = [t for t in completed_tasks if t.completed_at and 
                      t.completed_at.strftime('%Y-%m') == today.strftime('%Y-%m')]
        month_agent_commission = sum(t.agent_commission or 0 for t in month_tasks)
        
        # Agent expenses (purchases)
        purchases = Purchase.query.filter_by(agent_id=agent.id).all()
        total_expenses = sum(p.amount for p in purchases)
        
        # This month expenses
        month_purchases = Purchase.query.filter(
            Purchase.agent_id == agent.id,
            Purchase.date >= first_day
        ).all()
        month_expenses = sum(p.amount for p in month_purchases)
        
        # Tasks statistics
        tasks_assigned = Task.query.filter_by(agent_id=agent.id).count()
        tasks_completed = len(completed_tasks)
        
        # Cars wrapped this month
        cars_this_month = sum(t.car_count or 0 for t in month_tasks)
        
        # Total cars wrapped
        total_cars = sum(t.car_count or 0 for t in completed_tasks)
        
        report_data.append({
            'agent': agent,
            'total_company_income': total_company_income,
            'month_company_income': month_company_income,
            'total_agent_commission': total_agent_commission,
            'month_agent_commission': month_agent_commission,
            'total_expenses': total_expenses,
            'month_expenses': month_expenses,
            'tasks_assigned': tasks_assigned,
            'tasks_completed': tasks_completed,
            'cars_this_month': cars_this_month,
            'total_cars': total_cars
        })
    
    # Sort by month company income descending
    report_data.sort(key=lambda x: x['month_company_income'], reverse=True)
    
    return render_template('performance_report.html', report_data=report_data)


@app.route('/agents/new', methods=['GET', 'POST'])
@login_required
def agent_new():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form.get('phone')
        email = request.form.get('email')
        params = request.form.get('params')
        # Auto-create agent login
        base = (email or name or '').strip().lower()
        base = ''.join(ch if ch.isalnum() else '.' for ch in base)
        base = base or f"agent{int(datetime.utcnow().timestamp())}"
        username = base
        idx = 1
        while Agent.query.filter_by(username=username).first():
            idx += 1
            username = f"{base}.{idx}"
        temp_password = secrets.token_urlsafe(8)
        agent = Agent(
            name=name,
            phone=phone,
            email=email,
            params=params,
            username=username,
            password_hash=generate_password_hash(temp_password),
        )
        db.session.add(agent)
        db.session.commit()
        if isinstance(current_user, Admin):
            db.session.add(Log(action='create_agent', detail=f'Agent {name} created with username: {username}', created_by=current_user.id))
            db.session.commit()
        flash(f"✅ Agent created successfully!\n🔑 Username: {username}\n🔐 Temporary Password: {temp_password}\n⚠️ Save this password - it will not be shown again!", 'success')
        return redirect(url_for('agents_list'))
    return render_template('agent_form.html', agent=None)


@app.route('/agent')
@login_required
def agent_dashboard():
    # If an admin hits this, show a simple redirect
    if isinstance(current_user, Admin):
        return redirect(url_for('admin_dashboard'))
    
    # Show tasks assigned to the agent
    tasks = Task.query.filter_by(agent_id=current_user.id).order_by(Task.assigned_at.desc()).all()
    
    # Personal statistics
    from datetime import date
    from dateutil.relativedelta import relativedelta
    
    today = date.today()
    first_day = today.replace(day=1)
    
    # Income by this agent
    all_incomes = Income.query.filter_by(agent_id=current_user.id).all()
    month_incomes = Income.query.filter(
        Income.agent_id == current_user.id,
        Income.date >= first_day
    ).all()
    
    total_income_all_time = sum(i.amount for i in all_incomes)
    total_income_this_month = sum(i.amount for i in month_incomes)
    
    # Purchases by this agent
    all_purchases = Purchase.query.filter_by(agent_id=current_user.id).all()
    month_purchases = Purchase.query.filter(
        Purchase.agent_id == current_user.id,
        Purchase.date >= first_day
    ).all()
    
    total_purchases_all_time = sum(p.amount for p in all_purchases)
    total_purchases_this_month = sum(p.amount for p in month_purchases)
    
    # Tasks
    open_tasks = Task.query.filter(
        Task.agent_id == current_user.id,
        Task.due_date >= today
    ).count()
    
    overdue_tasks = Task.query.filter(
        Task.agent_id == current_user.id,
        Task.due_date < today
    ).count()
    
    # Calculate ranking based on income
    agent_stats = {}
    all_month_incomes = Income.query.filter(Income.date >= first_day).all()
    for inc in all_month_incomes:
        if inc.agent_id:
            agent_stats[inc.agent_id] = agent_stats.get(inc.agent_id, 0) + inc.amount
    
    sorted_agents = sorted(agent_stats.items(), key=lambda x: x[1], reverse=True)
    ranking = None
    for idx, (agent_id, amount) in enumerate(sorted_agents, 1):
        if agent_id == current_user.id:
            ranking = idx
            break
    
    stats = {
        'total_income_all_time': total_income_all_time,
        'total_income_this_month': total_income_this_month,
        'total_purchases_all_time': total_purchases_all_time,
        'total_purchases_this_month': total_purchases_this_month,
        'open_tasks': open_tasks,
        'overdue_tasks': overdue_tasks,
        'ranking': ranking,
        'total_agents': len(agent_stats)
    }
    
    return render_template('agent_dashboard.html', tasks=tasks, stats=stats, today=today)


@app.route('/agents/<int:agent_id>/edit', methods=['GET', 'POST'])
@login_required
def agent_edit(agent_id):
    agent = Agent.query.get_or_404(agent_id)
    if request.method == 'POST':
        agent.name = request.form['name']
        agent.phone = request.form.get('phone')
        agent.email = request.form.get('email')
        agent.params = request.form.get('params')
        # If username/password fields exist in form, allow updating them
        if 'username' in request.form and request.form['username']:
            agent.username = request.form['username']
        if 'new_password' in request.form and request.form['new_password']:
            agent.password_hash = generate_password_hash(request.form['new_password'])
        db.session.commit()
        if isinstance(current_user, Admin):
            db.session.add(Log(action='edit_agent', detail=f'Agent {agent.name} edited', created_by=current_user.id))
            db.session.commit()
        return redirect(url_for('agents_list'))
    return render_template('agent_form.html', agent=agent)


@app.route('/agents/<int:agent_id>/delete', methods=['POST'])
@login_required
def agent_delete(agent_id):
    agent = Agent.query.get_or_404(agent_id)
    name = agent.name
    db.session.delete(agent)
    db.session.commit()
    if isinstance(current_user, Admin):
        db.session.add(Log(action='delete_agent', detail=f'Agent {name} deleted', created_by=current_user.id))
        db.session.commit()
    return redirect(url_for('agents_list'))


@app.route('/agents/<int:agent_id>/reset_password', methods=['POST'])
@login_required
def agent_reset_password(agent_id):
    """Reset agent password and show it once"""
    agent = Agent.query.get_or_404(agent_id)
    
    # Generate new temporary password
    new_password = secrets.token_urlsafe(8)
    agent.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    # Log the action
    if isinstance(current_user, Admin):
        db.session.add(Log(
            action='reset_agent_password', 
            detail=f'Password reset for agent {agent.name} (username: {agent.username})', 
            created_by=current_user.id
        ))
        db.session.commit()
    
    flash(f"🔄 Password reset successful!\n👤 Agent: {agent.name}\n🔑 Username: {agent.username}\n🔐 New Password: {new_password}\n⚠️ Save this password - it will not be shown again!", 'warning')
    return redirect(url_for('agents_list'))


# Files upload/download
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config.get('ALLOWED_EXTENSIONS', set())


@app.route('/files/upload', methods=['GET', 'POST'])
@login_required
def files_upload():
    if request.method == 'POST':
        f = request.files.get('file')
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            f.save(path)
            fu = FileUpload(filename=filename, uploaded_by=current_user.id)
            db.session.add(fu)
            db.session.add(Log(action='upload_file', detail=f'Uploaded {filename}', created_by=current_user.id))
            db.session.commit()
            # Try to parse spreadsheet and import known data
            try:
                xls = pd.read_excel(path, sheet_name=None)
                imported = []
                for sheet, df in xls.items():
                    cols_map = {str(c).strip().lower(): c for c in df.columns}
                    lowered = set(cols_map.keys())
                    # Agents import
                    name_keys = ['name', 'nome', 'agent', 'agent_name']
                    name_col = None
                    for k in name_keys:
                        if k in lowered:
                            name_col = cols_map[k]
                            break
                    if name_col:
                        count = 0
                        phone_col = cols_map.get('phone') or cols_map.get('telefone')
                        email_col = cols_map.get('email') or cols_map.get('e-mail')
                        for _, row in df.iterrows():
                            name = row.get(name_col)
                            if not name or str(name).strip() == '':
                                continue
                            phone = row.get(phone_col) if phone_col in df.columns else None
                            email = row.get(email_col) if email_col in df.columns else None
                            # Auto-create login credentials
                            base = (str(email).strip().lower() if email and pd.notna(email) else str(name).strip().lower())
                            base = ''.join(ch if ch.isalnum() else '.' for ch in base)
                            base = base or f"agent{int(datetime.utcnow().timestamp())}"
                            username = base
                            idx = 1
                            while Agent.query.filter_by(username=username).first():
                                idx += 1
                                username = f"{base}.{idx}"
                            temp_password = secrets.token_urlsafe(8)
                            agent = Agent(
                                name=str(name).strip(),
                                phone=str(phone).strip() if phone and pd.notna(phone) else None,
                                email=str(email).strip() if email and pd.notna(email) else None,
                                username=username,
                                password_hash=generate_password_hash(temp_password)
                            )
                            db.session.add(agent)
                            count += 1
                        db.session.commit()
                        imported.append(f'Agents:{count}')
                    # Purchases import
                    amt_key = None
                    if 'amount' in lowered:
                        amt_key = 'amount'
                    elif 'valor' in lowered:
                        amt_key = 'valor'
                    if amt_key:
                        agent_key = 'agent_id' if 'agent_id' in lowered else ('agent' if 'agent' in lowered else None)
                        date_key = 'date' if 'date' in lowered else None
                        note_key = 'note' if 'note' in lowered else None
                        count = 0
                        for _, row in df.iterrows():
                            amt = row.get(cols_map.get(amt_key))
                            if not pd.notna(amt):
                                continue
                            agent_id = None
                            if agent_key:
                                agent_id = row.get(cols_map.get(agent_key))
                            date_val = None
                            try:
                                if date_key and pd.notna(row.get(cols_map.get(date_key))):
                                    date_val = pd.to_datetime(row.get(cols_map.get(date_key))).date()
                            except Exception:
                                date_val = None
                            p = Purchase(agent_id=int(agent_id) if pd.notna(agent_id) else None, amount=float(amt), note=str(row.get(cols_map.get(note_key)) or ''), date=date_val)
                            db.session.add(p)
                            count += 1
                        db.session.commit()
                        imported.append(f'Purchases:{count}')
                    # Income import
                    if 'amount' in lowered and 'source' in lowered:
                        count = 0
                        for _, row in df.iterrows():
                            amt = row.get(cols_map.get('amount'))
                            if not pd.notna(amt):
                                continue
                            source = row.get(cols_map.get('source'))
                            date_val = None
                            try:
                                if 'date' in cols_map and pd.notna(row.get(cols_map.get('date'))):
                                    date_val = pd.to_datetime(row.get(cols_map.get('date'))).date()
                            except Exception:
                                date_val = None
                            inc = Income(amount=float(amt), source=str(source) if pd.notna(source) else '', note=str(row.get(cols_map.get('note')) or ''), date=date_val)
                            db.session.add(inc)
                            count += 1
                        db.session.commit()
                        imported.append(f'Income:{count}')
                if imported:
                    db.session.add(Log(action='import_excel', detail=f'Imported: {";".join(imported)} from {filename}', created_by=current_user.id))
                    db.session.commit()
            except Exception as e:
                db.session.add(Log(action='import_error', detail=f'Error importing {filename}: {e}', created_by=current_user.id))
                db.session.commit()
            flash('File uploaded')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid file or no file')
    return render_template('upload_files.html')


@app.route('/files/download/<int:file_id>')
@login_required
def files_download(file_id):
    f = FileUpload.query.get_or_404(file_id)
    return send_from_directory(app.config['UPLOAD_FOLDER'], f.filename, as_attachment=True)


@app.route('/files/download_all')
@login_required
def files_download_all():
    files = FileUpload.query.all()
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, 'w') as zf:
        for f in files:
            path = os.path.join(app.config['UPLOAD_FOLDER'], f.filename)
            if os.path.exists(path):
                zf.write(path, arcname=f.filename)
    mem.seek(0)
    return send_file(mem, download_name='all_files.zip', as_attachment=True)


# Tasks
@app.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    is_agent = isinstance(current_user, Agent)
    
    if request.method == 'POST':
        # الموظف لا يستطيع إضافة مهام
        if is_agent:
            flash('غير مسموح للموظفين بإضافة مهام', 'danger')
            return redirect(url_for('tasks'))
        
        title = request.form['title']
        description = request.form.get('description')
        agent_id = request.form.get('agent_id')
        due = request.form.get('due_date')
        car_count = int(request.form.get('car_count', 0))
        agent_commission = float(request.form.get('agent_commission', 0))
        show_commission = request.form.get('show_commission_in_invoice') == 'on'
        due_date = datetime.strptime(due, '%Y-%m-%d').date() if due else None
        t = Task(
            title=title, 
            description=description, 
            agent_id=agent_id, 
            due_date=due_date, 
            car_count=car_count,
            agent_commission=agent_commission,
            show_commission_in_invoice=show_commission
        )
        db.session.add(t)
        db.session.add(Log(action='create_task', detail=f'Task {title} assigned to {agent_id}', created_by=current_user.id))
        db.session.commit()
        return redirect(url_for('tasks'))
    
    agents = Agent.query.all()
    
    # الموظف يرى مهامه فقط، المدير يرى كل المهام
    if is_agent:
        tasks_list = Task.query.filter_by(agent_id=current_user.id).order_by(Task.assigned_at.desc()).all()
    else:
        tasks_list = Task.query.order_by(Task.assigned_at.desc()).all()
    
    # Get current month/year for monthly targets
    from models import MonthlyTarget
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    # Calculate monthly progress for each agent
    monthly_stats = {}
    for agent in agents:
        # Get target for current month
        target = MonthlyTarget.query.filter_by(
            agent_id=agent.id, 
            year=current_year, 
            month=current_month
        ).first()
        
        # Calculate completed tasks cars this month
        completed_cars = db.session.query(db.func.sum(Task.car_count)).filter(
            Task.agent_id == agent.id,
            Task.completed == True,
            db.func.strftime('%Y', Task.completed_at) == str(current_year),
            db.func.strftime('%m', Task.completed_at) == str(current_month).zfill(2)
        ).scalar() or 0
        
        monthly_stats[agent.id] = {
            'target': target.target_cars if target else 0,
            'achieved': completed_cars,
            'percentage': (completed_cars / target.target_cars * 100) if (target and target.target_cars > 0) else 0
        }
    
    # Calculate agent statistics for agents
    agent_stats = {}
    if is_agent:
        # Total completed tasks
        total_completed = Task.query.filter_by(agent_id=current_user.id, completed=True).count()
        # Total cars wrapped
        total_cars = db.session.query(db.func.sum(Task.car_count)).filter(
            Task.agent_id == current_user.id,
            Task.completed == True
        ).scalar() or 0
        # Completed this month
        completed_this_month = Task.query.filter(
            Task.agent_id == current_user.id,
            Task.completed == True,
            db.func.strftime('%Y', Task.completed_at) == str(current_year),
            db.func.strftime('%m', Task.completed_at) == str(current_month).zfill(2)
        ).count()
        # Open tasks
        open_tasks = Task.query.filter_by(agent_id=current_user.id, completed=False).count()
        
        agent_stats = {
            'total_completed': total_completed,
            'total_cars': total_cars,
            'completed_this_month': completed_this_month,
            'open_tasks': open_tasks,
            'target': monthly_stats[current_user.id]['target'] if current_user.id in monthly_stats else 0,
            'achieved_cars': monthly_stats[current_user.id]['achieved'] if current_user.id in monthly_stats else 0,
            'percentage': monthly_stats[current_user.id]['percentage'] if current_user.id in monthly_stats else 0
        }
    
    return render_template('tasks.html', agents=agents, tasks=tasks_list, is_agent=is_agent, 
                         monthly_stats=monthly_stats, current_month=current_month, current_year=current_year, 
                         agent_stats=agent_stats, today=datetime.now().date())


@app.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    if isinstance(current_user, Agent):
        flash('غير مسموح للموظفين بتعديل المهام', 'danger')
        return redirect(url_for('tasks'))
    
    task = Task.query.get_or_404(task_id)
    
    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form.get('description')
        task.agent_id = request.form.get('agent_id')
        task.car_count = int(request.form.get('car_count', 0))
        task.agent_commission = float(request.form.get('agent_commission', 0))
        task.show_commission_in_invoice = request.form.get('show_commission_in_invoice') == 'on'
        due = request.form.get('due_date')
        task.due_date = datetime.strptime(due, '%Y-%m-%d').date() if due else None
        
        db.session.add(Log(action='edit_task', detail=f'Task {task.title} updated', created_by=current_user.id))
        db.session.commit()
        flash('Task updated successfully!', 'success')
        return redirect(url_for('tasks'))
    
    agents = Agent.query.all()
    return render_template('edit_task.html', task=task, agents=agents)


@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    if isinstance(current_user, Agent):
        flash('غير مسموح للموظفين بحذف المهام', 'danger')
        return redirect(url_for('tasks'))
    
    task = Task.query.get_or_404(task_id)
    title = task.title
    
    db.session.delete(task)
    db.session.add(Log(action='delete_task', detail=f'Task {title} deleted', created_by=current_user.id))
    db.session.commit()
    flash(f'Task "{title}" deleted successfully!', 'success')
    return redirect(url_for('tasks'))


@app.route('/tasks/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check permission: agent can only complete their own tasks
    if isinstance(current_user, Agent) and task.agent_id != current_user.id:
        flash('غير مسموح بإكمال هذه المهمة', 'danger')
        return redirect(url_for('tasks'))
    
    task.completed = True
    task.completed_at = datetime.utcnow()
    
    db.session.add(Log(action='complete_task', detail=f'Task {task.title} completed by {current_user.name if hasattr(current_user, "name") else "admin"}', created_by=current_user.id))
    db.session.commit()
    flash('تم إكمال المهمة بنجاح!', 'success')
    return redirect(url_for('tasks'))

@app.route('/tasks/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check permission: agent can only toggle their own tasks, admin can toggle any
    if isinstance(current_user, Agent) and task.agent_id != current_user.id:
        flash('غير مسموح بتعديل هذه المهمة', 'danger')
        return redirect(url_for('tasks'))
    
    # Toggle the status
    if task.completed:
        task.completed = False
        task.completed_at = None
        action = 'reopened'
        flash('تم إعادة فتح المهمة!', 'info')
    else:
        task.completed = True
        task.completed_at = datetime.utcnow()
        action = 'completed'
        flash('تم إكمال المهمة بنجاح!', 'success')
    
    db.session.add(Log(action=f'{action}_task', detail=f'Task {task.title} {action} by {current_user.name if hasattr(current_user, "name") else "admin"}', created_by=current_user.id))
    db.session.commit()
    return redirect(url_for('tasks'))


# Quick add completed task with car count
@app.route('/tasks/quick-add', methods=['POST'])
@login_required
def quick_add_task():
    """إضافة مهمة مكتملة بسرعة مع عدد السيارات"""
    is_agent = isinstance(current_user, Agent)
    
    if is_agent:
        flash('غير مسموح للموظفين بإضافة مهام', 'danger')
        return redirect(url_for('tasks'))
    
    agent_id = request.form.get('agent_id')
    car_count = int(request.form.get('car_count', 1))
    title = request.form.get('title', f'تغليف ({car_count} سيارة)')
    
    # Create completed task
    task = Task(
        title=title,
        agent_id=agent_id,
        car_count=car_count,
        completed=True,
        completed_at=datetime.utcnow()
    )
    
    db.session.add(task)
    db.session.add(Log(action='quick_add_task', detail=f'Quick task: {title} for agent {agent_id} with {car_count} cars', created_by=current_user.id))
    db.session.commit()
    
    flash(f'تمت إضافة المهمة: {car_count} سيارة مغلفة', 'success')
    return redirect(url_for('tasks'))


# Monthly targets management
@app.route('/monthly-targets', methods=['GET', 'POST'])
@login_required
def monthly_targets():
    """إدارة الأهداف الشهرية"""
    is_agent = isinstance(current_user, Agent)
    
    from models import MonthlyTarget
    
    # Agents can only view, not modify
    if request.method == 'POST':
        if is_agent:
            flash('غير مسموح للموظفين بتعديل الأهداف', 'danger')
            return redirect(url_for('monthly_targets'))
        agent_id = request.form.get('agent_id')
        year = int(request.form.get('year'))
        month = int(request.form.get('month'))
        target_cars = int(request.form.get('target_cars'))
        
        # Check if target already exists
        existing_target = MonthlyTarget.query.filter_by(
            agent_id=agent_id, year=year, month=month
        ).first()
        
        if existing_target:
            existing_target.target_cars = target_cars
            flash('تم تحديث الهدف الشهري', 'success')
        else:
            target = MonthlyTarget(
                agent_id=agent_id,
                year=year,
                month=month,
                target_cars=target_cars,
                created_by=current_user.id
            )
            db.session.add(target)
            flash('تم إضافة الهدف الشهري', 'success')
        
        db.session.commit()
        return redirect(url_for('monthly_targets'))
    
    agents = Agent.query.all()
    targets = MonthlyTarget.query.order_by(MonthlyTarget.year.desc(), MonthlyTarget.month.desc()).all()
    
    return render_template('monthly_targets.html', agents=agents, targets=targets, is_agent=is_agent)


@app.route('/monthly-targets/<int:target_id>/delete', methods=['POST'])
@login_required
def delete_monthly_target(target_id):
    """حذف هدف شهري"""
    is_agent = isinstance(current_user, Agent)
    
    if is_agent:
        flash('غير مسموح للموظفين بحذف الأهداف', 'danger')
        return redirect(url_for('tasks'))
    
    from models import MonthlyTarget
    target = MonthlyTarget.query.get_or_404(target_id)
    
    db.session.delete(target)
    db.session.commit()
    flash('تم حذف الهدف الشهري', 'success')
    return redirect(url_for('monthly_targets'))


# Purchases - Leader page
@app.route('/leader', methods=['GET', 'POST'])
@login_required
def leader():
    if request.method == 'POST':
        # إذا كان المستخدم موظف، استخدم ID الخاص به
        if isinstance(current_user, Agent):
            agent_id = current_user.id
        else:
            agent_id = request.form.get('agent_id')
        
        amount = float(request.form.get('amount') or 0)
        note = request.form.get('note')
        date = request.form.get('date')
        date_obj = datetime.strptime(date, '%Y-%m-%d').date() if date else datetime.utcnow().date()
        p = Purchase(agent_id=agent_id, amount=amount, note=note, date=date_obj)
        db.session.add(p)
        db.session.add(Log(action='add_purchase', detail=f'Purchase {amount} by agent {agent_id}', created_by=current_user.id))
        db.session.commit()
        return redirect(url_for('leader'))
    
    agents = Agent.query.all()
    
    # إذا كان الموظف، عرض مشترياته فقط
    is_agent = isinstance(current_user, Agent)
    current_agent_id = current_user.id if is_agent else None
    
    # Handle search & filter
    query = Purchase.query
    
    # إذا كان موظف، عرض مشترياته فقط
    if is_agent:
        query = query.filter(Purchase.agent_id == current_agent_id)
    
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    agent_filter = request.args.get('agent_id')
    
    if from_date:
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            query = query.filter(Purchase.date >= from_date_obj)
        except:
            pass
    
    if to_date:
        try:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            query = query.filter(Purchase.date <= to_date_obj)
        except:
            pass
    
    if agent_filter:
        query = query.filter(Purchase.agent_id == int(agent_filter))
    
    purchases = query.order_by(Purchase.date.desc()).limit(50).all()
    
    # Calculate total expenses for agent
    total_agent_expenses = 0
    if is_agent:
        total_agent_expenses = db.session.query(db.func.sum(Purchase.amount)).filter(
            Purchase.agent_id == current_agent_id
        ).scalar() or 0
    
    # Group purchases by month and agent
    from collections import defaultdict
    purchases_by_month = defaultdict(lambda: {'purchases': [], 'total': 0, 'by_agent': defaultdict(lambda: {'purchases': [], 'total': 0})})
    
    # Get all purchases for grouping (not limited)
    all_purchases_query = Purchase.query
    if is_agent:
        all_purchases_query = all_purchases_query.filter(Purchase.agent_id == current_agent_id)
    
    all_purchases = all_purchases_query.order_by(Purchase.date.desc()).all()
    
    for p in all_purchases:
        if p.date:
            month_key = p.date.strftime('%Y-%m')
            month_display = p.date.strftime('%B %Y')  # e.g., "January 2026"
            
            # Add to month total
            purchases_by_month[month_key]['month_display'] = month_display
            purchases_by_month[month_key]['month_key'] = month_key
            purchases_by_month[month_key]['purchases'].append(p)
            purchases_by_month[month_key]['total'] += p.amount
            
            # Add to agent total within month
            if p.agent_id:
                agent = Agent.query.get(p.agent_id)
                agent_name = agent.name if agent else 'N/A'
                purchases_by_month[month_key]['by_agent'][p.agent_id]['name'] = agent_name
                purchases_by_month[month_key]['by_agent'][p.agent_id]['purchases'].append(p)
                purchases_by_month[month_key]['by_agent'][p.agent_id]['total'] += p.amount
    
    # Convert to sorted list (newest first)
    purchases_by_month_list = []
    for month_key in sorted(purchases_by_month.keys(), reverse=True):
        month_data = purchases_by_month[month_key]
        # Convert by_agent defaultdict to regular dict
        month_data['by_agent'] = dict(month_data['by_agent'])
        purchases_by_month_list.append(month_data)
    
    # monthly totals for chart (kept for compatibility)
    try:
        with db.engine.connect() as conn:
            df = pd.read_sql(str(Purchase.query.statement.compile(compile_kwargs={"literal_binds": True})), conn)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df['month'] = df['date'].dt.to_period('M')
            monthly = df.groupby('month')['amount'].sum().reset_index()
            monthly['month'] = monthly['month'].astype(str)
            monthly = monthly.to_dict(orient='records')
        else:
            monthly = []
    except Exception as e:
        print(f"Error in leader monthly totals: {e}")
        monthly = []
    
    return render_template('leader.html', 
                          agents=agents, 
                          purchases=purchases, 
                          monthly=monthly, 
                          purchases_by_month=purchases_by_month_list,
                          is_agent=is_agent, 
                          current_agent_id=current_agent_id, 
                          total_agent_expenses=total_agent_expenses)


@app.route('/leader/download/<month>')
@login_required
def leader_download_month(month):
    """Download purchases for specific month as Excel"""
    try:
        # month format: '2025-01' or similar
        purchases = Purchase.query.all()
        data = []
        for p in purchases:
            if p.date and p.date.strftime('%Y-%m') == month:
                agent = Agent.query.get(p.agent_id) if p.agent_id else None
                data.append({
                    'Date': p.date.strftime('%Y-%m-%d'),
                    'Agent': agent.name if agent else 'N/A',
                    'Amount': p.amount,
                    'Note': p.note or ''
                })
        
        if not data:
            flash('No purchases found for this month')
            return redirect(url_for('leader'))
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=f'Purchases_{month}', index=False)
        output.seek(0)
        
        if isinstance(current_user, Admin):
            db.session.add(Log(action='download_purchases', detail=f'Downloaded purchases for {month}', created_by=current_user.id))
            db.session.commit()
        
        return send_file(output, download_name=f'purchases_{month}.xlsx', as_attachment=True)
    except Exception as e:
        flash(f'Error downloading: {e}')
        return redirect(url_for('leader'))


@app.route('/leader/<int:purchase_id>/delete', methods=['POST'])
@login_required
def delete_purchase(purchase_id):
    """Delete a purchase/expense record"""
    is_agent = isinstance(current_user, Agent)
    
    if is_agent:
        flash('غير مسموح للموظفين بحذف المصروفات', 'danger')
        return redirect(url_for('leader'))
    
    purchase = Purchase.query.get_or_404(purchase_id)
    amount = purchase.amount
    note = purchase.note
    
    db.session.delete(purchase)
    db.session.add(Log(action='delete_purchase', detail=f'Purchase {amount} deleted: {note}', created_by=current_user.id))
    db.session.commit()
    
    flash(f'تم حذف المصروف بنجاح ({amount} درهم)', 'success')
    return redirect(url_for('leader'))


@app.route('/leader/<int:purchase_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_purchase(purchase_id):
    """Edit a purchase/expense record"""
    is_agent = isinstance(current_user, Agent)
    
    if is_agent:
        flash('غير مسموح للموظفين بتعديل المصروفات', 'danger')
        return redirect(url_for('leader'))
    
    purchase = Purchase.query.get_or_404(purchase_id)
    
    if request.method == 'POST':
        purchase.agent_id = request.form.get('agent_id')
        purchase.amount = float(request.form.get('amount', 0))
        purchase.note = request.form.get('note')
        date_str = request.form.get('date')
        if date_str:
            purchase.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        db.session.add(Log(action='edit_purchase', detail=f'Purchase {purchase.id} updated', created_by=current_user.id))
        db.session.commit()
        
        flash('تم تحديث المصروف بنجاح', 'success')
        return redirect(url_for('leader'))
    
    agents = Agent.query.all()
    return render_template('edit_purchase.html', purchase=purchase, agents=agents)


# Income page
@app.route('/income', methods=['GET','POST'])
@login_required
def income():
    if request.method == 'POST':
        # إذا كان المستخدم موظف، استخدم ID الخاص به
        if isinstance(current_user, Agent):
            agent_id = current_user.id
        else:
            agent_id = request.form.get('agent_id')
        
        amount = float(request.form.get('amount') or 0)
        discount = float(request.form.get('discount') or 0)
        discount_description = request.form.get('discount_description', '').strip()
        source = request.form.get('source')
        customer_name = request.form.get('customer_name')
        service_type = request.form.get('service_type')
        car_type = request.form.get('car_type')
        note = request.form.get('note')
        date = request.form.get('date')
        date_obj = datetime.strptime(date, '%Y-%m-%d').date() if date else datetime.utcnow().date()
        
        # Generate invoice number
        from datetime import datetime as dt
        invoice_number = f"INV-{dt.now().strftime('%Y%m%d%H%M%S')}-{agent_id}"
        
        inc = Income(
            agent_id=agent_id, 
            amount=amount,
            discount=discount,
            discount_description=discount_description,
            source=source, 
            customer_name=customer_name,
            service_type=service_type,
            car_type=car_type,
            note=note, 
            date=date_obj,
            invoice_number=invoice_number
        )
        db.session.add(inc)
        
        # Add service type to list if new
        if service_type and service_type.strip():
            existing = ServiceType.query.filter_by(name=service_type.strip()).first()
            if not existing:
                new_service = ServiceType(name=service_type.strip())
                db.session.add(new_service)
        
        # Add car type to list if new
        if car_type and car_type.strip():
            existing_car = CarType.query.filter_by(name=car_type.strip()).first()
            if not existing_car:
                new_car = CarType(name=car_type.strip())
                db.session.add(new_car)
        
        # Create task for this income (car wrapping)
        final_amount = amount - discount
        task_title = f"تغليف: {service_type or 'N/A'} - {customer_name or 'N/A'}"
        task_desc = f"نوع السيارة: {car_type}\nالمبلغ الأصلي: {amount} MAD\nالخصم: {discount} MAD\nالمبلغ النهائي: {final_amount} MAD\nالمصدر: {source}\nرقم الفاتورة: {invoice_number}"
        task = Task(
            title=task_title,
            description=task_desc,
            agent_id=agent_id,
            due_date=date_obj,
            income_id=None  # Will be updated after commit
        )
        db.session.add(task)
        db.session.flush()  # Get inc.id
        task.income_id = inc.id
        
        db.session.add(Log(action='add_income', detail=f'Income {amount} from {customer_name} - {service_type} - {car_type}', created_by=current_user.id))
        db.session.commit()
        
        flash(f'تمت إضافة الخدمة بنجاح! ✅ رقم الفاتورة: {invoice_number}', 'success')
        return redirect(url_for('income'))
    
    agents = Agent.query.all()
    service_types = ServiceType.query.order_by(ServiceType.name).all()
    car_types = CarType.query.order_by(CarType.name).all()
    
    # إذا كان الموظف، عرض مداخيله فقط
    is_agent = isinstance(current_user, Agent)
    current_agent_id = current_user.id if is_agent else None
    
    # Handle search & filter
    query = Income.query
    
    # إذا كان موظف، عرض مداخيله فقط
    if is_agent:
        query = query.filter(Income.agent_id == current_agent_id)
    
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    source_filter = request.args.get('source')
    agent_filter = request.args.get('agent_id')
    
    if from_date:
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            query = query.filter(Income.date >= from_date_obj)
        except:
            pass
    
    if to_date:
        try:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            query = query.filter(Income.date <= to_date_obj)
        except:
            pass
    
    if source_filter:
        query = query.filter(Income.source.ilike(f'%{source_filter}%'))
    
    if agent_filter and not is_agent:
        query = query.filter(Income.agent_id == int(agent_filter))
    
    incomes = query.order_by(Income.date.desc()).limit(50).all()
    
    # Monthly totals - filter by agent if needed
    if is_agent:
        monthly_query = Income.query.filter_by(agent_id=current_agent_id)
    else:
        monthly_query = Income.query
    
    try:
        with db.engine.connect() as conn:
            df = pd.read_sql(str(monthly_query.statement.compile(compile_kwargs={"literal_binds": True})), conn)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df['month'] = df['date'].dt.to_period('M')
            # Calculate final amount (amount - discount)
            df['discount'] = df['discount'].fillna(0)
            df['final_amount'] = df['amount'] - df['discount']
            monthly = df.groupby('month')['final_amount'].sum().reset_index()
            monthly.columns = ['month', 'amount']
            monthly['month'] = monthly['month'].astype(str)
            monthly = monthly.to_dict(orient='records')
        else:
            monthly = []
    except Exception as e:
        print(f"Error in income monthly totals: {e}")
        monthly = []
    return render_template('income.html', incomes=incomes, monthly=monthly, agents=agents, service_types=service_types, car_types=car_types, is_agent=is_agent, current_agent_id=current_agent_id)


@app.route('/income/<int:income_id>/invoice')
@login_required
def generate_invoice(income_id):
    income = Income.query.get_or_404(income_id)
    agent = Agent.query.get(income.agent_id)
    
    # Check permission
    if isinstance(current_user, Agent) and current_user.id != income.agent_id:
        flash('غير مسموح بالوصول لهذه الفاتورة', 'danger')
        return redirect(url_for('income'))
    
    return render_template('invoice.html', income=income, agent=agent)

@app.route('/income/<int:income_id>/delete', methods=['POST'])
@login_required
def delete_income(income_id):
    # Only admin can delete income
    if isinstance(current_user, Agent):
        flash('غير مسموح لك بحذف المداخيل', 'danger')
        return redirect(url_for('income'))
    
    income = Income.query.get_or_404(income_id)
    
    # Delete related task if exists
    task = Task.query.filter_by(income_id=income_id).first()
    if task:
        db.session.delete(task)
    
    db.session.add(Log(action='delete_income', detail=f'Deleted income {income.invoice_number} - Amount: {income.amount} MAD (Discount: {income.discount or 0}) = Final: {income.amount - (income.discount or 0)} MAD', created_by=current_user.id))
    db.session.delete(income)
    db.session.commit()
    flash('تم حذف المدخول بنجاح!', 'success')
    return redirect(url_for('income'))

@app.route('/income/<int:income_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_income(income_id):
    # Only admin can edit income
    if isinstance(current_user, Agent):
        flash('غير مسموح لك بتعديل المداخيل', 'danger')
        return redirect(url_for('income'))
    
    income = Income.query.get_or_404(income_id)
    agents = Agent.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        income.agent_id = int(request.form.get('agent_id'))
        income.amount = float(request.form.get('amount'))
        income.discount = float(request.form.get('discount', 0))
        income.discount_description = request.form.get('discount_description', '').strip()
        income.source = request.form.get('source')
        income.customer_name = request.form.get('customer_name')
        income.service_type = request.form.get('service_type')
        income.car_type = request.form.get('car_type')
        income.note = request.form.get('note', '')
        
        date_str = request.form.get('date')
        if date_str:
            income.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Update related task if exists
        task = Task.query.filter_by(income_id=income_id).first()
        if task:
            final_amount = income.amount - income.discount
            task.title = f"خدمة {income.service_type or 'N/A'} - {income.customer_name or 'N/A'}"
            task.description = f"نوع السيارة: {income.car_type}\nالمبلغ الأصلي: {income.amount} MAD\nالخصم: {income.discount} MAD\nالمبلغ النهائي: {final_amount} MAD\nالمصدر: {income.source}\nرقم الفاتورة: {income.invoice_number}"
            task.agent_id = income.agent_id
            task.due_date = income.date
        
        db.session.add(Log(action='edit_income', detail=f'Edited income {income.invoice_number}: {income.amount} - {income.discount} = {income.amount - income.discount}', created_by=current_user.id))
        db.session.commit()
        flash('تم تحديث المدخول بنجاح!', 'success')
        return redirect(url_for('income'))
    
    service_types = ServiceType.query.all()
    car_types = CarType.query.all()
    return render_template('edit_income.html', income=income, agents=agents, service_types=service_types, car_types=car_types)


@app.route('/income/download/<month>')
@login_required
def income_download_month(month):
    """Download income for specific month as Excel"""
    try:
        # month format: '2025-01' or similar
        incomes = Income.query.all()
        data = []
        for i in incomes:
            if i.date and i.date.strftime('%Y-%m') == month:
                final_amount = i.amount - (i.discount or 0)
                data.append({
                    'Date': i.date.strftime('%Y-%m-%d'),
                    'Customer': i.customer_name or '',
                    'Service': i.service_type or '',
                    'Car Type': i.car_type or '',
                    'Original Amount': i.amount,
                    'Discount': i.discount or 0,
                    'Final Amount': final_amount,
                    'Source': i.source or '',
                    'Invoice': i.invoice_number or '',
                    'Note': i.note or ''
                })
        
        if not data:
            flash('No income found for this month')
            return redirect(url_for('income'))
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=f'Income_{month}', index=False)
        output.seek(0)
        
        if isinstance(current_user, Admin):
            db.session.add(Log(action='download_income', detail=f'Downloaded income for {month}', created_by=current_user.id))
            db.session.commit()
        
        return send_file(output, download_name=f'income_{month}.xlsx', as_attachment=True)
    except Exception as e:
        flash(f'Error downloading: {e}')
        return redirect(url_for('income'))


# Logs admin
@app.route('/logs', methods=['GET','POST'])
@login_required
def logs():
    if request.method == 'POST':
        action = request.form.get('action')
        detail = request.form.get('detail')
        l = Log(action=action, detail=detail, created_by=current_user.id)
        db.session.add(l)
        db.session.commit()
        return redirect(url_for('logs'))
    logs = Log.query.order_by(Log.created_at.desc()).all()
    return render_template('logs.html', logs=logs)


@app.route('/logs/<int:log_id>/delete', methods=['POST'])
@login_required
def log_delete(log_id):
    l = Log.query.get_or_404(log_id)
    db.session.delete(l)
    db.session.commit()
    return redirect(url_for('logs'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Application settings and backup"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'backup':
            # Create comprehensive backup with all data
            import shutil
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            backup_path = os.path.join(backup_dir, backup_name)
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            
            # Copy database file
            shutil.copy(db_path, backup_path)
            
            # Verify backup contains all data
            import sqlite3
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            
            # Check all tables exist and count records
            tables_info = {}
            for table in ['agent', 'task', 'purchase', 'income', 'admin', 'file_upload', 'log', 'api_token', 'service_type', 'car_type']:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    tables_info[table] = count
                except:
                    tables_info[table] = 0
            
            conn.close()
            
            # Create backup info file
            info_path = os.path.join(backup_dir, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_info.txt")
            with open(info_path, 'w', encoding='utf-8') as f:
                f.write(f"النسخة الاحتياطية: {backup_name}\n")
                f.write(f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"حجم الملف: {os.path.getsize(backup_path) / 1024 / 1024:.2f} MB\n\n")
                f.write("محتويات النسخة الاحتياطية:\n")
                f.write(f"  - الموظفين (agent): {tables_info.get('agent', 0)} سجل\n")
                f.write(f"  - المهام (task): {tables_info.get('task', 0)} سجل\n")
                f.write(f"  - المشتريات (purchase): {tables_info.get('purchase', 0)} سجل\n")
                f.write(f"  - المداخيل (income): {tables_info.get('income', 0)} سجل\n")
                f.write(f"  - المسؤولين (admin): {tables_info.get('admin', 0)} سجل\n")
                f.write(f"  - الملفات (file_upload): {tables_info.get('file_upload', 0)} سجل\n")
                f.write(f"  - السجلات (log): {tables_info.get('log', 0)} سجل\n")
                f.write(f"  - API Tokens: {tables_info.get('api_token', 0)} سجل\n")
                f.write(f"  - أنواع الخدمات (service_type): {tables_info.get('service_type', 0)} سجل\n")
                f.write(f"  - أنواع السيارات (car_type): {tables_info.get('car_type', 0)} سجل\n")
            
            if isinstance(current_user, Admin):
                detail = f'Created backup: {backup_name} | Agents: {tables_info.get("agent", 0)}, Tasks: {tables_info.get("task", 0)}, Purchases: {tables_info.get("purchase", 0)}, Income: {tables_info.get("income", 0)}'
                db.session.add(Log(action='backup_database', detail=detail, created_by=current_user.id))
                db.session.commit()
            
            flash(f'✅ تم إنشاء النسخة الاحتياطية: {backup_name}')
            flash(f'📊 المحتويات: {tables_info.get("agent", 0)} موظف | {tables_info.get("task", 0)} مهمة | {tables_info.get("purchase", 0)} مشترى | {tables_info.get("income", 0)} مدخول')
            return send_file(backup_path, download_name=backup_name, as_attachment=True)
        
        elif action == 'backup_full':
            # Create full backup including database and uploads folder
            import shutil
            import tempfile
            
            backup_name = f"full_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Create temporary directory for full backup
            temp_dir = tempfile.mkdtemp()
            temp_backup_dir = os.path.join(temp_dir, backup_name)
            os.makedirs(temp_backup_dir)
            
            try:
                # Copy database
                db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
                shutil.copy(db_path, os.path.join(temp_backup_dir, 'database.db'))
                
                # Copy uploads folder if exists
                uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
                if os.path.exists(uploads_dir):
                    shutil.copytree(uploads_dir, os.path.join(temp_backup_dir, 'uploads'))
                
                # Create info file
                info_path = os.path.join(temp_backup_dir, 'backup_info.txt')
                with open(info_path, 'w', encoding='utf-8') as f:
                    f.write(f"نسخة احتياطية شاملة\n")
                    f.write(f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(f"المحتويات:\n")
                    f.write(f"  - قاعدة البيانات: database.db\n")
                    f.write(f"  - مجلد الملفات المرفوعة: uploads/\n\n")
                    f.write(f"البيانات:\n")
                    f.write(f"  - الموظفين: {Agent.query.count()}\n")
                    f.write(f"  - المهام: {Task.query.count()}\n")
                    f.write(f"  - المشتريات: {Purchase.query.count()}\n")
                    f.write(f"  - المداخيل: {Income.query.count()}\n")
                    f.write(f"  - الملفات المرفوعة: {FileUpload.query.count()}\n")
                
                # Create zip file
                zip_path = os.path.join(backup_dir, f"{backup_name}.zip")
                shutil.make_archive(os.path.join(backup_dir, backup_name), 'zip', temp_dir)
                
                # Cleanup
                shutil.rmtree(temp_dir)
                
                if isinstance(current_user, Admin):
                    db.session.add(Log(action='full_backup', detail=f'Created full backup: {backup_name}.zip', created_by=current_user.id))
                    db.session.commit()
                
                flash(f'✅ تم إنشاء النسخة الاحتياطية الشاملة: {backup_name}.zip')
                flash(f'📁 تحتوي على: قاعدة البيانات + جميع الملفات المرفوعة')
                return send_file(zip_path, download_name=f"{backup_name}.zip", as_attachment=True)
            
            except Exception as e:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                flash(f'❌ خطأ في إنشاء النسخة الاحتياطية الشاملة: {str(e)}')
                return redirect(url_for('settings'))
        
        elif action == 'restore':
            # Restore database from uploaded backup
            if 'backup_file' not in request.files:
                flash('❌ لم يتم اختيار ملف')
                return redirect(url_for('settings'))
            
            file = request.files['backup_file']
            if file.filename == '':
                flash('❌ لم يتم اختيار ملف')
                return redirect(url_for('settings'))
            
            if not (file.filename.endswith('.db') or file.filename.endswith('.zip')):
                flash('❌ يجب أن يكون الملف بصيغة .db أو .zip')
                return redirect(url_for('settings'))
            
            try:
                import shutil
                import sqlite3
                
                # Backup current database before restoring
                backup_name = f"backup_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                backup_path = os.path.join(backup_dir, backup_name)
                db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
                shutil.copy(db_path, backup_path)
                
                if file.filename.endswith('.zip'):
                    # Full backup restore
                    import zipfile
                    import tempfile
                    
                    temp_dir = tempfile.mkdtemp()
                    zip_path = os.path.join(temp_dir, 'backup.zip')
                    file.save(zip_path)
                    
                    # Extract zip
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    # Find database file
                    db_file = None
                    for root, dirs, files in os.walk(temp_dir):
                        for f in files:
                            if f == 'database.db' or f.endswith('.db'):
                                db_file = os.path.join(root, f)
                                break
                        if db_file:
                            break
                    
                    if not db_file:
                        shutil.rmtree(temp_dir)
                        flash('❌ لم يتم العثور على قاعدة البيانات في الملف المضغوط')
                        return redirect(url_for('settings'))
                    
                    # Verify database integrity
                    try:
                        conn = sqlite3.connect(db_file)
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM agent")
                        agents_count = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM task")
                        tasks_count = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM purchase")
                        purchases_count = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM income")
                        income_count = cursor.fetchone()[0]
                        conn.close()
                    except Exception as e:
                        shutil.rmtree(temp_dir)
                        flash(f'❌ قاعدة البيانات تالفة: {str(e)}')
                        return redirect(url_for('settings'))
                    
                    # Close database connections
                    db.session.close()
                    db.engine.dispose()
                    
                    # Replace database
                    shutil.copy(db_file, db_path)
                    
                    # Restore uploads folder if exists
                    uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
                    for root, dirs, files in os.walk(temp_dir):
                        if 'uploads' in dirs:
                            backup_uploads = os.path.join(root, 'uploads')
                            if os.path.exists(uploads_dir):
                                shutil.rmtree(uploads_dir)
                            shutil.copytree(backup_uploads, uploads_dir)
                            break
                    
                    shutil.rmtree(temp_dir)
                    
                    flash(f'✅ تم استعادة النسخة الاحتياطية الشاملة')
                    flash(f'📊 تمت استعادة: {agents_count} موظف | {tasks_count} مهمة | {purchases_count} مشترى | {income_count} مدخول')
                    flash(f'💾 تم حفظ نسخة احتياطية من البيانات الحالية: {backup_name}')
                
                else:
                    # Database only restore
                    temp_path = os.path.join(os.path.dirname(__file__), 'temp_restore.db')
                    file.save(temp_path)
                    
                    # Verify database integrity
                    try:
                        import sqlite3
                        conn = sqlite3.connect(temp_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM agent")
                        agents_count = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM task")
                        tasks_count = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM purchase")
                        purchases_count = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM income")
                        income_count = cursor.fetchone()[0]
                        conn.close()
                    except Exception as e:
                        os.remove(temp_path)
                        flash(f'❌ قاعدة البيانات تالفة أو غير متوافقة: {str(e)}')
                        return redirect(url_for('settings'))
                    
                    # Close database connections
                    db.session.close()
                    db.engine.dispose()
                    
                    # Replace database with restored file
                    shutil.copy(temp_path, db_path)
                    os.remove(temp_path)
                    
                    flash(f'✅ تم استعادة قاعدة البيانات من: {file.filename}')
                    flash(f'📊 تمت استعادة: {agents_count} موظف | {tasks_count} مهمة | {purchases_count} مشترى | {income_count} مدخول')
                    flash(f'💾 تم حفظ نسخة احتياطية من قاعدة البيانات الحالية: {backup_name}')
                
                if isinstance(current_user, Admin):
                    db.session.add(Log(action='restore_database', detail=f'Restored from: {file.filename}', created_by=current_user.id))
                    db.session.commit()
                
                return redirect(url_for('admin_dashboard'))
            
            except Exception as e:
                flash(f'❌ خطأ في استعادة قاعدة البيانات: {str(e)}')
                return redirect(url_for('settings'))
        
        elif action == 'export_excel':
            # Export all data to Excel
            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Export Agents
                    agents = Agent.query.all()
                    agents_df = pd.DataFrame([{
                        'ID': a.id,
                        'الاسم': a.name,
                        'الهاتف': a.phone,
                        'البريد الإلكتروني': a.email,
                        'تاريخ الإنشاء': a.created_at
                    } for a in agents])
                    agents_df.to_excel(writer, sheet_name='الموظفين', index=False)
                    
                    # Export Tasks
                    tasks = Task.query.all()
                    tasks_df = pd.DataFrame([{
                        'ID': t.id,
                        'العنوان': t.title,
                        'الوصف': t.description,
                        'الموظف': t.agent.name if t.agent else '',
                        'السعر': t.price,
                        'عمولة الموظف': t.agent_commission,
                        'الحالة': t.status,
                        'تاريخ الإنشاء': t.created_at,
                        'تاريخ الإكمال': t.completed_at
                    } for t in tasks])
                    tasks_df.to_excel(writer, sheet_name='المهام', index=False)
                    
                    # Export Purchases
                    purchases = Purchase.query.all()
                    purchases_df = pd.DataFrame([{
                        'ID': p.id,
                        'الوصف': p.description,
                        'المبلغ': p.amount,
                        'الموظف': p.agent.name if p.agent else '',
                        'التاريخ': p.created_at
                    } for p in purchases])
                    purchases_df.to_excel(writer, sheet_name='المشتريات', index=False)
                    
                    # Export Income
                    incomes = Income.query.all()
                    incomes_df = pd.DataFrame([{
                        'ID': i.id,
                        'الوصف': i.description,
                        'المبلغ': i.amount,
                        'الخصم': i.discount,
                        'وصف الخصم': i.discount_description,
                        'الموظف': i.agent.name if i.agent else '',
                        'التاريخ': i.created_at
                    } for i in incomes])
                    incomes_df.to_excel(writer, sheet_name='المداخيل', index=False)
                
                output.seek(0)
                excel_name = f"full_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
                if isinstance(current_user, Admin):
                    db.session.add(Log(action='export_excel', detail=f'Exported all data to Excel: {excel_name}', created_by=current_user.id))
                    db.session.commit()
                
                return send_file(output, download_name=excel_name, as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            
            except Exception as e:
                flash(f'❌ خطأ في تصدير Excel: {str(e)}')
                return redirect(url_for('settings'))
    
    # Get database size
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    db_size = os.path.getsize(db_path) / 1024 / 1024  # MB
    
    # Get counts
    counts = {
        'agents': Agent.query.count(),
        'purchases': Purchase.query.count(),
        'income': Income.query.count(),
        'tasks': Task.query.count(),
        'logs': Log.query.count(),
        'files': FileUpload.query.count()
    }
    
    # Get list of existing backups
    backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
    backups = []
    if os.path.exists(backup_dir):
        for filename in sorted(os.listdir(backup_dir), reverse=True):
            if filename.endswith('.db') or filename.endswith('.zip'):
                file_path = os.path.join(backup_dir, filename)
                file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # Get backup details if it's a database file
                backup_info = {}
                if filename.endswith('.db'):
                    try:
                        import sqlite3
                        conn = sqlite3.connect(file_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM agent")
                        backup_info['agents'] = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM task")
                        backup_info['tasks'] = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM purchase")
                        backup_info['purchases'] = cursor.fetchone()[0]
                        cursor.execute("SELECT COUNT(*) FROM income")
                        backup_info['income'] = cursor.fetchone()[0]
                        conn.close()
                    except:
                        backup_info = None
                
                backups.append({
                    'filename': filename,
                    'size': file_size,
                    'date': file_time,
                    'info': backup_info,
                    'type': 'شامل (قاعدة بيانات + ملفات)' if filename.endswith('.zip') else 'قاعدة بيانات فقط'
                })
    
    return render_template('settings.html', db_size=db_size, counts=counts, backups=backups)


@app.route('/change_password', methods=['GET','POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current = request.form.get('current')
        new = request.form.get('new')
        confirm = request.form.get('confirm')
        if not check_password_hash(current_user.password_hash, current):
            flash('Current password incorrect')
            return redirect(url_for('change_password'))
        if new != confirm:
            flash('New passwords do not match')
            return redirect(url_for('change_password'))
        current_user.password_hash = generate_password_hash(new)
        db.session.commit()
        db.session.add(Log(action='change_password', detail=f'Password changed for admin {current_user.username}', created_by=current_user.id))
        db.session.commit()
        flash('Password changed')
        return redirect(url_for('admin_dashboard'))
    return render_template('change_password.html')


@app.route('/api_tokens', methods=['GET','POST'])
@login_required
def api_tokens():
    tokens = APIToken.query.order_by(APIToken.created_at.desc()).all()
    show = None
    if request.method == 'POST':
        name = request.form.get('name') or 'token'
        tval = secrets.token_hex(24)
        token = APIToken(name=name, token=tval, created_by=current_user.id)
        db.session.add(token)
        db.session.commit()
        # show the newly created token one time
        tokens = APIToken.query.order_by(APIToken.created_at.desc()).all()
        # mark show_token only for newest
        out = []
        for t in tokens:
            d = {'id':t.id,'name':t.name,'token':t.token if t.id==token.id else '','created_at':t.created_at,'revoked':t.revoked,'show_token': t.id==token.id}
            out.append(d)
        return render_template('api_tokens.html', tokens=out)
    # GET
    out = []
    for t in tokens:
        out.append({'id':t.id,'name':t.name,'token':'','created_at':t.created_at,'revoked':t.revoked,'show_token':False})
    return render_template('api_tokens.html', tokens=out)


@app.route('/api_tokens/<int:token_id>/revoke', methods=['POST'])
@login_required
def api_token_revoke(token_id):
    t = APIToken.query.get_or_404(token_id)
    t.revoked = True
    db.session.commit()
    db.session.add(Log(action='revoke_token', detail=f'Revoked token {t.id}', created_by=current_user.id))
    db.session.commit()
    return redirect(url_for('api_tokens'))

# --- Comprehensive JSON API endpoints ---

# API Token authentication decorator
def require_api_token(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        api_token = APIToken.query.filter_by(token=token, revoked=False).first()
        if not api_token:
            return jsonify({'error': 'Invalid or revoked token'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


# API: Get application info and version
@app.route('/api/info', methods=['GET'])
@require_api_token
def api_info():
    """Get application information and statistics"""
    return jsonify({
        'app_name': 'Auto Protect Database',
        'version': app.config.get('VERSION', '1.0'),
        'database': {
            'agents': Agent.query.count(),
            'tasks': Task.query.count(),
            'purchases': Purchase.query.count(),
            'income': Income.query.count(),
            'files': FileUpload.query.count()
        },
        'timestamp': datetime.now().isoformat()
    })


# API: Agents CRUD
@app.route('/api/agents', methods=['GET', 'POST'])
@require_api_token
def api_agents():
    """List all agents or create new agent"""
    if request.method == 'GET':
        agents = Agent.query.all()
        return jsonify({
            'count': len(agents),
            'agents': [{
                'id': a.id,
                'name': a.name,
                'phone': a.phone,
                'email': a.email,
                'created_at': a.created_at.isoformat() if a.created_at else None
            } for a in agents]
        })
    
    data = request.get_json() or {}
    name = data.get('name')
    if not name:
        return jsonify({'error': 'name required'}), 400
    
    agent = Agent(
        name=name,
        phone=data.get('phone'),
        email=data.get('email')
    )
    db.session.add(agent)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'agent': {
            'id': agent.id,
            'name': agent.name,
            'phone': agent.phone,
            'email': agent.email
        }
    }), 201


@app.route('/api/agents/<int:agent_id>', methods=['GET', 'PUT', 'DELETE'])
@require_api_token
def api_agent_detail(agent_id):
    """Get, update or delete specific agent"""
    agent = Agent.query.get_or_404(agent_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': agent.id,
            'name': agent.name,
            'phone': agent.phone,
            'email': agent.email,
            'created_at': agent.created_at.isoformat() if agent.created_at else None,
            'tasks_count': Task.query.filter_by(agent_id=agent_id).count(),
            'purchases_count': Purchase.query.filter_by(agent_id=agent_id).count(),
            'income_count': Income.query.filter_by(agent_id=agent_id).count()
        })
    
    if request.method == 'PUT':
        data = request.get_json() or {}
        if 'name' in data:
            agent.name = data['name']
        if 'phone' in data:
            agent.phone = data['phone']
        if 'email' in data:
            agent.email = data['email']
        db.session.commit()
        return jsonify({'success': True, 'agent': {'id': agent.id, 'name': agent.name}})
    
    if request.method == 'DELETE':
        db.session.delete(agent)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Agent deleted'})


# API: Tasks CRUD
@app.route('/api/tasks', methods=['GET', 'POST'])
@require_api_token
def api_tasks():
    """List all tasks or create new task"""
    if request.method == 'GET':
        status = request.args.get('status')
        agent_id = request.args.get('agent_id')
        
        query = Task.query
        if status:
            query = query.filter_by(status=status)
        if agent_id:
            query = query.filter_by(agent_id=int(agent_id))
        
        tasks = query.all()
        return jsonify({
            'count': len(tasks),
            'tasks': [{
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'status': t.status,
                'price': float(t.price) if t.price else 0,
                'agent_commission': float(t.agent_commission) if t.agent_commission else 0,
                'agent': {'id': t.agent.id, 'name': t.agent.name} if t.agent else None,
                'created_at': t.created_at.isoformat() if t.created_at else None,
                'completed_at': t.completed_at.isoformat() if t.completed_at else None,
                'due_date': t.due_date.isoformat() if t.due_date else None
            } for t in tasks]
        })
    
    data = request.get_json() or {}
    if not data.get('title'):
        return jsonify({'error': 'title required'}), 400
    
    task = Task(
        title=data['title'],
        description=data.get('description'),
        agent_id=data.get('agent_id'),
        price=data.get('price', 0),
        agent_commission=data.get('agent_commission', 0),
        status=data.get('status', 'pending')
    )
    db.session.add(task)
    db.session.commit()
    
    return jsonify({'success': True, 'task': {'id': task.id, 'title': task.title}}), 201


@app.route('/api/tasks/<int:task_id>', methods=['GET', 'PUT', 'DELETE'])
@require_api_token
def api_task_detail(task_id):
    """Get, update or delete specific task"""
    task = Task.query.get_or_404(task_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'price': float(task.price) if task.price else 0,
            'agent_commission': float(task.agent_commission) if task.agent_commission else 0,
            'show_commission_in_invoice': task.show_commission_in_invoice,
            'agent': {'id': task.agent.id, 'name': task.agent.name} if task.agent else None,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None
        })
    
    if request.method == 'PUT':
        data = request.get_json() or {}
        if 'title' in data:
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            task.status = data['status']
        if 'price' in data:
            task.price = data['price']
        if 'agent_commission' in data:
            task.agent_commission = data['agent_commission']
        if 'agent_id' in data:
            task.agent_id = data['agent_id']
        db.session.commit()
        return jsonify({'success': True, 'task': {'id': task.id, 'title': task.title}})
    
    if request.method == 'DELETE':
        db.session.delete(task)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Task deleted'})


# API: Purchases CRUD
@app.route('/api/purchases', methods=['GET', 'POST'])
@require_api_token
def api_purchases():
    """List all purchases or create new purchase"""
    if request.method == 'GET':
        agent_id = request.args.get('agent_id')
        month = request.args.get('month')
        year = request.args.get('year')
        
        query = Purchase.query
        if agent_id:
            query = query.filter_by(agent_id=int(agent_id))
        if month and year:
            query = query.filter(
                db.func.strftime('%m', Purchase.created_at) == month,
                db.func.strftime('%Y', Purchase.created_at) == year
            )
        
        purchases = query.order_by(Purchase.created_at.desc()).all()
        return jsonify({
            'count': len(purchases),
            'total_amount': sum(float(p.amount) for p in purchases),
            'purchases': [{
                'id': p.id,
                'description': p.description,
                'amount': float(p.amount),
                'agent': {'id': p.agent.id, 'name': p.agent.name} if p.agent else None,
                'created_at': p.created_at.isoformat() if p.created_at else None
            } for p in purchases]
        })
    
    data = request.get_json() or {}
    if not data.get('description') or not data.get('amount'):
        return jsonify({'error': 'description and amount required'}), 400
    
    purchase = Purchase(
        description=data['description'],
        amount=data['amount'],
        agent_id=data.get('agent_id')
    )
    db.session.add(purchase)
    db.session.commit()
    
    return jsonify({'success': True, 'purchase': {'id': purchase.id, 'amount': float(purchase.amount)}}), 201


@app.route('/api/purchases/<int:purchase_id>', methods=['GET', 'PUT', 'DELETE'])
@require_api_token
def api_purchase_detail(purchase_id):
    """Get, update or delete specific purchase"""
    purchase = Purchase.query.get_or_404(purchase_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': purchase.id,
            'description': purchase.description,
            'amount': float(purchase.amount),
            'agent': {'id': purchase.agent.id, 'name': purchase.agent.name} if purchase.agent else None,
            'created_at': purchase.created_at.isoformat() if purchase.created_at else None
        })
    
    if request.method == 'PUT':
        data = request.get_json() or {}
        if 'description' in data:
            purchase.description = data['description']
        if 'amount' in data:
            purchase.amount = data['amount']
        if 'agent_id' in data:
            purchase.agent_id = data['agent_id']
        db.session.commit()
        return jsonify({'success': True, 'purchase': {'id': purchase.id}})
    
    if request.method == 'DELETE':
        db.session.delete(purchase)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Purchase deleted'})


# API: Income CRUD
@app.route('/api/income', methods=['GET', 'POST'])
@require_api_token
def api_income():
    """List all income or create new income"""
    if request.method == 'GET':
        agent_id = request.args.get('agent_id')
        month = request.args.get('month')
        year = request.args.get('year')
        
        query = Income.query
        if agent_id:
            query = query.filter_by(agent_id=int(agent_id))
        if month and year:
            query = query.filter(
                db.func.strftime('%m', Income.created_at) == month,
                db.func.strftime('%Y', Income.created_at) == year
            )
        
        incomes = query.order_by(Income.created_at.desc()).all()
        total = sum(float(i.amount) - float(i.discount or 0) for i in incomes)
        
        return jsonify({
            'count': len(incomes),
            'total_amount': total,
            'income': [{
                'id': i.id,
                'description': i.description,
                'amount': float(i.amount),
                'discount': float(i.discount) if i.discount else 0,
                'discount_description': i.discount_description,
                'final_amount': float(i.amount) - float(i.discount or 0),
                'agent': {'id': i.agent.id, 'name': i.agent.name} if i.agent else None,
                'created_at': i.created_at.isoformat() if i.created_at else None
            } for i in incomes]
        })
    
    data = request.get_json() or {}
    if not data.get('description') or not data.get('amount'):
        return jsonify({'error': 'description and amount required'}), 400
    
    income = Income(
        description=data['description'],
        amount=data['amount'],
        discount=data.get('discount', 0),
        discount_description=data.get('discount_description'),
        agent_id=data.get('agent_id')
    )
    db.session.add(income)
    db.session.commit()
    
    return jsonify({'success': True, 'income': {'id': income.id, 'amount': float(income.amount)}}), 201


@app.route('/api/income/<int:income_id>', methods=['GET', 'PUT', 'DELETE'])
@require_api_token
def api_income_detail(income_id):
    """Get, update or delete specific income"""
    income = Income.query.get_or_404(income_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': income.id,
            'description': income.description,
            'amount': float(income.amount),
            'discount': float(income.discount) if income.discount else 0,
            'discount_description': income.discount_description,
            'final_amount': float(income.amount) - float(income.discount or 0),
            'agent': {'id': income.agent.id, 'name': income.agent.name} if income.agent else None,
            'created_at': income.created_at.isoformat() if income.created_at else None
        })
    
    if request.method == 'PUT':
        data = request.get_json() or {}
        if 'description' in data:
            income.description = data['description']
        if 'amount' in data:
            income.amount = data['amount']
        if 'discount' in data:
            income.discount = data['discount']
        if 'discount_description' in data:
            income.discount_description = data['discount_description']
        if 'agent_id' in data:
            income.agent_id = data['agent_id']
        db.session.commit()
        return jsonify({'success': True, 'income': {'id': income.id}})
    
    if request.method == 'DELETE':
        db.session.delete(income)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Income deleted'})


# API: Statistics and Reports
@app.route('/api/statistics', methods=['GET'])
@require_api_token
def api_statistics():
    """Get comprehensive statistics"""
    month = request.args.get('month')
    year = request.args.get('year')
    
    if month and year:
        purchases = Purchase.query.filter(
            db.func.strftime('%m', Purchase.created_at) == month,
            db.func.strftime('%Y', Purchase.created_at) == year
        ).all()
        incomes = Income.query.filter(
            db.func.strftime('%m', Income.created_at) == month,
            db.func.strftime('%Y', Income.created_at) == year
        ).all()
    else:
        purchases = Purchase.query.all()
        incomes = Income.query.all()
    
    total_purchases = sum(float(p.amount) for p in purchases)
    total_income = sum(float(i.amount) - float(i.discount or 0) for i in incomes)
    
    return jsonify({
        'period': f'{year}-{month}' if month and year else 'all_time',
        'agents': {
            'total': Agent.query.count(),
            'active': Agent.query.join(Task).filter(Task.status == 'in_progress').distinct().count()
        },
        'tasks': {
            'total': Task.query.count(),
            'pending': Task.query.filter_by(status='pending').count(),
            'in_progress': Task.query.filter_by(status='in_progress').count(),
            'completed': Task.query.filter_by(status='completed').count()
        },
        'financial': {
            'total_purchases': total_purchases,
            'total_income': total_income,
            'profit': total_income - total_purchases,
            'purchases_count': len(purchases),
            'income_count': len(incomes)
        }
    })


# API: Agent Performance Report
@app.route('/api/agents/<int:agent_id>/performance', methods=['GET'])
@require_api_token
def api_agent_performance(agent_id):
    """Get performance report for specific agent"""
    agent = Agent.query.get_or_404(agent_id)
    month = request.args.get('month')
    year = request.args.get('year')
    
    tasks_query = Task.query.filter_by(agent_id=agent_id)
    purchases_query = Purchase.query.filter_by(agent_id=agent_id)
    income_query = Income.query.filter_by(agent_id=agent_id)
    
    if month and year:
        tasks_query = tasks_query.filter(
            db.func.strftime('%m', Task.created_at) == month,
            db.func.strftime('%Y', Task.created_at) == year
        )
        purchases_query = purchases_query.filter(
            db.func.strftime('%m', Purchase.created_at) == month,
            db.func.strftime('%Y', Purchase.created_at) == year
        )
        income_query = income_query.filter(
            db.func.strftime('%m', Income.created_at) == month,
            db.func.strftime('%Y', Income.created_at) == year
        )
    
    tasks = tasks_query.all()
    completed_tasks = [t for t in tasks if t.status == 'completed']
    
    return jsonify({
        'agent': {
            'id': agent.id,
            'name': agent.name,
            'phone': agent.phone,
            'email': agent.email
        },
        'period': f'{year}-{month}' if month and year else 'all_time',
        'tasks': {
            'total': len(tasks),
            'completed': len(completed_tasks),
            'pending': len([t for t in tasks if t.status == 'pending']),
            'in_progress': len([t for t in tasks if t.status == 'in_progress'])
        },
        'financial': {
            'purchases': sum(float(p.amount) for p in purchases_query.all()),
            'income': sum(float(i.amount) - float(i.discount or 0) for i in income_query.all()),
            'commission': sum(float(t.agent_commission or 0) for t in completed_tasks)
        }
    })


if __name__ == '__main__':
    # Production: Set debug=False
    # Development: Set debug=True
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, port=5001)
