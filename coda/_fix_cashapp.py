import re

path = r'investing\templates\investing\shareholders\shareholders_deposit_cashapp.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# The file now has TWO closing script+endblock regions.
# We want to keep everything up to and including the FIRST </script>
# then immediately append {% endblock %} and nothing else.
# The first good </script> closes our new clean block.

# Find the first occurrence of  })();\n</script>
first_close = content.find('})();\n</script>')
if first_close == -1:
    print('ERROR: Could not find first closing })();')
else:
    # Keep everything up to and including </script>, then add endblock
    good_part = content[:first_close + len('})();\n</script>')]
    good_part += '\n{% endblock %}\n'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(good_part)
    print(f'Done. File now ends at line ~{good_part.count(chr(10))}')
    # Verify no Django tags inside <script> blocks
    scripts = re.findall(r'<script>(.*?)</script>', good_part, re.DOTALL)
    has_tags = any('{%' in s or '{{' in s for s in scripts)
    print('Django tags inside <script>:', has_tags)
