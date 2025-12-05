import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'templates' / 'landing.html'
BACKUP = TEMPLATE.with_suffix('.bak.fix_landing_quotes.html')

text = TEMPLATE.read_text(encoding='utf-8')
TEMPLATE.write_text(text, encoding='utf-8')
# create backup
if not BACKUP.exists():
    BACKUP.write_text(text, encoding='utf-8')

orig = text
new = orig

# 1) Fix double-quoted static tags: ""{% static '...'%}"" -> "{% static '...' %}"
new = re.sub(r'""(\{\%\s*static\s+[^\%]*\%\})""', r'\1', new)
# The above may remove too many quotes in some contexts; ensure attributes have proper quotes
# 2) If after previous step we have attributes like href={% static '...' %} (no quotes), add quotes
new = re.sub(r'href=(\{\%\s*static\s+[^\%]*\%\})', r'href="\1"', new)
new = re.sub(r'src=(\{\%\s*static\s+[^\%]*\%\})', r'src="\1"', new)

# 3) Fix remaining patterns like href=""/"" -> href="/"
new = new.replace('href=""/""', 'href="/"')
new = new.replace('href=""/""', 'href="/"')

# 4) Fix cases like src=""{% static '...' %}"" -> src="{% static '...' %}"
new = re.sub(r'src=\"\"(\{\%\s*static\s+[^\%]*\%\})\"\"', r'src="\1"', new)
new = re.sub(r'href=\"\"(\{\%\s*static\s+[^\%]*\%\})\"\"', r'href="\1"', new)

# 5) Fix javascript vars wrapped with doubled quotes: = ""{% static ... %}"" -> = "{% static ... %}"
new = re.sub(r'=\s*\"\"(\{\%\s*static\s+[^\%]*\%\})\"\"', r'= "\1"', new)

# 6) Fix SR7.E.* assignments that use single quotes around static tags: change to double quotes
new = re.sub(r"SR7\.E\.ajaxurl\s*=\s*'(.+?admin-ajax\.php.+?)';", r'SR7.E.ajaxurl = "\1";', new)
new = re.sub(r"SR7\.E\.resturl\s*=\s*'(.+?wp-json/.+?)';", r'SR7.E.resturl = "\1";', new)
new = re.sub(r"SR7\.E\.plugin_url\s*=\s*'(.+?revslider/.+?)';", r'SR7.E.plugin_url = "\1";', new)
new = re.sub(r"SR7\.E\.wp_plugin_url\s*=\s*'(.+?wp-content/plugins/.+?)';", r'SR7.E.wp_plugin_url = "\1";', new)

# 7) Normalize any leftover occurrences of ""{% static ... %}"" -> "{% static ... %}"
new = re.sub(r'""(\{\%\s*static\s+[^\%]*\%\})""', r'"\1"', new)

# 8) Replace twitter/url and og:url empty broken values like content=""/"" -> content="/"
new = new.replace('content=""/""', 'content="/"')
new = new.replace('url":""/""', 'url":"/"')

# 9) Replace remaining double-empty hrefs: href=""" -> href="
new = new.replace('href=""', 'href="')
new = new.replace('src=""', 'src="')

if new != orig:
    TEMPLATE.write_text(new, encoding='utf-8')
    print(f'Patched {TEMPLATE} (backup at {BACKUP})')
else:
    print('No changes made')
