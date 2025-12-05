import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / 'templates' / 'landing.html'
FONTS_CSS_DIR = ROOT / 'static' / 'landing' / 'wp-content' / 'uploads' / 'elementor' / 'google-fonts' / 'css'

def replace_in_template():
    txt = TEMPLATE.read_text(encoding='utf-8')

    # Replace protocol-relative and absolute biasharabridges.com asset URLs with {% static 'landing/...' %}
    pattern = re.compile(r'(["\'])(?:https?:)?//(?:www\.)?biasharabridges\.com(/[^"\'>\s]+)(["\'])')
    # First replace biasharabridges.com occurrences
    txt = pattern.sub(lambda m: m.group(1) + "{% static 'landing" + m.group(2) + "' %}" + m.group(3), txt)

    # Remove preconnects / dns-prefetch to external Google fonts (we'll use local fonts)
    txt = re.sub(r'<link[^>]+fonts\.googleapis\.com[^>]*>\s*', '', txt)
    txt = re.sub(r'<link[^>]+fonts\.gstatic\.com[^>]*>\s*', '', txt)
    txt = re.sub(r"<link[^>]+href=['\"][^'\"]*fonts\.googleapis\.com[^'\"]*['\"][^>]*>", '', txt)

    # Replace any remaining protocol-relative revslider or wp-content entries
    txt = re.sub(r"([\"'])(//biasharabridges\.com/[^\"'>\s]+)([\"'])",
                 lambda m: m.group(1) + "{% static 'landing" + m.group(2)[2:] + "' %}" + m.group(3), txt)

    # For feeds/wp-json/xmlrpc, replace with '#'
    txt = re.sub(r"https?://(?:www\.)?biasharabridges\.com/(?:feed/|comments/feed/|wp-json/|xmlrpc.php)", '#', txt)

    # Replace any remaining absolute google fonts link to local elementor CSS if present
    txt = re.sub(r'https?://fonts\.googleapis\.com[^\s>]*', '#', txt)

    TEMPLATE.write_text(txt, encoding='utf-8')
    print(f'Patched {TEMPLATE}')

def fix_font_css():
    if not FONTS_CSS_DIR.exists():
        print('No elementor google-fonts css dir found, skipping font CSS fixes.')
        return
    for css in FONTS_CSS_DIR.glob('*.css'):
        txt = css.read_text(encoding='utf-8')
        # Replace remote font URLs with local static path under /static/landing/fonts/
        txt = re.sub(r'https?://(?:www\.)?biasharabridges\.com/wp-content/uploads/elementor/google-fonts/fonts/','/static/landing/fonts/', txt)
        # Also replace any protocol-relative paths
        txt = re.sub(r'//(?:www\.)?biasharabridges\.com/wp-content/uploads/elementor/google-fonts/fonts/','/static/landing/fonts/', txt)
        css.write_text(txt, encoding='utf-8')
        print(f'Patched font CSS {css}')

if __name__ == '__main__':
    replace_in_template()
    fix_font_css()
