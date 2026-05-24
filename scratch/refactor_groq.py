import os
import re

def refactor_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Imports
    content = re.sub(
        r'from langchain_huggingface import HuggingFaceEndpoint,\s*ChatHuggingFace',
        r'from llm_utils import get_groq_llm, safe_invoke',
        content
    )
    
    # 2. Instantiations
    content = re.sub(
        r'ChatHuggingFace\(llm=HuggingFaceEndpoint\([^)]+\)\)',
        r'get_groq_llm()',
        content
    )
    content = re.sub(
        r'endpoint\s*=\s*HuggingFaceEndpoint\([^)]+\)\s*\n\s*llm\s*=\s*ChatHuggingFace\(llm=endpoint\)',
        r'llm = get_groq_llm()',
        content
    )
    
    # 3. Invokes
    content = re.sub(
        r'llm\.invoke\(\[([^\]]+)\]\)',
        r'safe_invoke(llm, [\1])',
        content
    )
    
    # 4. Remove 'if not ChatHuggingFace' checks
    content = re.sub(r'if not ChatHuggingFace(?: or not os\.getenv\("[^"]+"\))?:', 'if False:', content)
    content = re.sub(r'if ChatHuggingFace is not None and os\.getenv\("[^"]+"\):', 'if True:', content)
    
    # 5. Fix ChatGroq directly instantiated in app.py (from my previous run, though I reverted it)
    content = re.sub(
        r'ChatGroq\(model_name=os\.getenv\("[^"]+", "[^"]+"\)\)',
        r'get_groq_llm()',
        content
    )

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

# --- Specific fixes for app.py ---
with open('app.py', 'r', encoding='utf-8') as f:
    app_content = f.read()

# Add Step 5 to POLICY GENERATION WORKFLOW
step_4 = r"4. Once the user confirms, use the `trigger_policy_generation` tool to hand off the work to the background micro-agents. Pass the confirmed framework IDs and risk IDs to the tool.\\n\""
step_5 = r"4. Once the user confirms, use the `trigger_policy_generation` tool to hand off the work to the background micro-agents. Pass the confirmed framework IDs and risk IDs to the tool.\\n\"\n        \"   5. CRITICAL: When the `trigger_policy_generation` tool returns a success message containing a `<POLICY_CARD>` token, YOU MUST INCLUDE THAT EXACT `<POLICY_CARD>...` TOKEN IN YOUR FINAL RESPONSE! Do not strip it out, or the UI will fail to display the policy.\\n\""

app_content = app_content.replace(step_4, step_5)

# Add PDF & Email routes at the end before if __name__ == "__main__":
pdf_routes = """
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
import markdown

@app.route("/api/policies/download/<policy_id>", methods=["GET"])
def download_policy_pdf(policy_id):
    policy = db.db["policy_documents"].find_one({"policy_id": policy_id})
    if not policy:
        return jsonify({"error": "Policy not found"}), 404
        
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CustomNormal', parent=styles['Normal'], fontSize=11, spaceAfter=10))
    styles.add(ParagraphStyle(name='CustomTitle', parent=styles['Title'], fontSize=16, spaceAfter=20, textColor=colors.darkblue))
    styles.add(ParagraphStyle(name='CustomHeading2', parent=styles['Heading2'], fontSize=14, spaceBefore=15, spaceAfter=10, textColor=colors.black))
    
    story = []
    
    lines = policy.get("content", "").split("\\n")
    for line in lines:
        if line.startswith("# "):
            story.append(Paragraph(line[2:], styles['CustomTitle']))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], styles['CustomHeading2']))
        elif line.startswith("### "):
            story.append(Paragraph(line[4:], styles['Heading3']))
        elif line.strip() == "":
            story.append(Spacer(1, 10))
        else:
            # Simple bold parsing
            text = line.replace("**", "<b>", 1).replace("**", "</b>", 1)
            story.append(Paragraph(text, styles['CustomNormal']))
            
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{policy_id}.pdf"',
            "Content-Length": str(len(pdf_bytes))
        }
    )

@app.route("/api/policies/email/<policy_id>", methods=["POST"])
def email_policy(policy_id):
    policy = db.db["policy_documents"].find_one({"policy_id": policy_id})
    if not policy:
        return jsonify({"error": "Policy not found"}), 404
        
    try:
        from email_service import _send_email
        body = f"A new policy '{policy.get('title')}' has been generated.\\n\\n{policy.get('content')}"
        _send_email("New Policy Generated", body)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

"""

if "@app.route(\"/api/policies/download/<policy_id>\"," not in app_content:
    app_content = app_content.replace('if __name__ == "__main__":', pdf_routes + '\nif __name__ == "__main__":')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_content)
print("app.py specifics refactored")

