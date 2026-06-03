import requests

BASE = 'http://localhost:5000'
passed, failed = [], []

def chk(name, payload, expect_http, expect_status=None):
    r = requests.post(f'{BASE}/api/trigger', json=payload)
    ok = r.status_code == expect_http
    if ok and expect_status and r.status_code == 200:
        ok = r.json().get('status') == expect_status
    tag = 'PASS' if ok else 'FAIL'
    (passed if ok else failed).append(name)
    if r.status_code == 200:
        d = r.json()
        extra = f"status={d.get('status')} risk={d.get('risk_level')} tvi={d.get('tvi_score')}"
    else:
        extra = f"http={r.status_code}"
    print(f"  {tag}  {name} | {extra}")

chk('safe txn manager 500',       {'event_type':'financial_txn','payload':{'user_id':'E202','amount':500},'mode':'minimum'},    200, 'Approved')
chk('block R001 employee 5000',   {'event_type':'financial_txn','payload':{'user_id':'E101','amount':5000},'mode':'minimum'},   200, 'Blocked')
chk('block R002 vendor financial',{'event_type':'financial_txn','payload':{'user_id':'V100','amount':100},'mode':'minimum'},    200, 'Blocked')
chk('block R004 unknown user',    {'event_type':'financial_txn','payload':{'user_id':'GHOST999','amount':50},'mode':'minimum'}, 200, 'Blocked')
chk('review R003 security level1',{'event_type':'security_alert','payload':{'user_id':'E101'},'mode':'minimum'},               200, 'Review')
chk('approved director security', {'event_type':'security_alert','payload':{'user_id':'E303'},'mode':'minimum'},               200, 'Approved')
chk('rule_engine policy_upload',  {'event_type':'policy_upload','payload':{'user_id':'E202'},'mode':'rule_engine'},             200)

# Validation tests
for label, payload, expected_http in [
    ('invalid mode -> 400',     {'event_type':'financial_txn','payload':{},'mode':'BADMODE'}, 400),
    ('missing event_type -> 400',{'payload':{},'mode':'minimum'}, 400),
]:
    r = requests.post(f'{BASE}/api/trigger', json=payload)
    ok = r.status_code == expected_http
    tag = 'PASS' if ok else 'FAIL'
    (passed if ok else failed).append(label)
    print(f"  {tag}  {label} | http={r.status_code}")

# Malformed body
r = requests.post(f'{BASE}/api/trigger', data='not json', headers={'Content-Type':'text/plain'})
ok = r.status_code == 400
tag = 'PASS' if ok else 'FAIL'
(passed if ok else failed).append('malformed body -> 400')
print(f"  {tag}  malformed body -> 400 | http={r.status_code}")

print()
print(f"POST /api/trigger: {len(passed)} passed, {len(failed)} failed")
if failed:
    print("FAILED:", failed)
