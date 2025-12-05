import re
import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HOME_HTML = os.path.join(BASE, 'homepage.html')
LOCAL_HTML = os.path.join(BASE, 'templates', 'landing.html')
STATIC_DIR = os.path.join(BASE, 'static', 'landing')

# regex not needed; asset detection is done via BeautifulSoup

def extract_assets_from_html(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    assets = set()
    # href in link
    for m in re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', text, re.I):
        assets.add(m)
    # src in script/img/source
    for m in re.findall(r'<(?:script|img|source)[^>]+src=["\']([^"\']+)["\']', text, re.I):
        assets.add(m)
    # srcset
    for m in re.findall(r'srcset=["\']([^"\']+)["\']', text, re.I):
        for part in m.split(','):
            assets.add(part.strip().split(' ')[0])
    return assets, text


def local_asset_present(url):
    # convert URL path to local static path if possible
    # check if url contains '/wp-content' or '/static/landing/' etc
    if url.startswith('/'):
        # absolute path on site
        candidate = url.lstrip('/')
        local = os.path.join(BASE, candidate.replace('/', os.sep))
        return os.path.exists(local), local
    if 'biasharabridges.com' in url:
        # map to static/landing by taking basename
        b = os.path.basename(url.split('?')[0])
        # search static/landing recursively
        for root, dirs, files in os.walk(STATIC_DIR):
            if b in files:
                return True, os.path.join(root, b)
        return False, os.path.join(STATIC_DIR, b)
    # protocol-relative or other
    b = os.path.basename(url.split('?')[0])
    for root, dirs, files in os.walk(STATIC_DIR):
        if b in files:
            return True, os.path.join(root, b)
    return False, os.path.join(STATIC_DIR, b)


if not os.path.exists(HOME_HTML):
    print('Error: homepage.html not found in repo root. Unable to compare live HTML.')
    raise SystemExit(1)

if not os.path.exists(LOCAL_HTML):
    print('Error: templates/landing.html not found. Nothing to compare.')
    raise SystemExit(1)

live_assets, live_html = extract_assets_from_html(HOME_HTML)
local_assets, local_html = extract_assets_from_html(LOCAL_HTML)

print('Live page assets count:', len(live_assets))
print('Local page assets count:', len(local_assets))

# asset overlap
common = set()
missing = []
for a in live_assets:
    present, local_path = local_asset_present(a)
    if present:
        common.add(a)
    else:
        missing.append((a, local_path))

print('\nAssets referenced by live site that are NOT present (or not mapped) in local static/landing:')
for a, p in missing:
    print('-', a, '-> expected at', p)

# Compare HTML files roughly
if live_html.strip() == local_html.strip():
    print('\nHTML is identical (exact match)')
else:
    print('\nHTML differs. Summary:')
    # show basic stats
    print(' Live HTML length:', len(live_html))
    print(' Local HTML length:', len(local_html))
    # list top-level differences: title
    def get_title(html):
        m = re.search(r'<title>(.*?)</title>', html, re.I|re.S)
        return m.group(1).strip() if m else ''
    print(' Live title:', get_title(live_html))
    print(' Local title:', get_title(local_html))

# show assets in live not in local (count)
print('\nSummary:')
print(' Common asset count (found in local):', len(common))
print(' Missing asset count:', len(missing))

# show a short sample of common assets
print('\nSample common assets:')
for i,a in enumerate(sorted(list(common))[:20]):
    print('-', a)

print('\nDone.')
