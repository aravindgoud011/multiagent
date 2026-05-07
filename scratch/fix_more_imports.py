import os

routes_dir = r'c:\Users\aravi\Desktop\project\smart_retail\app\backend\routes'
for filename in os.listdir(routes_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(routes_dir, filename)
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Fix Agents imports
        new_content = content.replace('from ..agents.', 'from agents.')
        # Fix RAG imports
        new_content = new_content.replace('from ..rag.', 'from rag.')
        
        if new_content != content:
            with open(filepath, 'w') as f:
                f.write(new_content)
            print(f"Updated imports in {filename}")
