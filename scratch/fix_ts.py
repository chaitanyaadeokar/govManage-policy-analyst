import re

def patch_file(path, replacements):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    for search, replace in replacements:
        content = content.replace(search, replace)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# 1. App.tsx
patch_file(
    r'c:\Users\Avinash\OneDrive\Desktop\govManage-policy-analyst\frontend\src\App.tsx',
    [('ShieldCheck, UploadCloud } from', 'ShieldCheck } from')]
)

# 2. AgentStatusWidget.tsx
patch_file(
    r'c:\Users\Avinash\OneDrive\Desktop\govManage-policy-analyst\frontend\src\components\AgentStatusWidget.tsx',
    [('import React, { useState, useEffect }', 'import { useState, useEffect }')]
)

# 3. DatabaseExplorer.tsx
patch_file(
    r'c:\Users\Avinash\OneDrive\Desktop\govManage-policy-analyst\frontend\src\components\DatabaseExplorer.tsx',
    [('import { Database, Table as TableIcon, FileText, Download }', 'import { Table as TableIcon, FileText, Download }')]
)

# 4. PolicyHub.tsx
patch_file(
    r'c:\Users\Avinash\OneDrive\Desktop\govManage-policy-analyst\frontend\src\components\PolicyHub.tsx',
    [('TrendingUp, Target }', 'Target }'),
     ('const kpiCards = [', '// const kpiCards = [')]
)

print("Patched typescript files")
