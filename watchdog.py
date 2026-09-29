#!/usr/bin/env python3
"""Deterministic endpoint probe; invokes Hermes only when a failure appears."""
from __future__ import annotations
import json, os, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
try:
    sys.path.insert(0, str(ROOT))
    import stt_identity
except Exception:
    stt_identity = None

REGISTRY = ROOT / "endpoints.json"
STATE = ROOT / "watchdog-state.json"
REPORT = ROOT / "watchdog-report.json"
AGENT = "laurincov-pes"
TIMEOUT = 3


def load(path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def probe(item):
    started = time.perf_counter()
    req = urllib.request.Request(item["url"], headers={"User-Agent": "laurincov-pes-watchdog/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return {"status": "ONLINE" if r.status < 500 else "OFFLINE", "http_status": r.status,
                    "latency_ms": round((time.perf_counter()-started)*1000)}
    except urllib.error.HTTPError as e:
        return {"status": "ONLINE" if e.code < 500 else "OFFLINE", "http_status": e.code,
                "latency_ms": round((time.perf_counter()-started)*1000), "reason": "HTTPError"}
    except Exception as e:
        return {"status": "OFFLINE", "http_status": None, "latency_ms": None,
                "reason": type(e).__name__}


def main():
    cfg = load(REGISTRY, {})
    old = load(STATE, {"failed": []})
    results = []
    for item in cfg.get("endpoints", []):
        result = {"name": item["name"], "url": item["url"], "managed": item.get("managed", False)}
        if item.get("paused"):
            result["status"] = "PAUSED"
            results.append(result)
            continue
        result.update(probe(item))
        if item.get("ai_manager"):
            result["state"] = result["status"]
        results.append(result)
    failed = [r["name"] for r in results if r["status"] == "OFFLINE"]
    new_failures = sorted(set(failed) - set(old.get("failed", [])))
    state = {"failed": sorted(failed), "last_check": int(time.time())}
    STATE.write_text(json.dumps(state, indent=2) + "\n")
    stt = stt_identity.stt_stack() if stt_identity else ("unknown", "unknown")
    report = {"project": "laurincov-pes", "agent": AGENT, "online": sum(r["status"] == "ONLINE" for r in results),
              "offline": len(failed), "paused": sum(r["status"] == "PAUSED" for r in results),
              "stt_stack": {"worker_script": stt[0], "identified": stt[1]},
              "new_failures": new_failures, "results": results}
    if new_failures:
        prompt = ("Projekt laurincov-pes hlási zlyhané endpointy. Pracuj v " + str(ROOT) +
                  ". Diagnostikuj iba zlyhané služby podľa endpoints.json. Použi dôkazy z reálnych read-only kontrol. "
                  "Ak je v registri bezpečný restart príkaz, môžeš ho vykonať výhradne cez repair.py NÁZOV; potom endpoint znovu over. "
                  "Qwen Prisma neopravuj cez seba, ak práve tento endpoint zlyhal. Nemeň registry ani nespúšťaj neallowlistované príkazy. "
                  "Vráť stručný PASS/FAIL report po slovensky.\n\nVýsledky:\n" + json.dumps(report, ensure_ascii=False))
        try:
            completed = subprocess.run(["hermes", "-p", AGENT, "chat", "-q", prompt], cwd=ROOT,
                                       text=True, capture_output=True, timeout=240)
            report["agent_exit_code"] = completed.returncode
            report["agent_output"] = (completed.stdout + completed.stderr)[-12000:]
        except Exception as e:
            report["agent_error"] = type(e).__name__ + ": " + str(e)
    report["checked_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    temporary = REPORT.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(temporary, REPORT)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
