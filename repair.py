#!/usr/bin/env python3
"""Allowlisted, auditable restart helper for the laurincov-pes agent."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent

def main():
    if len(sys.argv) != 2:
        print("usage: repair.py SERVICE_NAME", file=sys.stderr); return 2
    name = sys.argv[1]
    cfg = json.loads((ROOT / "endpoints.json").read_text())
    item = next((x for x in cfg.get("endpoints", []) if x["name"] == name), None)
    if not item or not item.get("managed") or not item.get("restart"):
        print(json.dumps({"ok": False, "reason": "service_not_allowlisted", "name": name})); return 3
    command = item["restart"]
    if command[:2] != ["docker", "restart"] or len(command) != 3 or any(c.startswith("-") for c in command):
        print(json.dumps({"ok": False, "reason": "command_rejected", "name": name})); return 4
    p = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=120)
    print(json.dumps({"ok": p.returncode == 0, "name": name, "command": command,
                      "returncode": p.returncode, "stdout": p.stdout[-2000:], "stderr": p.stderr[-2000:]}))
    return p.returncode
if __name__ == "__main__": sys.exit(main())
