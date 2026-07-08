import os, re
t = {}
p = 'app/models'
for f in os.listdir(p):
    if not f.endswith('.py'): continue
    with open(os.path.join(p, f), 'r', encoding='utf-8') as file:
        content = file.read()
        for m in re.findall(r'__tablename__\s*=\s*[\'"]([^\'"]+)[\'"]', content):
            if m in t:
                print(f"Duplicate table {m} in {f} and {t[m]}")
            else:
                t[m] = f
