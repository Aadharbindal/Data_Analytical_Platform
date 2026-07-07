import os
import re
from collections import defaultdict

table_map = defaultdict(list)
for f in os.listdir('app/models'):
    if not f.endswith('.py'):
        continue
    text = open(f'app/models/{f}').read()
    for m in re.finditer(r'__tablename__\s*=\s*["\'](.+?)["\']', text):
        table_map[m.group(1)].append(f)

dupes = {k: v for k, v in table_map.items() if len(v) > 1}
for tbl, files in sorted(dupes.items()):
    print('DUPLICATE: ' + tbl + '  FILES: ' + str(files))
print('Total tables: ' + str(len(table_map)) + ', Duplicates: ' + str(len(dupes)))
