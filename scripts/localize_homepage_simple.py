#!/usr/bin/env python3
"""Simpler localization: convert biasharabridges.com absolute/protocol URLs to local `{% static %}` paths.

This does not attempt to download new files; it maps URLs whose path component can be found under
`static/landing/` by creating a `{% static 'landing/<path>' %}` replacement. For any `/wp-json` or
feed/xmlrpc links it replaces the href with `#`.
"""
import os
import re
from urllib.parse import urlparse

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HOME_HTML = os.path.join(BASE, 'homepage.html')
OUT = os.path.join(BASE, 'templates', 'landing.html')
STATIC_DIR = os.path.join(BASE, 'static', 'landing')
SITE = 'biasharabridges.com'

if not os.path.exists(HOME_HTML):
    print('homepage.html missing:', HOME_HTML)
    raise SystemExit(1)

with open(HOME_HTML, 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

def local_for_path(path):
    # path begins with '/'
    candidate = path.lstrip('/')
    full_local = os.path.join(STATIC_DIR, *candidate.split('/'))
    if os.path.exists(full_local):
        return "{% static 'landing/" + candidate.replace('\\', '/') + "' %}"
    # try basename search
    base = os.path.basename(path)
    for root, dirs, files in os.walk(STATIC_DIR):
        if base in files:
            rel = os.path.relpath(os.path.join(root, base), STATIC_DIR).replace('\\', '/')
            return "{% static 'landing/" + rel + "' %}"
    return None

# add load static at top
if '{% load static %}' not in html:
    html = '{% load static %}\n' + html

# replace absolute biasharabridges.com URLs
def replace_site_urls(m):
    url = m.group(0)
    parsed = urlparse(url if url.startswith('http') else 'https:' + url)
    path = parsed.path
    if path.startswith('/wp-json') or path.endswith('/feed/') or 'xmlrpc.php' in path:
        return '"#"'
    mapped = local_for_path(path)
    if mapped:
        return '"' + mapped + '"'
    # fallback: remove domain, keep path (relative)
    return '"' + path + '"'

html = re.sub(r'"//?'+re.escape(SITE)+r'[^"\s]*"', replace_site_urls, html)
html = re.sub(r'"https?://'+re.escape(SITE)+r'[^"\s]*"', replace_site_urls, html)

# neutralize feeds/wp-json/xmlrpc in other forms
html = re.sub(r'href=["\"]?https?://[^"\s]*/wp-json/[^"\s]*', 'href="#"', html)
html = re.sub(r'href=["\"]?https?://[^"\s]*/feed/[^"\s]*', 'href="#"', html)
html = re.sub(r'href=["\"]?https?://[^"\s]*/xmlrpc.php', 'href="#"', html)

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html)

print('Wrote', OUT)
