from email_service import is_configured, get_smtp_config, get_default_recipients, send_email, compose_weekly_report_data

print("=== EMAIL SERVICE TESTS ===")

# 1. Config check
cfg = get_smtp_config()
print(f"\n[1] SMTP Config:")
print(f"    Host: {cfg['host']}")
print(f"    Port: {cfg['port']}")
print(f"    User: {cfg['user']}")
print(f"    Password set: {bool(cfg['password'])}")
print(f"    Configured: {is_configured()}")
assert is_configured(), "SMTP not configured!"
print("    PASS SMTP configured")

# 2. Recipients
recips = get_default_recipients()
print(f"\n[2] Recipients: {recips}")
assert len(recips) > 0, "No recipients!"
print("    PASS recipients found")

# 3. Weekly report data
print(f"\n[3] Composing weekly report data...")
data = compose_weekly_report_data()
print(f"    Generated at: {data['generated_at']}")
print(f"    Total packs: {data['total_policy_packs']}")
print(f"    High risks: {data['high_risk_count']}")
print(f"    Active docs: {data['active_documents']}")
print(f"    Actions reviewed: {data['actions_reviewed']}")
print("    PASS report data composed")

# 4. Send test email
print(f"\n[4] Sending live test email to {recips}...")
result = send_email(
    to_addrs=recips,
    subject="[govManage Test] Production Readiness Check",
    html_body="<h2>govManage Test Email</h2><p>If you see this, SMTP is working correctly. This was sent from the production readiness test suite.</p>",
    text_body="govManage SMTP test passed. Production readiness check."
)
print(f"    Result: {result}")
if result.get('ok'):
    print("    PASS Email sent successfully!")
else:
    print(f"    FAIL Email failed: {result.get('error')}")
