import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'templates' / 'landing.html'
BACKUP = TEMPLATE.with_suffix('.bak.fix_landing_static_qs.html')

text = TEMPLATE.read_text(encoding='utf-8')
if not BACKUP.exists():
    BACKUP.write_text(text, encoding='utf-8')

# Replace patterns like {% static 'path/to/file.css?ver=123' %} -> {% static 'path/to/file.css' %}
new = re.sub(r"(\{\%\s*static\s+'([^']+?)\?)ver=[^' ]+'\s*\%\}", r"{% static '\2' %}", text)
# Also handle double-quoted static strings
new = re.sub(r'(\{\%\s*static\s+"([^"]+?)\?)ver=[^" ]+"\s*\%\}', r'{% static "\2" %}', new)

if new != text:
    TEMPLATE.write_text(new, encoding='utf-8')
    print(f'Stripped querystrings from static tags in {TEMPLATE} (backup at {BACKUP})')
else:
    print('No querystrings found in static tags')
