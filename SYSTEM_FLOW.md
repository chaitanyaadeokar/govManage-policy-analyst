# System Flow Diagram

Visual representation of how the Agentic Governance System processes events.

---

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         EVENT SUBMISSION                         │
│                                                                  │
│  Client → POST /api/v2/events → {"event_type", "payload"}      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AGENTIC ORCHESTRATOR                          │
│                                                                  │
│  • Assigns event_id                                             │
│  • Initializes working memory                                   │
│  • Spawns 3 agents in parallel                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   POLICY     │ │  COMPLIANCE  │ │     RISK     │
    │   ANALYST    │ │    AGENT     │ │  ASSESSMENT  │
    │              │ │              │ │              │
    │  ReAct Loop  │ │  ReAct Loop  │ │  ReAct Loop  │
    │  (8 iters)   │ │  (8 iters)   │ │  (10 iters)  │
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
           │                │                │
           └────────────────┼────────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │      SHARED MEMORY            │
            │                               │
            │  • Working Memory             │
            │  • Agent Findings             │
            │  • Episodic Memory            │
            │  • Semantic Memory            │
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │    DECISION ENGINE AGENT      │
            │                               │
            │  • Synthesizes findings       │
            │  • Applies decision framework │
            │  • Resolves conflicts         │
            │  • Generates audit trail      │
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │      FINAL DECISION           │
            │                               │
            │  • Approved / Review / Block  │
            │  • Risk level & TVI score     │
            │  • Reasoning & audit trace    │
            │  • Confidence level           │
            └───────────────┬───────────────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
                ▼           ▼           ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ MongoDB  │ │  Memory  │ │  Client  │
        │  Persist │ │  Learn   │ │ Response │
        └──────────┘ └──────────┘ └──────────┘
```

---

## Detailed Agent ReAct Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT REASONING CYCLE                         │
└─────────────────────────────────────────────────────────────────┘

    START (Receive event data)
      │
      ▼
┌─────────────────────────────────────┐
│  1. THINK (Reasoning Node)          │
│                                     │
│  • Analyze current knowledge        │
│  • Identify information gaps        │
│  • Plan next action                 │
│  • Check shared memory              │
│  • Review past similar cases        │
└──────────────┬──────────────────────┘
               │
               ▼
         ┌─────────┐
         │ Enough  │───Yes───┐
         │  Info?  │         │
         └────┬────┘         │
              │ No           │
              ▼              │
┌─────────────────────────────────────┐
│  2. ACT (Tool Execution)            │
│                                     │
│  • Select appropriate tool          │
│  • Prepare parameters               │
│  • Execute tool call                │
│  • Wait for result                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  3. OBSERVE (Result Analysis)       │
│                                     │
│  • Receive tool output              │
│  • Parse and validate               │
│  • Extract key information          │
│  • Update understanding             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  4. REASON (Synthesis)              │
│                                     │
│  • Integrate new information        │
│  • Draw conclusions                 │
│  • Update confidence                │
│  • Decide next step                 │
└──────────────┬──────────────────────┘
               │
               │
               └──────► Back to THINK
                       (iterate 8-10x)
                            │
                            │ Max iterations
                            │ or confident
                            ▼
┌─────────────────────────────────────┐
│  5. FINALIZE (Output)               │
│                                     │
│  • Format findings                  │
│  • Store in shared memory           │
│  • Return to orchestrator           │
└─────────────────────────────────────┘
      │
      ▼
    END
```

---

## Policy Analyst Agent Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     POLICY ANALYST AGENT                         │
└─────────────────────────────────────────────────────────────────┘

Iteration 1: Gather Policies
  THINK: "I need to check relevant policies for this event"
  ACT: get_compliance_policies(sector="Finance")
  OBSERVE: Retrieved 3 policies
  REASON: "Policy P001 applies - transactions >$1000 need approval"

Iteration 2: Get Rules
  THINK: "I need specific enforcement rules"
  ACT: get_hard_rules()
  OBSERVE: Retrieved 4 rules, R001 is relevant
  REASON: "Rule R001: threshold=$1000, required_role=manager"

Iteration 3: Evaluate Rule
  THINK: "Does this event violate R001?"
  ACT: evaluate_rule_against_event("R001", payload)
  OBSERVE: {"passed": false, "reason": "Insufficient role"}
  REASON: "User is employee, needs manager - VIOLATION"

Iteration 4: Check Precedent
  THINK: "How were similar cases handled?"
  ACT: query_similar_past_decisions("financial_txn")
  OBSERVE: 4/5 similar cases were blocked
  REASON: "Consistent with precedent"

FINALIZE:
  {
    "policy_conflict": true,
    "violated_rules": ["R001"],
    "policy_analysis_score": 0.8,
    "recommendation": "block",
    "reasoning": "Amount exceeds threshold without required authorization"
  }
```

---

## Compliance Agent Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      COMPLIANCE AGENT                            │
└─────────────────────────────────────────────────────────────────┘

Iteration 1: Verify Identity
  THINK: "First, verify this user exists"
  ACT: get_employee_info("E101")
  OBSERVE: {"exists": true, "role": "employee", "clearance": "level_1"}
  REASON: "User exists with employee role and level 1 clearance"

Iteration 2: Check Authorization
  THINK: "Is this user authorized for this action?"
  ACT: evaluate_rule_against_event("R001", payload)
  OBSERVE: {"passed": false, "action": "block"}
  REASON: "Authorization failed - insufficient role"

Iteration 3: Check Activity Pattern
  THINK: "Is there suspicious activity?"
  ACT: check_cross_event_correlation("E101", 24)
  OBSERVE: {"correlation_detected": false, "event_count": 3}
  REASON: "Normal activity pattern - no red flags"

FINALIZE:
  {
    "user_authorized": false,
    "user_exists": true,
    "user_role": "employee",
    "compliance_violation": "Insufficient role for transaction amount",
    "suspicious_activity": false,
    "recommendation": "block"
  }
```

---

## Risk Assessment Agent Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   RISK ASSESSMENT AGENT                          │
└─────────────────────────────────────────────────────────────────┘

Iteration 1: Get Base Parameters
  THINK: "Calculate base TVI score"
  ACT: get_risk_parameters("financial_txn")
  OBSERVE: {"threat": 0.8, "vulnerability": 0.4, "impact": 0.9}
  REASON: "base_tvi = (0.8 * 0.4 * 0.9) / 1000 = 0.288"

Iteration 2: Check Anomalies
  THINK: "Is this behavior unusual for this user?"
  ACT: check_user_behavior_anomaly("E101", "financial_txn", 1500)
  OBSERVE: {"anomaly_detected": false, "baseline_avg": 1200}
  REASON: "Amount within normal range for this user"

Iteration 3: Compare Baseline
  THINK: "How does this compare to historical norms?"
  ACT: get_risk_baseline_for_event_type("financial_txn")
  OBSERVE: {"avg_tvi": 0.35, "sample_size": 150}
  REASON: "Current TVI (0.288) below average - lower risk"

Iteration 4: Check Correlation
  THINK: "Any coordinated attack patterns?"
  ACT: check_cross_event_correlation("E101", 24)
  OBSERVE: {"correlation_detected": false}
  REASON: "No suspicious patterns detected"

FINALIZE:
  {
    "tvi_score": 0.288,
    "risk_level": "Low",
    "base_tvi": 0.288,
    "anomaly_detected": false,
    "recommendation": "approve"  # From risk perspective
  }
```

---

## Decision Engine Synthesis

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECISION ENGINE AGENT                         │
└─────────────────────────────────────────────────────────────────┘

INPUT: All agent findings from shared memory

ANALYSIS:
  Policy Agent:
    ✗ policy_conflict = true
    ✗ violated_rules = ["R001"]
    → Recommendation: BLOCK

  Compliance Agent:
    ✗ user_authorized = false
    ✗ compliance_violation = "Insufficient role"
    → Recommendation: BLOCK

  Risk Agent:
    ✓ tvi_score = 0.288 (Low)
    ✓ anomaly_detected = false
    → Recommendation: APPROVE

DECISION LOGIC:
  1. Check blocking conditions:
     - Hard rule violation? YES (R001)
     - User unauthorized? YES
     → BLOCK PATH

  2. Risk consideration:
     - Risk is low, BUT hard rules override
     - Policy violations are absolute

  3. Confidence:
     - All agents agree on facts
     - Clear rule violation
     → HIGH confidence

FINAL DECISION:
  {
    "path_taken": "Block Path",
    "action_taken": "Auto Blocked",
    "status": "Blocked",
    "risk_level": "Low",
    "tvi_score": 0.288,
    "reasoning": "Transaction amount $1500 exceeds $1000 threshold. 
                  Rule R001 requires manager role, but user has employee role.",
    "confidence": "high",
    "audit_trace": [
      "BLOCK: Hard rule violations detected: ['R001']",
      "Policy: conflict=true, violated_rules=1, rec=block",
      "Compliance: authorized=false, violation=true, rec=block",
      "Risk: level=Low, TVI=0.288, anomaly=false, rec=approve",
      "Decision: Block Path -> Auto Blocked"
    ]
  }
```

---

## Memory & Learning Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    MEMORY & LEARNING SYSTEM                      │
└─────────────────────────────────────────────────────────────────┘

DURING PROCESSING:
  Working Memory (Event-Scoped)
    ↓
  Store agent findings as they complete
    ↓
  Enable agent collaboration via shared context

AFTER DECISION:
  Episodic Memory
    ↓
  Store complete decision episode:
    • Event details
    • All agent findings
    • Final decision
    • Timestamp
    ↓
  Pattern Extraction
    ↓
  Semantic Memory
    • Update risk baselines
    • Track user behavior patterns
    • Identify fraud indicators
    • Learn policy patterns

FUTURE EVENTS:
  Query Similar Cases
    ↓
  Retrieve relevant episodes from episodic memory
    ↓
  Apply learned patterns from semantic memory
    ↓
  Detect anomalies against baselines
    ↓
  Improve decision accuracy over time
```

---

## Complete End-to-End Example

```
TIME: 0s
  Client submits: POST /api/v2/events/sync
  {
    "event_type": "financial_txn",
    "payload": {"user_id": "E101", "amount": 1500}
  }

TIME: 0.1s
  Orchestrator:
    • Assigns event_id: "evt_12345"
    • Initializes working memory
    • Spawns 3 agents in parallel threads

TIME: 0.1s - 6s (PARALLEL)
  Policy Agent: 4 iterations, 3 tool calls → BLOCK
  Compliance Agent: 3 iterations, 3 tool calls → BLOCK
  Risk Agent: 4 iterations, 4 tool calls → APPROVE (low risk)

TIME: 6s
  All agents complete, findings in shared memory

TIME: 6s - 8s
  Decision Engine:
    • Reads all findings
    • Applies decision framework
    • Synthesizes: BLOCK (rule violation overrides low risk)
    • Generates audit trail

TIME: 8s
  Persistence:
    • Save to MongoDB
    • Update episodic memory
    • Extract patterns to semantic memory
    • Cleanup working memory

TIME: 8.1s
  Response to client:
  {
    "event_id": "evt_12345",
    "status": "Blocked",
    "action_taken": "Auto Blocked",
    "reasoning": "Rule R001 violation...",
    "confidence": "high"
  }

TOTAL TIME: 8.1 seconds
```

---

**This flow demonstrates the complete autonomous reasoning process from event submission to final decision.**
