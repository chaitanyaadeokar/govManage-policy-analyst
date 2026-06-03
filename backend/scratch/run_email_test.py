import sys
sys.path.insert(0, '.')
from email_service import is_configured, get_smtp_config, get_default_recipients, send_email, compose_weekly_report_data

print("=== EMAIL SERVICE TESTS ===")
cfg = get_smtp_config()
host = cfg["host"]
user = cfg["user"]
conf = is_configured()
print("SMTP Host:", host)
print("User:", user)
print("Configured:", conf)

recips = get_default_recipients()
print("Recipients:", recips)

data = compose_weekly_report_data()
packs = data["total_policy_packs"]
high = data["high_risk_count"]
docs = data["active_documents"]
print("Report data - packs:", packs, "high_risks:", high, "docs:", docs)

print("Sending test email...")
result = send_email(
    to_addrs=recips,
    subject="[govManage Test] Production Readiness Check",
    html_body="<h2>govManage Test Email</h2><p>SMTP is working correctly.</p>",
    text_body="govManage SMTP test passed."
)
ok = result.get("ok")
print("Result:", result)
if ok:
    print("PASS Email sent successfully!")
else:
    print("FAIL Email failed:", result.get("error"))
