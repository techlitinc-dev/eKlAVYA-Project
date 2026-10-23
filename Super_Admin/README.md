# eKlAVYA — Mentor AI SuperAdmin Portal

The **SuperAdmin Portal** is built into the unified React 19 + TypeScript + Vite web application in [`/home/tushka/Projects/eKlAVYA/Frontend_Website`](file:///home/tushka/Projects/eKlAVYA/Frontend_Website) and powered by the FastAPI backend router [`Backend/routers/superadmin_router.py`](file:///home/tushka/Projects/eKlAVYA/Backend/routers/superadmin_router.py).

## Direct SuperAdmin Routes (`http://localhost:3000`)

- **Executive Overview & Telemetry**: `http://localhost:3000/superadmin/dashboard`
- **User, Subscription & Concept Wall Governance**: `http://localhost:3000/superadmin/users`
- **PYQ Question Bank CMS (Live KaTeX Preview + Hot-Reload)**: `http://localhost:3000/superadmin/questions`
- **3D Flashcard Decks & JoSAA/MCC College Cutoff Matrix**: `http://localhost:3000/superadmin/content`
- **Hermes AI Guardrails & Audit Logs**: `http://localhost:3000/superadmin/ai-settings`

## SuperAdmin API Endpoints (`http://localhost:8000/api/superadmin/*`)

- `POST /api/superadmin/login`
- `POST /api/superadmin/demo-session`
- `GET  /api/superadmin/overview`
- `GET  /api/superadmin/users`
- `POST /api/superadmin/users/action`
- `GET  /api/superadmin/questions`
- `POST /api/superadmin/questions`
- `PUT  /api/superadmin/questions/{question_id}`
- `DELETE /api/superadmin/questions/{question_id}`
- `GET  /api/superadmin/flashcards`
- `POST /api/superadmin/flashcards`
- `DELETE /api/superadmin/flashcards/{card_id}`
- `GET  /api/superadmin/colleges`
- `PUT  /api/superadmin/colleges/{college_id}`
- `GET  /api/superadmin/assessments`
- `GET  /api/superadmin/system-config`
- `PUT  /api/superadmin/system-config`
