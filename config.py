import os

SESSION_TYPE = 'filesystem'
SESSION_PERMANENT = False
ADMIN_SECRET= 'adminUser04356'
SENDGRID_API_KEY = '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'
SESSION_FILE_DIR = os.path.abspath('flask-session_custom')  # Custom folder