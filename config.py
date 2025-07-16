import os

SESSION_TYPE = 'filesystem'
SESSION_PERMANENT = False
ADMIN_SECRET= 'adminUser04356'
SENDGRID_API_KEY = 'Your_Api_key'
SESSION_FILE_DIR = os.path.abspath('flask-session_custom')  # Custom folder
