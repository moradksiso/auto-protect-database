from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()


class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    # Distinguish admin vs agent in Flask-Login sessions
    def get_id(self):
        return f"admin:{self.id}"

class Agent(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    params = db.Column(db.Text)  # JSON string for parameters
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Login credentials for agents
    username = db.Column(db.String(80), unique=True)
    password_hash = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)

    def get_id(self):
        return f"agent:{self.id}"

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.Date)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    income_id = db.Column(db.Integer, db.ForeignKey('income.id'))
    car_count = db.Column(db.Integer, default=0)  # عدد السيارات المغلفة


class MonthlyTarget(db.Model):
    """أهداف شهرية لكل موظف"""
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)  # 1-12
    target_cars = db.Column(db.Integer, default=0)  # الهدف: عدد السيارات المغلفة
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('admin.id'))
    
    # Relationship to agent
    agent = db.relationship('Agent', backref='monthly_targets', foreign_keys=[agent_id])

class FileUpload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('admin.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'))
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.Text)
    date = db.Column(db.Date, default=datetime.utcnow)

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'))
    amount = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(200))
    customer_name = db.Column(db.String(200))
    service_type = db.Column(db.String(200))
    car_type = db.Column(db.String(200))
    note = db.Column(db.Text)
    date = db.Column(db.Date, default=datetime.utcnow)
    invoice_number = db.Column(db.String(50), unique=True)


class ServiceType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CarType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(200))
    detail = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('admin.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class APIToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('admin.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    revoked = db.Column(db.Boolean, default=False)
