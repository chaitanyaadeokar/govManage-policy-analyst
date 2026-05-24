# AI Policy Chat: Architecture & Implementation Guide

This document provides a technical summary of the `AiPolicyChat` component, how it integrates with the broader `govManage-policy-analyst` ecosystem, and critical edge-cases (fuckups) that the next agent should be aware of.

## 1. Overview
The AI Policy Chat is an interactive, conversational agent designed to rapidly draft custom governance and compliance policies through natural language. Unlike the massive batch-generation engine (`generate_policy_pack`), the chat provides a quick, iterative drafting experience where the user can request a policy and the AI responds with an interactive policy card.

## 2. Implementation Architecture

### Frontend (`AiPolicyChat.tsx`)
- **Location:** `frontend/src/components/AiPolicyChat.tsx`
- **Mechanism:** Provides a conversational UI communicating with the backend via WebSocket or REST (depending on current config) or directly to the `/api/chat` agent endpoints.
- **Interactive Forms:** The UI recognizes special XML-like tags (e.g., `<POLICY_CARD>{"id": "pol_123", "title": "..."}</POLICY_CARD>`) emitted by the backend agent and renders them as clickable React components (allowing instant viewing, downloading, and emailing of the generated policy).

### Backend Agent (`tools.py` & `agent_policy.py`)
- **Core Tool:** `trigger_policy_generation(topic, sector, additional_instructions, selected_frameworks, selected_risks)` inside `tools.py`.
- **Logic:**
  1. The agent fetches real controls from the DB for selected frameworks.
  2. It fetches actual risk descriptions/mitigations from the DB for selected risks.
  3. It constructs a massive, structured prompt asking the LLM (Llama 3.3 via Groq) to generate a professional markdown policy containing specific sections (Objective, Scope, Policy Statements, Procedures, Governance Structure, Enforcement, Review Cycle).
  4. It appends structured markdown tables for the **Compliance Control Matrix** and **Risk Mitigation Mapping** dynamically.
  5. It saves the resulting payload to MongoDB and emits the `<POLICY_CARD>` tag back to the frontend.

### PDF Generation (`report_pdf.py`)
- Standard policy packs use `build_policy_pack_pdf`.
- AI Chat policies (which are raw markdown, not complex JSON) use `build_markdown_policy_pdf()`.
- **Critical Capability:** `build_markdown_policy_pdf` features a custom state-machine parser that correctly identifies markdown tables (`|...|...|`) and horizontal rules (`---`) and natively renders them as ReportLab `Table` and `HRFlowable` objects.

## 3. Database Model & Policy Library Integration
- **Separation of Concerns:** 
  - Standard multi-agent generated policies go to `policy_packs` (complex JSON structure).
  - Chat-generated policies go to `policy_documents` (primarily raw markdown strings).
- **The Library Merge:** The Policy Library UI (`PolicyLibrary.tsx`) only fetches from `/api/policy-packs`. To make chat policies visible in the library, `app.py` intercepts the `GET /api/policy-packs` call and dynamically maps `policy_documents` into a mock `PolicyPack` shape (attaching fake 100% scores and a special `AI Chat` risk tag).
- **Endpoint Overloading:** The endpoints for `GET /api/policy-packs/<id>`, `DELETE /api/policy-packs/<id>`, and `GET /api/policy-packs/<id>/pdf` check if the ID starts with `pol_` (chat document) or `PACK-` (standard pack) and route to the correct DB collection and PDF generator accordingly.

## 4. Current / Recent "Fuckups" (Gotchas to Watch Out For)

If you are the next agent working on this, **READ THIS CAREFULLY**:

1. **The `<br>` Crash in ReportLab:**
   - *The Fuckup:* The LLM occasionally outputs raw `<br>` tags inside markdown tables. ReportLab's `paraparser` violently crashes with a syntax error if it sees unclosed XML tags.
   - *The Fix:* In `report_pdf.py` inside `build_markdown_policy_pdf`, always run `.replace("<br>", "<br/>")` on cell text before passing it to ReportLab `Paragraph` objects.
2. **Missing `created_at` Crash:**
   - *The Fuckup:* Older mock records in the DB had `created_at: null`. Python's `.sort()` crashed with `TypeError: '<' not supported between instances of 'NoneType' and 'NoneType'` in `/api/policy-packs`.
   - *The Fix:* Always use `.get("created_at") or ""` when sorting. Never assume a key exists *or* is non-null.
3. **The Boilerplate Hallucination:**
   - *The Fuckup:* The LLM loves to append useless metadata like "*Approved by Board of Directors*" or "*Effective Date: [Insert Date]*" at the bottom of the generated markdown policy.
   - *The Fix:* The prompt in `tools.py` has a strict, all-caps `CRITICAL REQUIREMENT` block explicitly banning these phrases and forcing it to end immediately after the Review Cycle section. If you edit the prompt, **do not remove this instruction**.
4. **Emailing Raw Markdown:**
   - *The Fuckup:* The email function originally dumped the raw markdown policy as HTML into the body of the email. It looked terrible and broke email clients.
   - *The Fix:* The `/api/policies/email/<id>` endpoint now calls `build_markdown_policy_pdf`, converts the policy to bytes, and sends a concise email with a professional `.pdf` file attached.
5. **Memory Issues:**
   - *The Fuckup:* Previously, chat history wasn't saving correctly because backend session management wasn't explicitly committing messages to MongoDB after every interaction. Ensure any new chat features write state immediately.
