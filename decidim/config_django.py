import os
import django
import sys

BASE_DIR = os.path.dirname((os.path.dirname(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_hub.settings")
django.setup()
