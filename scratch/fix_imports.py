import os

files = [
    'email_service.py',
    'reports.py',
    'agents_micro/compliance/main.py',
    'agents_micro/risk_assessment/main.py',
    'agents_micro/policy_analyst/main.py',
    'agents_micro/decision_engine/main.py'
]

for file in files:
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'safe_invoke' in content and 'from llm_utils import' not in content:
            content = 'from llm_utils import get_groq_llm, safe_invoke\n' + content
            with open(file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Added import to {file}")
