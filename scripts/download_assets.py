import os
import re
import requests
from urllib.parse import urljoin, urlparse

ROOT = 'https://biasharabridges.com/'
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'landing')

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'css'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'js'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'images'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, 'fonts'), exist_ok=True)

def save_file(url, subdir):
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
    except Exception as e:
        print(f'Failed to fetch {url}: {e}')
        return
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path) or 'file'
    # ensure unique name
    out_path = os.path.join(OUT_DIR, subdir, filename)
    with open(out_path, 'wb') as f:
        f.write(r.content)
    print('Saved', url, '->', out_path)

def main():
    print('Fetching', ROOT)
    r = requests.get(ROOT, timeout=20)
    r.raise_for_status()
    html = r.text

    # find CSS links
    css_urls = re.findall(r'<link[^>]+href=["\']([^"\']+\.css)["\']', html)
    # find JS
    js_urls = re.findall(r'<script[^>]+src=["\']([^"\']+\.js)["\']', html)
    # find images
    img_urls = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
    # find font urls (woff, woff2, ttf)
    font_urls = re.findall(r'url\(["\']?([^"\')]+\.(?:woff2?|ttf|otf))["\']?\)', html)

    # normalize and download
    all_urls = []
    for u in css_urls:
        full = urljoin(ROOT, u)
        all_urls.append(('css', full))
    for u in js_urls:
        full = urljoin(ROOT, u)
        all_urls.append(('js', full))
    for u in img_urls:
        full = urljoin(ROOT, u)
        all_urls.append(('images', full))
    for u in font_urls:
        full = urljoin(ROOT, u)
        all_urls.append(('fonts', full))

    # deduplicate preserving order
    seen = set()
    dedup = []
    for sub, url in all_urls:
        if url in seen:
            continue
        seen.add(url)
        dedup.append((sub, url))

    print('Found', len(dedup), 'assets')
    for sub, url in dedup:
        save_file(url, sub)

    # scan downloaded CSS for font urls and other referenced assets
    css_dir = os.path.join(OUT_DIR, 'css')
    font_refs = set()
    if os.path.isdir(css_dir):
        for fn in os.listdir(css_dir):
            path = os.path.join(css_dir, fn)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = f.read()
            except Exception:
                continue
            refs = re.findall(r'url\(["\']?([^"\')]+\.(?:woff2?|ttf|otf|eot|svg))["\']?\)', data)
            for r in refs:
                full = urljoin(ROOT, r)
                font_refs.add(full)

    for url in font_refs:
        save_file(url, 'fonts')

if __name__ == '__main__':
    main()
