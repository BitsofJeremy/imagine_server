import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    COMFYUI_URL = os.environ.get('COMFYUI_URL') or 'http://localhost:8188'

