import os

for root, dirs, files in os.walk('.'):
    if 'coda_venv' in root or '.git' in root:
        continue
    for file in files:
        if file == 'models.py':
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if 'get_user_model()' in content:
                    # Comment out lines assigning get_user_model globally
                    lines = content.splitlines()
                    new_lines = []
                    modified = False
                    for line in lines:
                        if 'get_user_model()' in line and not line.strip().startswith('#'):
                            new_lines.append('# ' + line + '  # [Fixed global call]')
                            modified = True
                        else:
                            new_lines.append(line)
                    
                    if modified:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(new_lines) + '\n')
                        print(f'Successfully cleaned: {path}')
            except Exception as e:
                print(f'Error reading {path}: {e}')

print('Cleanup complete!')
