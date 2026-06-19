"""
Run a Vapi test suite and print pass/fail per test with the grader's reasoning.

Usage:
  VAPI_API_KEY=... TEST_SUITE_ID=... uv run python run_evals.py
  VAPI_API_KEY=... TEST_SUITE_ID=... RUN_ID=... uv run python run_evals.py   # poll existing run
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

VAPI = "https://api.vapi.ai"
KEY = os.environ.get("VAPI_API_KEY")
SID = os.environ.get("TEST_SUITE_ID")
RUN_ID = os.environ.get("RUN_ID")
if not (KEY and SID):
    sys.exit("Set VAPI_API_KEY and TEST_SUITE_ID.")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def http(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(VAPI + path, data=data, method=method,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode()[:400]); raise


def truthy_pass(result_obj):
    # scorers report results; treat presence of a truthy pass/result as success
    for key in ("passed", "result", "success", "score"):
        if key in result_obj:
            v = result_obj[key]
            if isinstance(v, bool): return v
            if isinstance(v, str): return v.lower() in ("pass", "passed", "true", "success")
            if isinstance(v, (int, float)): return v >= 0.5
    return None


def main():
    run_id = RUN_ID or http(f"/test-suite/{SID}/run", "POST", {})["id"]
    print(f"Run: {run_id}")

    last = None
    for _ in range(120):  # up to ~10 min
        run = http(f"/test-suite/{SID}/run/{run_id}")
        status = run.get("status")
        if status != last:
            print(f"  status: {status}")
            last = status
        if status in ("completed", "failed", "ended", "error"):
            break
        time.sleep(5)

    results = run.get("testResults") or run.get("results") or []
    print(f"\n=== Results ({len(results)} tests) ===")
    npass = 0
    for r in results:
        name = r.get("name") or (r.get("test") or {}).get("name") or r.get("testId", "?")
        scorers = r.get("scorerResults") or r.get("scorers") or []
        verdicts = [truthy_pass(s) for s in scorers]
        ok = all(v is True for v in verdicts) if verdicts else None
        npass += 1 if ok else 0
        mark = "PASS" if ok else ("FAIL" if ok is False else "??")
        print(f"\n[{mark}] {name}")
        for s in scorers:
            reason = s.get("reasoning") or s.get("reason") or s.get("rationale") or ""
            if reason:
                print("   reason:", reason[:300])

    if results:
        print(f"\n{npass}/{len(results)} passed.")
    else:
        print("No per-test results in payload yet. Full run object:")
        print(json.dumps(run, indent=2)[:1500])
    print(f"\nDashboard: https://dashboard.vapi.ai/test/{SID}")


if __name__ == "__main__":
    main()
