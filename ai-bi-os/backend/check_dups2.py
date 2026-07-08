import os, ast
t = {}
p = 'app/models'
for f in os.listdir(p):
    if not f.endswith('.py'): continue
    with open(os.path.join(p, f), 'r', encoding='utf-8') as file:
        content = file.read()
        for node in ast.parse(content).body:
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if getattr(base, 'id', '') == 'Base':
                        m = node.name
                        if m in t:
                            print(f"Duplicate class {m} in {f} and {t[m]}")
                        else:
                            t[m] = f
