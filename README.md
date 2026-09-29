# laurincov-pes

Deterministic 15-minute endpoint watchdog with conditional Hermes/Qwen analysis.

Flow:

1. `watchdog.py` reads `endpoints.json` and performs HTTP checks without an LLM.
2. Healthy runs emit JSON and exit 0.
3. A newly detected failure invokes Hermes profile `laurincov-pes`.
4. The profile diagnoses the failed service and may use `repair.py SERVICE_NAME` for an exact allowlisted Docker restart.
5. The watchdog keeps incident state in `watchdog-state.json` and does not re-invoke the agent for an unchanged failure.

The Qwen endpoint is diagnosis-only: if Qwen itself is down, this profile cannot use Qwen to repair it.
