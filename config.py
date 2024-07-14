import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-secret-key'
    COMFYUI_URL = os.environ.get('COMFYUI_URL') or 'http://localhost:8188'
    FLASK_ENV = os.environ.get('FLASK_ENV') or 'production'
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'

    # Corrected path to the workflows directory
    WORKFLOWS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'workflows')

    # Logging configuration
    import logging
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='app.log',
        filemode='a'
    )

    # Add any other configuration variables your application needs