# Quick Reference Card

One-page reference for common tasks and commands.

---

## 🚀 Quick Start

```bash
# Setup
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your GROQ_API_KEY

# Run tests
python test_agentic_system.py

# Start API
python api.py
# Visit: http://localhost:8000/docs
```

---

## 📡 API Endpoints

### Submit Event (Sync)
```bash
curl -X POST http://localhost:8000/api/v2/events/sync \
  -H "Content-Type: application/json" \
  -d '{"event_type":"financial_txn","payload":{"user_id":"E101","amount":1500}}'
```

### Submit Event (Async)
```bash
curl -X POST http://localhost:8000/api/v2/events \
  -H "Content-Type: application/json" \
  -d '{"event_type":"financial_txn","payload":{"user_id":"E101","amount":1500}}'
```

### Get Decision
```bash
curl http://localhost:8000/api/v2/events/{event_id}
```

### Get Analytics
```bash
curl http://localhost:8000/api/v2/analytics
```

### Health Check
```bash
curl http://localhost:8000/api/v2/health
```

---

## 🧪 Testing

```bash
# Full test suite
python test_agentic_system.py

# Single test
python -c "from agents import process_governance_event; \
  result = process_governance_event({'event_id':'test','event_type':'financial_txn','payload':{'user_id':'E101','amount':1500}}); \
  print(result)"

# API test
curl http://localhost:8000/api/v2/health
```

---

## 🗄️ Database

```bash
# Connect to MongoDB
mongo mongodb://localhost:27017

# Use database
use govmanage

# Check collections
show collections

# Query actions
db.governance_actions.find().limit(5)

# Count by status
db.governance_actions.countDocuments({"status": "Approved"})
```

---

## 🔧 Configuration

### Environment Variables (.env)
```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-120b
MONGO_URI=mongodb://127.0.0.1:27017
MONGO_DB_NAME=govmanage
API_PORT=8000
```

### Key Files
- `agentic_core/` - Core framework
- `api.py` - REST API
- `test_agentic_system.py` - Tests
- `database.py` - Data access

---

## 🤖 Agent Tools

### Policy Agent
- `get_compliance_policies()`
- `get_hard_rules()`
- `evaluate_rule_against_event()`
- `query_similar_past_decisions()`

### Compliance Agent
- `get_employee_info()`
- `evaluate_rule_against_event()`
- `check_cross_event_correlation()`

### Risk Agent
- `get_risk_parameters()`
- `check_user_behavior_anomaly()`
- `get_risk_baseline_for_event_type()`
- `query_similar_past_decisions()`

---

## 📊 Decision Framework

### Block Path
- Unknown user
- Hard rule violation
- High risk + compliance violation
- Suspicious correlation

### Review Path
- Medium-high risk
- Policy conflict
- Behavioral anomaly
- Conflicting signals

### Safe Path
- User authorized
- No violations
- Low risk
- No anomalies

---

## 🔍 Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u agentic-governance -n 50

# Check Python
python --version

# Check MongoDB
sudo systemctl status mongod
```

### API errors
```bash
# Check health
curl http://localhost:8000/api/v2/health

# Check logs
tail -f /var/log/agentic-governance/app.log
```

### Database issues
```bash
# Test connection
python -c "from database import db; print(db.count_actions())"

# Check MongoDB
mongo --eval "db.serverStatus().connections"
```

---

## 📈 Monitoring

### Key Metrics
- Decision latency: <10s
- Automation rate: >85%
- Accuracy: >90%
- Uptime: >99.5%

### Health Checks
```bash
# API health
curl http://localhost:8000/api/v2/health

# Service status
sudo systemctl status agentic-governance

# Database status
sudo systemctl status mongod
```

---

## 🚨 Emergency Commands

### Restart service
```bash
sudo systemctl restart agentic-governance
```

### View logs
```bash
sudo journalctl -u agentic-governance -f
```

### Rollback
```bash
sudo systemctl stop agentic-governance
cd /opt/agentic-governance
git checkout <previous-commit>
sudo systemctl start agentic-governance
```

### Database backup
```bash
mongodump --uri="mongodb://localhost:27017" --db=govmanage --out=/backup/
```

---

## 📚 Documentation

- **INDEX.md** - Documentation index
- **README.md** - User guide
- **ARCHITECTURE.md** - Technical details
- **DEPLOYMENT.md** - Deployment guide
- **EXECUTIVE_OVERVIEW.md** - Business case

---

## 💻 Development

### Run locally
```bash
python api.py
```

### Run with auto-reload
```bash
uvicorn api:app --reload
```

### Run tests
```bash
python test_agentic_system.py
```

### Check code
```bash
python -m py_compile agentic_core/**/*.py
```

---

## 🔐 Security

### Generate secret key
```python
import secrets
print(secrets.token_urlsafe(32))
```

### Check SSL
```bash
openssl s_client -connect governance.yourdomain.com:443
```

### View certificates
```bash
sudo certbot certificates
```

---

## 📞 Support

### Documentation
- Start: INDEX.md
- Quick: SUMMARY.md
- Deep: ARCHITECTURE.md

### Common Issues
- Service won't start → Check logs
- API errors → Check health endpoint
- Database errors → Check MongoDB status
- Slow responses → Check agent iterations

---

## ✅ Pre-Flight Checklist

Before deployment:
- [ ] MongoDB running
- [ ] .env configured
- [ ] Tests passing
- [ ] API responding
- [ ] Health check OK

---

**Keep this card handy for quick reference!**

**Full docs**: See INDEX.md  
**Questions**: Check README.md  
**Issues**: Review ARCHITECTURE.md
