# Security

## Before Publishing

1. Never commit `.env`; use `.env.example` for placeholders.
2. Do not commit real VINs, exact home/work routes, personal driving logs, or API
   keys.
3. Treat live OBD-II captures as personal data. Sanitize or synthesize public
   samples.

## Read-Only Scope

Corvus reads OBD-II data only. It must not clear diagnostic codes, write to an
ECU, or expose Mode 04 behavior.

Allowed read modes:

- Mode 01 - current live data
- Mode 02 - freeze-frame data
- Mode 03 - stored trouble codes
- Mode 07 - pending trouble codes
- Mode 09 - vehicle information

## Environment Variables

| Variable | Required | Notes |
| --- | --- | --- |
| `USE_LLM` | Yes | Enables or disables language interpretation paths. |
| `LLM_ENDPOINT` | Yes | Hosted endpoint or local Ollama-compatible endpoint. |
| `LLM_MODEL` | Yes | Defaults to `JOSIEFIED-Qwen3:8b`. |
| `LLM_API_KEY` | Local placeholder | Keep real hosted keys out of git. |
| `DATABASE_URL` | Yes | Defaults to local SQLite seed path. |
| `OBD_PORT` | Optional | `auto` or an explicit adapter path. |

## Reporting Issues

If a secret or personal vehicle log reaches git history, rotate the credential or
remove the data source immediately, then open a private issue for cleanup.

