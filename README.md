# laurincov-pes

Deterministic endpoint watchdog written in Python. Probes registered endpoints (HTTP, MySQL) on a schedule. When new failures appear, it can optionally invoke a Hermes agent profile for diagnosis and automated repair via `repair.py`.

## Features

- **Deterministic probes**: HTTP/HTTPS (with latency) and MySQL handshake checks
- **State tracking**: Persists failure state in `watchdog-state.json`
- **Report generation**: Outputs `watchdog-report.json` consumed by dashboards
- **Hermes escalation**: On new failures, spawns a Hermes agent with diagnostic prompt
- **Safe repairs**: Allowed repairs listed in `endpoints.json` executed via `repair.py`
- **Pause support**: Endpoints can be marked `paused: true` to skip checks
- **Cron-friendly**: Runs as a standalone script, exits with code 1 if any OFFLINE

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  laurincov-pes (Python script)                                 │
│  ├── endpoints.json          → Registry of endpoints to probe  │
│  ├── watchdog.py             → Main probe logic                │
│  ├── mysql_health.py         → MySQL handshake probe           │
│  ├── repair.py               → Allowlisted restart commands    │
│  ├── watchdog-state.json     → Persistent failure state        │
│  └── watchdog-report.json    → Latest report for dashboards    │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
   ┌───────────────┐
   │  Hermes Agent │  (only on NEW failures)
   │  (profile:    │
   │  laurincov-   │
   │  pes)         │
   └───────────────┘
```

## Endpoint Registry (`endpoints.json`)

```json
{
  "version": 1,
  "endpoints": [
    {
      "name": "OpenViking",
      "url": "http://127.0.0.1:1933/health",
      "managed": true
    },
    {
      "name": "kalixtDB",
      "url": "mysql://192.168.253.42:3307",
      "scheme": "mysql",
      "managed": false
    },
    {
      "name": "Peppol features",
      "url": "http://127.0.0.1:10001/",
      "managed": true,
      "restart": ["docker", "restart", "peppol-features"]
    },
    {
      "name": "Open WebUI",
      "url": "http://127.0.0.1:3080/",
      "managed": true,
      "paused": true
    }
  ]
}
```

Fields:
- `name` — unique identifier
- `url` — HTTP/HTTPS URL or `mysql://host:port`
- `scheme` — `http`, `https`, or `mysql` (auto-detected from URL if omitted)
- `managed` — whether Hermes can attempt repairs
- `paused` — skip this endpoint
- `restart` — allowlisted repair command (executed via `repair.py NAME`)
- `ai_manager` — endpoint managed by AI GPU Manager (informational)

## Installation

```bash
git clone https://github.com/Rugents-masterpiece/laurincov-pes.git
cd laurincov-pes

# Run manually
python3 watchdog.py

# Run check-only (no state update, no Hermes)
python3 watchdog.py --check-only
```

## Cron / Hermes Integration

Add to Hermes cron (runs every 15 min):

```json
{
  "name": "Laurincov pes – deterministický watchdog",
  "script": "laurincov-pes-watchdog.py",
  "schedule": "every 15m",
  "no_agent": true
}
```

The script `laurincov-pes-watchdog.py` is the cron wrapper that:
1. Runs `watchdog.py`
2. Captures stdout (the JSON report)
3. On new failures, invokes Hermes agent with diagnostic prompt

## Repair System

`repair.py` provides safe, allowlisted restarts:

```bash
# List available repairs
python3 repair.py --list

# Execute repair for a specific endpoint
python3 repair.py "Peppol features"
```

Only endpoints with a `restart` array in `endpoints.json` can be repaired.

## Output Files

| File | Purpose |
|------|---------|
| `watchdog-report.json` | Latest full report (consumed by dash-local-route) |
| `watchdog-state.json` | Persistent failure state (tracks recidivism) |
| `endpoints.json` | Registry (source of truth) |

## Report Format (`watchdog-report.json`)

```json
{
  "project": "laurincov-pes",
  "agent": "laurincov-pes",
  "checked_at": "2026-10-30T17:13:49Z",
  "online": 10,
  "offline": 13,
  "paused": 2,
  "results": [
    {
      "name": "OpenViking",
      "url": "http://127.0.0.1:1933/health",
      "status": "ONLINE",
      "http_status": 200,
      "latency_ms": 2,
      "managed": true
    }
  ],
  "stt_stack": { "identified": "WhisperX/KInIT", "worker_script": "whisperx_worker.py" }
}
```

## Security

- No credentials in repository
- `endpoints.json` contains only public URLs (no tokens)
- MySQL probes use handshake only (no auth)
- Hermes escalation uses existing authenticated session

## License

MIT
