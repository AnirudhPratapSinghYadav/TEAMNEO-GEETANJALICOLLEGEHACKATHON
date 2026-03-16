# TEAMNEO-GEETANJALICOLLEGEHACKATHON
This project is made by team Neo for Hackathon at Geetanjali college

## Setup Instructions

### Backend
```bash
cd aegis/backend && pip install -r requirements.txt && python -m spacy download en_core_web_sm
```

### Frontend
```bash
cd aegis/frontend && npm install
```

### Run Backend
```bash
cd aegis/backend && uvicorn main:app --reload --port 8000
```

### Run Frontend
```bash
cd aegis/frontend && npm run dev
```
