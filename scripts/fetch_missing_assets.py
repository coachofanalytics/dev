#!/usr/bin/env python3
"""Fetch remaining missing assets for landing page into static/landing/.

What it does:
- Scans `templates/landing.html` for external URLs (revslider, fonts.googleapis.com, fonts.gstatic.com).
- Downloads each URL, strips querystrings, and saves under `static/landing/<netloc><path>`.
- If a CSS file from Google Fonts references font files on fonts.gstatic.com, those are downloaded too.
- Creates small stub files for `/feed/` and `/wp-json/` paths if referenced.

Run from repo root (where `manage.py` lives):
  python scripts/fetch_missing_assets.py
"""

import os
import re
import sys
from urllib.parse import urlparse, urljoin

try:
    import requests
except Exception:
    print("Missing dependency: requests. Install in your venv and re-run: pip install requests")
    sys.exit(1)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TEMPLATES = os.path.join(ROOT, 'templates')
LANDING = os.path.join(ROOT, 'static', 'landing')
LANDING_REL = 'static/landing'

os.makedirs(LANDING, exist_ok=True)

def safe_path_for_url(url):
    p = urlparse(url)
    netloc = p.netloc.replace(':', '_')
    path = p.path.lstrip('/')
    # If this is the source site and refers to wp-content, save under static/landing/wp-content/...
    if 'biasharabridges.com' in netloc and '/wp-content/' in p.path:
        rel = p.path.lstrip('/')
        save = os.path.join(LANDING, rel)
        d = os.path.dirname(save)
        os.makedirs(d, exist_ok=True)
        return save
    if not path or path.endswith('/'):
        # give sensible filename
        filename = 'index'
        folder = os.path.join(LANDING, netloc, path)
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, filename)
    parts = [netloc] + path.split('/')
    # remove any empty parts
    parts = [part for part in parts if part]
    # strip querystrings completely
    filename = parts[-1]
    folder = os.path.join(LANDING, *parts[:-1]) if len(parts) > 1 else os.path.join(LANDING, parts[0])
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, filename)

def normalized_url(found):
    # handle protocol-relative URLs
    if found.startswith('//'):
        return 'https:' + found
    if found.startswith('http://') or found.startswith('https://'):
        return found
    return None

def extract_urls_from_template(template_text):
    # find src/href occurrences
    urls = set()
    # common patterns
    for match in re.findall(r'(?:src|href)=["\']([^"\']+)["\']', template_text, flags=re.I):
        if match.startswith('http') or match.startswith('//'):
            urls.add(match)
    # also capture @import url(...) in inline styles
    for match in re.findall(r'@import\s+url\(([^\)]+)\)', template_text):
        u = match.strip("'\" ")
        if u.startswith('http') or u.startswith('//'):
            urls.add(u)
    return urls

def download_url(url):
    norm = normalized_url(url)
    if not norm:
        return None
    p = urlparse(norm)
    print('Downloading:', norm)
    try:
        resp = requests.get(norm, timeout=20)
    except Exception as e:
        print('  ERROR downloading', norm, e)
        return None
    if resp.status_code != 200:
        print('  HTTP', resp.status_code, 'for', norm)
        return None
    # decide filename
    save_path = safe_path_for_url(norm)
    # if the URL had an extension missing (like fonts.googleapis.com/css2), add .css
    if not os.path.splitext(save_path)[1]:
        # try to infer from content-type
        ct = resp.headers.get('content-type', '')
        if 'text/css' in ct or 'font' in ct or 'application/javascript' in ct or 'javascript' in ct:
            ext = '.css' if 'css' in ct else ('.js' if 'javascript' in ct else '')
            save_path = save_path + ext
    # ensure we don't write querystrings into filename (we stripped earlier)
    try:
        with open(save_path, 'wb') as f:
            f.write(resp.content)
    except Exception as e:
        print('  ERROR saving to', save_path, e)
        return None
    print('  Saved to', os.path.relpath(save_path, ROOT))
    return (norm, save_path, resp)

def find_and_download_fonts_from_css(css_text, base_url=None):
    # find url(...) occurrences
    found = re.findall(r'url\(([^)]+)\)', css_text)
    downloaded = []
    for u in found:
        u = u.strip(' \"\'')
        # handle relative URLs in CSS
        if u.startswith('data:'):
            continue
        if u.startswith('//'):
            u = 'https:' + u
        if u.startswith('/') and base_url:
            u = urljoin(base_url, u)
        if not u.startswith('http'):
            continue
        # only download fonts.gstatic.com or other hosts referenced
        if 'fonts.gstatic.com' in u or 'fonts.googleapis.com' in u or '.woff' in u or '.woff2' in u or '.ttf' in u or '.otf' in u:
            r = download_url(u)
            if r:
                downloaded.append(r)
    return downloaded

def create_stub(path_rel):
    p = os.path.join(LANDING, path_rel.lstrip('/'))
    d = os.path.dirname(p)
    os.makedirs(d, exist_ok=True)
    if os.path.exists(p):
        return p
    with open(p, 'w', encoding='utf-8') as f:
        f.write('<!-- stub generated for local dev -->\n')
        f.write('<html><body>This is a local stub for %s</body></html>' % path_rel)
    print('  Created stub', os.path.relpath(p, ROOT))
    return p

def main():
    tpl_path = os.path.join(TEMPLATES, 'landing.html')
    if not os.path.exists(tpl_path):
        print('templates/landing.html not found at', tpl_path)
        return 1
    with open(tpl_path, 'r', encoding='utf-8') as f:
        tpl = f.read()

    urls = extract_urls_from_template(tpl)
    # filter to relevant hosts
    interesting = set()
    for u in urls:
        lu = u.lower()
        if 'fonts.googleapis.com' in lu or 'fonts.gstatic.com' in lu or 'revslider' in lu or 'biasharabridges.com/wp-json' in lu or '/feed/' in lu:
            interesting.add(u)

    # Add common revslider paths (CSS + JS) that the live page references
    # Include the ?ver=6.7.37 querystring variants so we save the exact assets
    interesting.update({
        'https://biasharabridges.com/wp-content/plugins/revslider/public/css/sr7.css?ver=6.7.37',
        'https://biasharabridges.com/wp-content/plugins/revslider/public/js/sr7.js?ver=6.7.37',
        'https://biasharabridges.com/wp-content/plugins/revslider/public/js/libs/tptools.js?ver=6.7.37',
    })

    print('Found %d interesting external URLs to fetch' % len(interesting))

    downloaded = []
    for u in sorted(interesting):
        res = download_url(u)
        if res:
            downloaded.append(res)
            # if CSS, parse for fonts
            _, _, resp = res
            ct = resp.headers.get('content-type', '')
            if 'text/css' in ct or (u.endswith('.css') or 'fonts.googleapis.com' in u):
                css_text = resp.text
                find_and_download_fonts_from_css(css_text, base_url=u)

    # create stubs for feeds and wp-json if referenced
    if 'feed/' in tpl or 'comments/feed' in tpl:
        print('Creating feed stubs')
        create_stub('feed/index.html')
        create_stub('comments/feed/index.html')
    if 'wp-json' in tpl or 'wp-json' in ' '.join(urls):
        print('Creating wp-json stub')
        create_stub('wp-json/index.html')

    print('\nSummary:')
    print('  Files downloaded:', len(downloaded))
    print('  Assets saved under', LANDING_REL)
    print('  If any externals remain, run the comparator and re-run this script to fetch more.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
