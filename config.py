import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'sms.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

SECRET_KEY = os.environ.get('SECRET_KEY', 'apex-sms-super-secret-key-2026')
SCHOOL_NAME = "Apex International Academy"
SCHOOL_TAGLINE = "Empowering Minds, Shaping the Future"
SCHOOL_ADDRESS = "104 Academy Boulevard, Tech City, TC 45201"
SCHOOL_CONTACT = "+1 (555) 234-5678 | info@apexacademy.edu"
SCHOOL_ACADEMIC_YEAR = "2025-2026"
