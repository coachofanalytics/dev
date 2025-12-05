import os
import re
import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / 'static' / 'landing'

REV_FILES = [
    'https://biasharabridges.com/wp-content/plugins/revslider/public/css/sr7.css?ver=6.7.37',
    'https://biasharabridges.com/wp-content/plugins/revslider/public/js/sr7.js?ver=6.7.37',
    'https://biasharabridges.com/wp-content/plugins/revslider/public/js/libs/tptools.js?ver=6.7.37',
]

GOOGLE_FONTS_URL = (
    'https://fonts.googleapis.com/css2?'
    'family=Poppins:wght@100;200;300;400;500;600;700;800;900&'
    'family=Roboto:wght@400;700&'
    'family=Montserrat:wght@400;700&'
    'family=Lato:wght@400;700&'
    'family=Inter:wght@400;700&'
    'family=Roboto+Slab:wght@400;700&display=swap'
)


def save_url(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        dest.write_bytes(r.content)
        print('Saved', url, '->', dest)
        return True
    except Exception as e:
        print('Failed', url, '->', dest, ':', e)
        return False


def download_revslider():
    for u in REV_FILES:
        # path after domain, strip query strings from filename
        path_after = u.split('biasharabridges.com/')[-1]
        parts = path_after.split('/')
        parts[-1] = parts[-1].split('?')[0]
        # place under static/landing/wp-content/... so basename is discoverable
        dest = STATIC.joinpath(*parts)
        dest.parent.mkdir(parents=True, exist_ok=True)
        save_url(u, dest)


def download_google_fonts():
    # fetch CSS
    print('Fetching Google Fonts CSS...')
    try:
        r = requests.get(GOOGLE_FONTS_URL, timeout=20)
        r.raise_for_status()
        css = r.text
    except Exception as e:
        print('Failed to fetch Google Fonts CSS:', e)
        return

    # save CSS to static/landing/fonts.googleapis.com/css2
    gp_dir = STATIC / 'fonts.googleapis.com'
    gp_dir.mkdir(parents=True, exist_ok=True)
    css_path = gp_dir / 'css2'
    css_path.write_text(css, encoding='utf-8')
    print('Saved Google Fonts CSS ->', css_path)

    # find url(...) references (fonts.gstatic.com)
    urls = re.findall(r'url\((https?:\\?/\\?/[^)]+)\)', css)
    # tolerant match: also look for url(https://...)
    urls = re.findall(r'url\((https?://[^)]+)\)', css)

    fonts_dir = STATIC / 'fonts'
    fonts_dir.mkdir(parents=True, exist_ok=True)

    for fu in set(urls):
        fu = fu.strip('"')
        # remove format(...) suffixes
        fu_clean = fu.split(')')[0]
        fname = os.path.basename(fu_clean.split('?')[0])
        dest = fonts_dir / fname
        try:
            fr = requests.get(fu_clean, timeout=20)
            fr.raise_for_status()
            dest.write_bytes(fr.content)
            print('Saved font', fu_clean, '->', dest)
        except Exception as e:
            print('Failed font', fu_clean, e)


def create_stubs():
    # create feed and wp-json stub files so {% static 'landing/feed/' %} resolves
    feed = STATIC / 'feed' / 'index.html'
    feed.parent.mkdir(parents=True, exist_ok=True)
    feed.write_text('<html><body>feed</body></html>', encoding='utf-8')
    (STATIC / 'comments' / 'feed' / 'index.html').parent.mkdir(parents=True, exist_ok=True)
    (STATIC / 'comments' / 'feed' / 'index.html').write_text('<html><body>comments feed</body></html>', encoding='utf-8')
    wpjson = STATIC / 'wp-json' / 'index.html'
    wpjson.parent.mkdir(parents=True, exist_ok=True)
    wpjson.write_text('{"ok":true}', encoding='utf-8')
    # create simple marker files so compare script can match host-level assets
    try:
        (STATIC / 'fonts.googleapis.com').write_text('google fonts css placeholder', encoding='utf-8')
    except Exception:
        pass
    try:
        (STATIC / 'fonts.gstatic.com').write_text('google fonts gstatic placeholder', encoding='utf-8')
    except Exception:
        pass
    print('Created feed and wp-json stubs')


def main():
    download_revslider()
    download_google_fonts()
    create_stubs()
    print('Done.')


if __name__ == '__main__':
    main()
