import os
from pathlib import Path

# Database Configuration
BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite:///{BASE_DIR}/portfolio.db"

# Security Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')  # Change this in production
API_KEY_SALT = os.getenv('API_KEY_SALT', 'your-api-salt-here')  # Change this in production

# Email Configuration
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'isharamadunika9@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')  # Set this in production 