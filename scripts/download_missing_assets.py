#!/usr/bin/env python3
"""Download missing assets referenced in `homepage.html` into `static/landing/`.

Behavior:
- Parse `homepage.html` for asset URLs (link href, script/img/src, srcset).
- For absolute/site-relative URLs pointing to biasharabridges.com (or starting with '/') download and save under `static/landing/<path>`.
- Skip external domains (except those on biasharabridges.com and protocol-relative URLs).
- After downloading, insert <link> tags for CSS into the head of `templates/landing.html` and <script> tags before </body> for JS assets (if not already referenced).
- Re-run the comparison logic from `compare_with_live.py` to show updated counts.

Note: This is a best-effort static copy; dynamic server-driven features will still not work.
"""
import os
import re
import sys
import requests
from urllib.parse import urlparse, urljoin

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HOME_HTML = os.path.join(BASE, 'homepage.html')
LOCAL_HTML = os.path.join(BASE, 'templates', 'landing.html')
STATIC_DIR = os.path.join(BASE, 'static', 'landing')
SITE_DOMAIN = 'biasharabridges.com'

if not os.path.exists(HOME_HTML):
    print('homepage.html not found; place a copy of the live site HTML at', HOME_HTML)
    sys.exit(1)
if not os.path.exists(LOCAL_HTML):
    print('templates/landing.html not found; ensure file exists at', LOCAL_HTML)
    sys.exit(1)

with open(HOME_HTML, 'r', encoding='utf-8', errors='ignore') as f:
    live_html = f.read()

assets = set()
for m in re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', live_html, re.I):
    assets.add(m)
for m in re.findall(r'<(?:script|img|source)[^>]+src=["\']([^"\']+)["\']', live_html, re.I):
    assets.add(m)
for m in re.findall(r'srcset=["\']([^"\']+)["\']', live_html, re.I):
    for part in m.split(','):
        assets.add(part.strip().split(' ')[0])

print(f'Found {len(assets)} assets in homepage.html; attempting to download site assets for fidelity.')

downloaded = []
skipped = []

session = requests.Session()
session.headers.update({'User-Agent': 'biashara-landing-downloader/1.0'})

def full_url(u):
    u = u.strip()
    if u.startswith('//'):
        return 'https:' + u
    if u.startswith('http://') or u.startswith('https://'):
        return u
    if u.startswith('/'):
        return f'https://{SITE_DOMAIN}' + u
    # relative path on site: join with site root
    if SITE_DOMAIN in u:
        return u
    return None

def local_target_path(url):
    # Save under STATIC_DIR + url_path (discard query)
    p = urlparse(url).path
    if p.startswith('/'):
        p = p.lstrip('/')
    return os.path.join(STATIC_DIR, p.replace('/', os.sep))

for a in sorted(assets):
    fu = full_url(a)
    if not fu:
        skipped.append((a, 'not site/unsupported'))
        continue
    # only download from the site domain
    parsed = urlparse(fu)
    if SITE_DOMAIN not in parsed.netloc and not parsed.netloc.endswith(SITE_DOMAIN):
        skipped.append((a, f'external domain {parsed.netloc}'))
        continue

    target = local_target_path(fu)
    if os.path.exists(target):
        skipped.append((a, 'already exists'))
        continue

    os.makedirs(os.path.dirname(target), exist_ok=True)
    try:
        print('Downloading', fu)
        r = session.get(fu, timeout=20, stream=True)
        r.raise_for_status()
        with open(target, 'wb') as out:
            for chunk in r.iter_content(8192):
                out.write(chunk)
        downloaded.append((a, target))
    except Exception as e:
        skipped.append((a, f'error: {e}'))

print('\nDownload finished.')
print('Downloaded:', len(downloaded), 'Skipped:', len(skipped))

# Now update templates/landing.html to include missing references.
with open(LOCAL_HTML, 'r', encoding='utf-8') as f:
    local_html = f.read()

head_insert = []
body_scripts = []

for a, target in downloaded:
    # determine type by extension
    path_on_static = os.path.relpath(target, STATIC_DIR).replace(os.sep, '/')
    if re.search(r'\.css($|\?)', a, re.I):
        tag = f"<link rel=\"stylesheet\" href=\"{{% static 'landing/{path_on_static}' %}}\">"
        if tag not in local_html:
            head_insert.append(tag)
    elif re.search(r'\.js($|\?)', a, re.I):
        tag = f"<script src=\"{{% static 'landing/{path_on_static}' %}}\"></script>"
        if tag not in local_html:
            body_scripts.append(tag)
    else:
        # images/fonts: nothing to add to template automatically
        pass

if head_insert:
    # insert before </head>
    local_html = local_html.replace('</head>', '  ' + '\n  '.join(head_insert) + '\n</head>')

if body_scripts:
    # insert before </body>
    local_html = local_html.replace('</body>', '  ' + '\n  '.join(body_scripts) + '\n</body>')

with open(LOCAL_HTML, 'w', encoding='utf-8') as f:
    f.write(local_html)

print('\nUpdated templates/landing.html with', len(head_insert), 'CSS links and', len(body_scripts), 'script tags.')

print('\nRe-running comparison to measure remaining missing assets...')
import subprocess
res = subprocess.run([sys.executable, os.path.join(BASE, 'scripts', 'compare_with_live.py')], capture_output=True, text=True)
print(res.stdout)
if res.stderr:
    print('Errors from comparison script:', res.stderr)

print('\nDone.')
