# Agentic AI Governance System

**Professional-grade autonomous multi-agent system for enterprise governance and compliance.**

## 🎯 What Makes This Truly Agentic

This system implements **genuine agentic AI** with:

### ✅ Autonomous Reasoning (ReAct Loops)
- Agents think, act, observe, and reason iteratively
- Not just prompt templates - actual multi-step reasoning chains
- Agents decide when to use tools and when they have enough information

### ✅ Real Tool Use
- Agents query databases, evaluate rules, detect anomalies
- Not hallucinating decisions - using real data sources
- Tools for: employee lookup, policy retrieval, rule evaluation, anomaly detection

### ✅ Multi-Agent Collaboration
- Specialized agents (Policy, Compliance, Risk) work in parallel
- Shared memory system for coordination
- Decision engine synthesizes findings through collaborative reasoning

### ✅ Learning & Memory
- **Episodic Memory**: Learns from past decisions
- **Semantic Memory**: Extracts patterns and baselines
- **Working Memory**: Coordinates current event processing
- Agents query similar past cases to inform decisions

### ✅ Anomaly Detection
- Behavioral analysis against user baselines
- Cross-event correlation detection
- Statistical anomaly identification (>2 std deviations)

### ✅ Self-Reflection
- Agents reflect on outcomes for continuous improvement
- Pattern extraction from decision history
- Risk baseline adaptation

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                      │
│              /api/v2/events, /api/v2/analytics              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Agentic Orchestrator                        │
│         Coordinates multi-agent collaboration                │
└─────┬──────────────────┬──────────────────┬─────────────────┘
      │                  │                  │
      ▼                  ▼                  ▼
┌──────────┐      ┌──────────┐      ┌──────────┐
│ Policy   │      │Compliance│      │   Risk   │
│ Analyst  │      │  Agent   │      │Assessment│
│  Agent   │      │          │      │  Agent   │
└────┬─────┘      └────┬─────┘      └────┬─────┘
     │                 │                  │
     │    ┌────────────▼──────────────┐   │
     └───►│   Shared Memory System    │◄──┘
          │  • Working Memory         │
          │  • Episodic Memory        │
          │  • Semantic Memory        │
          └────────────┬──────────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │   Decision Engine      │
          │   Synthesizes findings │
          └────────────┬───────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │  MongoDB + Audit Logs  │
          └────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- MongoDB running on localhost:27017 (or configure MONGO_URI)
- Groq API key

### Installation

```bash
# Clone repository
git clone <repo-url>
cd <repo-directory>

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### Configuration (.env)
```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
MONGO_URI=mongodb://127.0.0.1:27017
MONGO_DB_NAME=govmanage
API_PORT=8000
```

### Run Tests

```bash
python test_agentic_system.py
```

This will run 5 test scenarios demonstrating:
- Financial transaction approval
- Vendor blocking (rule violation)
- Security alert processing
- Unknown user blocking
- Manager authorization

### Start API Server

```bash
python api.py
```

API will be available at `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

---

## 📡 API Usage

### Submit Event (Async)

```bash
curl -X POST http://localhost:8000/api/v2/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "financial_txn",
    "payload": {
      "user_id": "E101",
      "amount": 1500,
      "vendor": "Acme Corp",
      "description": "Software purchase"
    }
  }'
```

Response:
```json
{
  "event_id": "uuid-here",
  "status": "processing",
  "message": "Event submitted successfully. Autonomous agents are analyzing.",
  "processing_mode": "async"
}
```

### Submit Event (Sync)

```bash
curl -X POST http://localhost:8000/api/v2/events/sync \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "financial_txn",
    "payload": {
      "user_id": "E202",
      "amount": 1500,
      "vendor": "Enterprise Software Inc"
    }
  }'
```

Response:
```json
{
  "event_id": "uuid-here",
  "event_type": "financial_txn",
  "status": "Approved",
  "action_taken": "Approved",
  "path_taken": "Safe Path",
  "risk_level": "Low",
  "tvi_score": 0.288,
  "reasoning": "User authorized, no policy violations, low risk",
  "timestamp": "2026-04-08T10:30:00",
  "confidence": "high"
}
```

### Get Decision

```bash
curl http://localhost:8000/api/v2/events/{event_id}
```

### Get Analytics

```bash
curl http://localhost:8000/api/v2/analytics
```

Response:
```json
{
  "total_events": 150,
  "approved": 95,
  "blocked": 20,
  "under_review": 35,
  "average_tvi": 0.425,
  "high_risk_percentage": 13.33
}
```

---

## 🤖 Agent Capabilities

### Policy Analyst Agent
**Tools:**
- `get_compliance_policies`: Fetch organizational policies
- `get_hard_rules`: Retrieve enforcement rules
- `evaluate_rule_against_event`: Test rules deterministically
- `query_similar_past_decisions`: Learn from precedent

**Reasoning:**
- Systematically evaluates all applicable policies
- Checks for conflicts and ambiguities
- Provides evidence-based recommendations

### Compliance Agent
**Tools:**
- `get_employee_info`: Verify identity and authorization
- `get_hard_rules`: Check authorization rules
- `evaluate_rule_against_event`: Verify permissions
- `check_cross_event_correlation`: Detect attack patterns

**Reasoning:**
- Verifies user identity and role
- Checks clearance levels
- Detects suspicious activity patterns
- Strict security-first approach

### Risk Assessment Agent
**Tools:**
- `get_risk_parameters`: Get TVI calculation parameters
- `check_user_behavior_anomaly`: Detect unusual behavior
- `get_risk_baseline_for_event_type`: Compare to historical norms
- `query_similar_past_decisions`: Learn from similar cases
- `check_cross_event_correlation`: Identify coordinated threats

**Reasoning:**
- Calculates TVI score: (Threat × Vulnerability × Impact) / 1000
- Applies risk multipliers for anomalies
- Compares against learned baselines
- Classifies risk level (Low/Medium/High)

### Decision Engine Agent
**Synthesis Logic:**
- Analyzes all agent findings
- Applies decision framework (Block/Review/Safe paths)
- Handles conflicting signals
- Provides audit trail
- Assigns confidence levels

---

## 📊 Decision Framework

### Block Path (Immediate Rejection)
- Unknown user (identity fraud)
- Hard rule violation with block action
- High risk + compliance violation
- Suspicious cross-event correlation

### Review Path (Human Escalation)
- Medium-high risk (TVI 0.5-0.75)
- Policy conflict without hard block
- Behavioral anomaly detected
- Conflicting agent recommendations

### Safe Path (Auto-Approve)
- User authorized
- No policy violations
- Low risk (TVI < 0.3)
- No anomalies detected

---

## 🧠 Memory & Learning

### Episodic Memory
- Stores past decisions and outcomes
- Enables case-based reasoning
- Supports "query similar cases" functionality

### Semantic Memory
- Extracts patterns from episodes
- Maintains risk baselines per event type
- Tracks fraud indicators
- Stores user behavior baselines

### Working Memory
- Coordinates current event processing
- Enables agent-to-agent communication
- Stores intermediate findings

---

## 🔧 Advanced Configuration

### Custom Agents
Extend `BaseAgenticAgent` to create specialized agents:

```python
from agentic_core.base_agent import BaseAgenticAgent

class MyCustomAgent(BaseAgenticAgent):
    def get_tools(self):
        return [my_tool_1, my_tool_2]
    
    def get_system_prompt(self):
        return "You are a specialized agent for..."
    
    def format_final_output(self, state):
        return {"custom": "output"}
```

### Custom Tools
Add tools using LangChain's `@tool` decorator:

```python
from langchain_core.tools import tool

@tool
def my_custom_tool(param: str) -> str:
    """Tool description for the agent."""
    # Implementation
    return result
```

---

## 📈 Production Deployment

### Scaling Considerations
- Run API with multiple workers: `uvicorn api:app --workers 4`
- Use Redis for shared memory in distributed setup
- Replace file-based queues with Kafka/RabbitMQ
- Add caching layer for database queries

### Monitoring
- Track agent reasoning iterations
- Monitor tool call patterns
- Alert on high block rates
- Track confidence score distributions

### Security
- Implement API authentication (JWT)
- Rate limiting per user/IP
- Encrypt sensitive payload data
- Audit log retention policies

---

## 🧪 Testing

Run comprehensive test suite:
```bash
python test_agentic_system.py
```

Test individual components:
```python
from agentic_core.agents.policy_agent import PolicyAnalystAgent

agent = PolicyAnalystAgent()
result = agent.process_event("test-001", event_data)
```

---

## 📝 Database Schema

### Collections

**employees**
```json
{
  "user_id": "E101",
  "role": "employee",
  "clearance": "level_1",
  "name": "Alice"
}
```

**policies**
```json
{
  "policy_id": "P001",
  "name": "Financial transactions > 1000 require manager approval",
  "sector": "Finance",
  "risk": "Medium"
}
```

**rule_engine**
```json
{
  "rule_code": "R001",
  "description": "Transactions above threshold require manager role",
  "condition": "amount_gt_role_required",
  "threshold": 1000,
  "required_role": "manager",
  "severity": "high",
  "action_on_fail": "block",
  "enabled": true
}
```

**governance_actions** (decisions)
```json
{
  "event_id": "uuid",
  "event_type": "financial_txn",
  "status": "Approved",
  "action_taken": "Approved",
  "path_taken": "Safe Path",
  "risk_level": "Low",
  "tvi_score": 0.288,
  "reasoning": "...",
  "audit_trace": [...],
  "timestamp": "2026-04-08T10:30:00"
}
```

---

## 🤝 Contributing

This is a professional-grade system. Contributions should maintain:
- Autonomous reasoning capabilities
- Tool-based decision making
- Comprehensive testing
- Clear documentation

---

## 📄 License

[Your License Here]

---

## 🎓 Key Differences from Non-Agentic Systems

| Feature | Non-Agentic (Old) | Agentic (New) |
|---------|-------------------|---------------|
| Decision Making | Hardcoded prompts | ReAct reasoning loops |
| Tool Use | None (hallucinated) | Real database queries |
| Learning | None | Episodic + semantic memory |
| Collaboration | File-based queues | Shared memory coordination |
| Anomaly Detection | None | Statistical + behavioral |
| Reasoning | Single LLM call | Multi-step iterative |
| Adaptability | Static | Learns from outcomes |

---

**Built with ❤️ for enterprise governance**
