import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / 'templates' / 'landing.html'

def backup(fp: Path):
    bak = fp.with_suffix('.html.bak')
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    bak = fp.with_name(fp.stem + f'.bak.{timestamp}.html')
    bak.write_bytes(fp.read_bytes())
    return bak

def patch_content(s: str):
    replaced = 0

    # 1) Replace uploads URLs (full URLs) with {% static 'landing/...'%}
    # Match https://biasharabridges.com/wp-content/uploads/... up to quote or space
    def uploads_repl(m):
        nonlocal replaced
        url = m.group(0)
        # strip domain
        path = re.sub(r'https?://[^/]+/', '', url)
        # ensure leading landing/ prefix
        if not path.startswith('landing/'):
            path = 'landing/' + path
        rep = "{% static '" + path + "' %}"
        replaced += 1
        return rep

    s = re.sub(r'https://biasharabridges\.com/wp-content/uploads/[^\s"\)\']+', uploads_repl, s)

    # Also replace any remaining absolute uploads that used http (unlikely)
    s = re.sub(r'http://biasharabridges\.com/wp-content/uploads/[^\s"\)\']+', uploads_repl, s)

    # 2) Neutralize known external social and partner links by replacing href="https://..." with href="#"
    external_host_patterns = [
        r'https?://web\.facebook\.com/[^"\s]*',
        r'https?://x\.com/[^"\s]*',
        r'https?://twitter\.com/[^"\s]*',
        r'https?://(www\.)?instagram\.com/[^"\s]*',
        r'https?://(www\.)?linkedin\.com/[^"\s]*',
        r'https?://(www\.)?startersites\.io/[^"\s]*',
        r'https?://cookieadmin\.net/[^"\s]*',
        r'https?://cookieadmin\.net/[^"\s]*',
    ]
    for pat in external_host_patterns:
        s, n = re.subn(pat, '#', s)
        replaced += n

    # 3) Replace canonical, og:url, twitter:url, shortlink values that point to biasharabridges.com with '/'
    s, n1 = re.subn(r'(https?://)?(www\.)?biasharabridges\.com/?', '/', s)
    replaced += n1

    # 4) Remove leftover cookieadmin 'Powered by' hrefs that may contain absolute urls (already handled above but ensure)
    s, n2 = re.subn(r'href="#""', 'href="#"', s)
    replaced += n2

    return s, replaced

def main():
    if not TEMPLATE.exists():
        print('templates/landing.html not found')
        return 1

    bak = backup(TEMPLATE)
    print('Backup created:', bak)

    original = TEMPLATE.read_text(encoding='utf-8')
    patched, count = patch_content(original)

    TEMPLATE.write_text(patched, encoding='utf-8')
    print(f'Patched {TEMPLATE} — replacements made: {count}')

    # Quick report: count remaining https:// occurrences except schema.org
    remaining = re.findall(r'https://(?!schema\.org)[^"\s]+', patched)
    print('Remaining external https:// (excluding schema.org):', len(remaining))
    if remaining:
        # show a few
        for u in list(dict.fromkeys(remaining))[:30]:
            print(' ', u)

    return 0

if __name__ == '__main__':
    raise SystemExit(main())
