import os

routes_dir = r'c:\Users\aravi\Desktop\project\smart_retail\app\backend\routes'
for filename in os.listdir(routes_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(routes_dir, filename)
        with open(filepath, 'r') as f:
            content = f.read()
        
        new_content = content.replace('from ..utils.helpers', 'from utils.helpers')
        
        if new_content != content:
            with open(filepath, 'w') as f:
                f.write(new_content)
            print(f"Updated {filename}")
