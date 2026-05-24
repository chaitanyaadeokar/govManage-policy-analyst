import os
import re

files = [
    'agents_micro/compliance/main.py',
    'agents_micro/risk_assessment/main.py',
    'agents_micro/policy_analyst/main.py',
    'agents_micro/decision_engine/main.py'
]

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Imports
    # Remove old import
    content = re.sub(r'from langchain_huggingface import HuggingFaceEndpoint,\s*ChatHuggingFace\n?', '', content)
    
    # 2. Add llm_utils import AFTER sys.path.append(ROOT_DIR)
    sys_path_line = "sys.path.append(ROOT_DIR)"
    if sys_path_line in content and "from llm_utils import get_groq_llm, safe_invoke" not in content:
        content = content.replace(sys_path_line, sys_path_line + "\nfrom llm_utils import get_groq_llm, safe_invoke")

    # 3. Instantiations
    content = re.sub(r'ChatHuggingFace\(llm=HuggingFaceEndpoint\([^)]+\)\)', 'get_groq_llm()', content)
    content = re.sub(r'endpoint\s*=\s*HuggingFaceEndpoint\([^)]+\)\s*\n\s*llm\s*=\s*ChatHuggingFace\(llm=endpoint\)', 'llm = get_groq_llm()', content)
    
    # 4. Invokes
    content = re.sub(r'llm\.invoke\(\[([^\]]+)\]\)', r'safe_invoke(llm, [\1])', content)
    
    # 5. Remove 'if not ChatHuggingFace' checks
    content = re.sub(r'if not ChatHuggingFace(?: or not os\.getenv\("[^"]+"\))?:', 'if False:', content)
    content = re.sub(r'if ChatHuggingFace is not None and os\.getenv\("[^"]+"\):', 'if True:', content)

    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Refactored {file}")
