#!/usr/bin/env python3
"""Convert `homepage.html` into a local Django template `templates/landing.html`.

Replacements:
- For any asset URL pointing to biasharabridges.com (absolute or protocol-relative), map
  it to a local file under `static/landing/` if present; otherwise attempt to download it
  into that location and then map.
- For Google Fonts URLs, attempt to download the CSS file and any referenced fonts if possible
  into `static/landing/wp-content/uploads/elementor/google-fonts/css/` and reference locally.
- Remove dynamic endpoints like feeds and wp-json links (replace href with '#').

This is targeted for a single-page local replica; navigation hrefs are left unchanged.
"""
import os
import re
import sys
from urllib.parse import urlparse
import requests

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HOME_HTML = os.path.join(BASE, 'homepage.html')
OUT_TEMPLATE = os.path.join(BASE, 'templates', 'landing.html')
STATIC_DIR = os.path.join(BASE, 'static', 'landing')
SITE_DOMAIN = 'biasharabridges.com'

if not os.path.exists(HOME_HTML):
    print('Error: homepage.html not found at', HOME_HTML)
    sys.exit(1)

with open(HOME_HTML, 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

session = requests.Session()
session.headers.update({'User-Agent': 'make-local-landing/1.0'})

def make_full(u):
    u = u.strip()
    if u.startswith('//'):
        return 'https:' + u
    if u.startswith('http://') or u.startswith('https://'):
        return u
    if u.startswith('/'):
        return 'https://' + SITE_DOMAIN + u
    return None

def find_local_by_basename(basename):
    for root, dirs, files in os.walk(STATIC_DIR):
        if basename in files:
            return os.path.join(root, basename)
    return None

def download_to_target(url, target_path):
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    try:
        print('Downloading', url, '->', target_path)
        r = session.get(url, timeout=20, stream=True)
        r.raise_for_status()
        with open(target_path, 'wb') as w:
            for chunk in r.iter_content(8192):
                w.write(chunk)
        return True
    except Exception as e:
        print('Failed to download', url, 'error:', e)
        return False

def map_url_to_static(url):
    full = make_full(url)
    if not full:
        return None
    parsed = urlparse(full)
    # skip wp-json, feed, xmlrpc
    if parsed.path.startswith('/wp-json') or parsed.path.endswith('/feed/') or 'xmlrpc.php' in parsed.path:
        return '#'

    basename = os.path.basename(parsed.path)
    # try to find local existing file by basename
    local = find_local_by_basename(basename)
    if local:
        rel = os.path.relpath(local, STATIC_DIR).replace(os.sep, '/')
        return "{% static 'landing/" + rel + "' %}"

    # else, attempt to download and save to STATIC_DIR using the path
    rel_path = parsed.path.lstrip('/')
    target = os.path.join(STATIC_DIR, rel_path.replace('/', os.sep))
    success = download_to_target(full, target)
    if success:
        rel = os.path.relpath(target, STATIC_DIR).replace(os.sep, '/')
        return "{% static 'landing/" + rel + "' %}"

    # as fallback, try to match by basename in any location
    local2 = find_local_by_basename(basename)
    if local2:
        rel = os.path.relpath(local2, STATIC_DIR).replace(os.sep, '/')
        return "{% static 'landing/" + rel + "' %}"

    return None

# Replace href/src/srcset values
def replace_attrs(text):
    # href
    def href_repl(m):
        url = m.group(1)
        mapped = None
        # ignore mailto and javascript
        if url.startswith('mailto:') or url.startswith('javascript:'):
            return m.group(0)
        if 'fonts.googleapis.com' in url or 'fonts.gstatic.com' in url:
            # try to download into elementor/google-fonts folder
            full = make_full(url)
            if full:
                basename = os.path.basename(full.split('?')[0])
                tgt = os.path.join(STATIC_DIR, 'wp-content', 'uploads', 'elementor', 'google-fonts', 'css', basename)
                if download_to_target(full, tgt):
                    rel = os.path.relpath(tgt, STATIC_DIR).replace(os.sep, '/')
                    mapped = "{% static 'landing/" + rel + "' %}"
        if mapped is None:
            mapped = map_url_to_static(url)
        if mapped:
            return m.group(0).replace(url, mapped)
        return m.group(0)

    text = re.sub(r'href=["\']([^"\']+)["\']', href_repl, text, flags=re.I)

    # src and srcset
    def src_repl(m):
        url = m.group(1)
        mapped = map_url_to_static(url)
        if mapped:
            return m.group(0).replace(url, mapped)
        return m.group(0)

    text = re.sub(r'src=["\']([^"\']+)["\']', src_repl, text, flags=re.I)
    # srcset: handle multiple entries
    def srcset_repl(m):
        val = m.group(1)
        parts = [p.strip() for p in val.split(',')]
        newparts = []
        for p in parts:
            url = p.split(' ')[0]
            rest = ' '.join(p.split(' ')[1:])
            mapped = map_url_to_static(url)
            if mapped:
                newparts.append(mapped + (' ' + rest if rest else ''))
            else:
                newparts.append(p)
        return 'srcset="' + ', '.join(newparts) + '"'

    text = re.sub(r'srcset=["\']([^"\']+)["\']', srcset_repl, text, flags=re.I)
    return text

new_html = html

# prepend Django static load if not present
if '{% load static %}' not in new_html:
    new_html = '{% load static %}\n' + new_html

new_html = replace_attrs(new_html)

# remove or neutralize dynamic endpoints: wp-json, feed, xmlrpc
new_html = re.sub(r'href=["\']https?://[^"\']*/wp-json/[^"\']*["\']', 'href="#"', new_html)
new_html = re.sub(r'href=["\']https?://[^"\']*/feed/[^"\']*["\']', 'href="#"', new_html)
new_html = re.sub(r'src=["\']https?://[^"\']*/wp-json/[^"\']*["\']', 'src="#"', new_html)

with open(OUT_TEMPLATE, 'w', encoding='utf-8') as f:
    f.write(new_html)

print('Wrote', OUT_TEMPLATE)

print('Done. Please start the dev server and open http://127.0.0.1:8000/ to view the page.')
