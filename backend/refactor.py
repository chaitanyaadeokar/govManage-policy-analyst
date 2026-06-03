import os
import re
import glob

def refactor_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace imports
    # from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace -> from llm_utils import get_groq_llm, safe_invoke
    content = re.sub(
        r'from langchain_huggingface import HuggingFaceEndpoint,\s*ChatHuggingFace',
        r'from llm_utils import get_groq_llm, safe_invoke',
        content
    )
    
    # 2. Replace llm instantiations
    # llm = ChatHuggingFace(llm=HuggingFaceEndpoint(...)) -> llm = get_groq_llm()
    content = re.sub(
        r'ChatHuggingFace\(llm=HuggingFaceEndpoint\([^)]+\)\)',
        r'get_groq_llm()',
        content
    )
    # also endpoint = HuggingFaceEndpoint(...); llm = ChatHuggingFace(llm=endpoint)
    content = re.sub(
        r'endpoint = HuggingFaceEndpoint\([^)]+\)\s*\n\s*llm = ChatHuggingFace\(llm=endpoint\)',
        r'llm = get_groq_llm()',
        content
    )
    
    # 3. Replace invoke
    # llm.invoke(messages) -> safe_invoke(llm, messages)
    content = re.sub(
        r'llm\.invoke\(\[([^\]]+)\]\)',
        r'safe_invoke(llm, [\1])',
        content
    )
    
    # Also in app.py there is `if not ChatHuggingFace:` check
    content = re.sub(r'if not ChatHuggingFace(?: or not os\.getenv\("[^"]+"\))?:', 'if False:', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Refactored {filepath}")

files = [
    'app.py',
    'tools.py',
    'reports.py',
    'email_service.py',
    'agents_micro/compliance/main.py',
    'agents_micro/risk_assessment/main.py',
    'agents_micro/policy_analyst/main.py',
    'agents_micro/decision_engine/main.py'
]

for file in files:
    if os.path.exists(file):
        refactor_file(file)
    else:
        print(f"File not found: {file}")
