import os
import django
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()
from main.models import EmergencyHotlines, EmergencyHelpActivations
print('EmergencyHotlines count:', EmergencyHotlines.objects.count())
print('EmergencyHelpActivations count:', EmergencyHelpActivations.objects.count())
