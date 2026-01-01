"""
WSGI Configuration for PythonAnywhere
Copy this file content to: /var/www/<username>_pythonanywhere_com_wsgi.py
"""

import sys
import os

# Add your project directory to the sys.path
project_home = '/home/autoprotectagadir/auto-protect-db'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'
os.environ['SECRET_KEY'] = 'ICS2xL4W_PSarfwEs4E942HXgR1e1x9OsMI-PN4hLsE'

# Import Flask app
from app import app as application
