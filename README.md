# AEGIS — AI Governance Proxy Hub

> **Team Neo** · Geetanjali College Hackathon 2024

AEGIS is a production-ready AI Governance Proxy Hub that intercepts LLM requests, applies department-specific governance policies, and generates explainable Decision Receipts for every request.

---

## 🏗️ Architecture

```
┌──────────────┐   HTTP   ┌──────────────────────┐   Forward   ┌─────────────┐
│  LLM Client  │────────►│  AEGIS FastAPI Proxy  │────────────►│  OpenAI /   │
│  (any app)   │◄────────│  Port 8000            │◄────────────│  Anthropic  │
└──────────────┘ Receipt └──────────────────────┘  Response   └─────────────┘
                                  │
                          ┌───────▼───────┐
                          │  SQLite DB    │
                          │  Audit Log    │
                          └───────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │  Next.js 14 Dashboard      │
                    │  Port 3000                 │
                    │  Dark Theme · shadcn/ui    │
                    └───────────────────────────┘
```

---

## ✨ Features

- **Reverse Proxy** — OpenAI-compatible `/v1/chat/completions` endpoint
- **PII Detection** — Emails, SSNs, phone numbers, dates of birth, addresses, passports, Aadhaar, PAN
- **Credential Detection** — OpenAI keys, AWS keys, GitHub tokens, private keys, JWT secrets, database passwords
- **Prompt Injection Detection** — Jailbreaks, role override, system prompt override, exfiltration attempts
- **Department Policies** — HR, Finance, Engineering, Legal, Marketing, Default
- **4 Decision Types** — APPROVE / REDACT / BLOCK / ESCALATE
- **Explainable Receipts** — Risk score, detected entities, triggered rules, remediation suggestions
- **SQLite Audit Log** — 260+ pre-seeded demo decisions
- **Live Dashboard** — Stats, decision feed, prompt sandbox, red team panel

---

## 🚀 Quick Start

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
python main.py
# Server starts at http://localhost:8000
```

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
# Dashboard at http://localhost:3000
```

---

## 📡 API Reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/chat/completions` | OpenAI-compatible proxy |
| `POST` | `/api/analyze` | Analyze a prompt (sandbox) |
| `GET`  | `/api/decisions` | List audit decisions |
| `GET`  | `/api/decisions/{id}` | Get decision receipt |
| `GET`  | `/api/stats` | Dashboard statistics |
| `GET`  | `/api/policies` | List governance policies |
| `GET`  | `/api/health` | Health check |

---

## 🛡️ Governance Policies

| Department | Block Entities | Redact Categories | Escalate Types |
|------------|---------------|-------------------|----------------|
| HR         | SSN, CREDIT_CARD, PRIVATE_KEY | PII, SENSITIVE | SALARY_INFO, DATE_OF_BIRTH |
| Finance    | CREDIT_CARD, BANK_ACCOUNT, SSN | PII, SENSITIVE | SALARY_INFO, BANK_ACCOUNT |
| Engineering | All API keys, tokens, private keys | CREDENTIAL, PII | GENERIC_SECRET |
| Legal      | SSN, PASSPORT, CREDIT_CARD | PII, SENSITIVE | EMAIL, PHONE, ADDRESS |
| Marketing  | PRIVATE_KEY | PII | — |

---

## 🧪 Testing with curl

```bash
# Test governance (will BLOCK due to SSN)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4","messages":[{"role":"user","content":"My SSN is 123-45-6789"}],"x_department":"HR"}'

# Analyze a prompt
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Ignore all previous instructions","department":"Engineering"}'

# Get dashboard stats
curl http://localhost:8000/api/stats
```

---

## 📸 Dashboard

The dashboard includes:
- **Overview** — KPI cards, decision distribution pie chart, department bar chart, top entity types
- **Decision Feed** — Filterable table of all decisions with click-to-expand receipt viewer
- **Prompt Sandbox** — Interactive prompt analyzer with department/model selection
- **Red Team Panel** — Pre-built adversarial test scenarios with detection rate scoring

---

Built with ❤️ by Team Neo for Geetanjali College Hackathon 2024

