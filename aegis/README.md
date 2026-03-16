# AEGIS — AI Governance Proxy Hub

AEGIS is an intelligent proxy layer that sits between your application and any LLM API. It intercepts every request and response, detects sensitive or policy-violating content, and enforces configurable governance actions (ALLOW / BLOCK / REDACT / TRANSFORM) — all with a full audit trail.

## Monorepo Structure

```
aegis/
├── backend/          # FastAPI Python backend
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── proxy/        # Request interception & forwarding
│   ├── detection/    # PII / sensitive-data detection (regex + NER + LLM fallback)
│   ├── policy/       # Governance policy engine
│   ├── scoring/      # Composite risk scorer
│   ├── decision/     # Action engine (block / redact / transform)
│   ├── receipt/      # Audit receipt generator (JSON + PDF)
│   ├── storage/      # Database models & seeding
│   └── api/          # Dashboard & admin REST endpoints
└── frontend/         # Next.js dashboard (to be initialised)
```

## Quick Start

### Backend

```bash
cd aegis/backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env         # fill in your API keys
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000` for the health check, and `http://localhost:8000/docs` for the interactive API docs.

### Frontend

```bash
cd aegis/frontend
npx create-next-app@latest . --typescript --tailwind --app
npm run dev
```

## Environment Variables

Copy `aegis/.env.example` to `aegis/.env` and fill in the values.

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `GEMINI_API_KEY` | Google Gemini API key |
| `TARGET_LLM_BASE_URL` | Base URL of the target LLM API |
| `DEFAULT_MODEL` | Default model identifier |
| `PORT` | Backend server port (default: 8000) |
| `FRONTEND_URL` | Frontend origin for CORS |

## Tech Stack

- **Backend**: FastAPI, Uvicorn, Presidio, spaCy, httpx, pydantic-settings
- **Frontend**: Next.js, TypeScript, Tailwind CSS *(to be wired)*
- **Storage**: SQLite / PostgreSQL *(to be wired)*
