# Service Level Indicators (SLI) & Objectives (SLO)

## Definitions

### SLI (Service Level Indicator)
Metrics that directly measure the user's experience.
1. **Availability:** (Total Successful Requests / Total Requests) * 100
2. **Latency:** p95 response time for the `/chat` endpoint.
3. **Error Rate:** Rate of HTTP 5xx errors per minute.
4. **AI Quality:** Ratio of user feedback (👍 vs 👎) and internal RAGAS evaluations.

### SLO (Service Level Objective)
The hard thresholds we commit to maintaining for enterprise SLAs.
1. **Availability:** 99.5% (Max allowable downtime: 3.6 hours/month).
2. **Latency:** p95 < 10 seconds for standard chat.
3. **Error Rate:** < 0.5% global API failures.
4. **Ingestion Success:** > 98% of all document uploads process without crashing.

## Error Budget Policy

If the monthly Error Budget (the 0.5% downtime allowance) is:
- **50% Depleted:** A warning is sent to the engineering team.
- **75% Depleted:** **Feature Freeze**. All deployments of new features are halted. Engineering shifts 100% focus to reliability and bug fixing.
- **100% Depleted:** Incident Response declared. Post-mortem required. No non-critical deployments allowed until the next 30-day window resets the budget.
