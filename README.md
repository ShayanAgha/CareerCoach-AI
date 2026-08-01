# Interview Prep Coach — AI-Powered Career Coaching Chatbot

A production-ready Flask web application that acts as a personalised **Interview Prep Coach**. It uses the Gemini 3.5 Flash Lite API to ask structured interview questions, give detailed coaching feedback, and refuse all off-domain requests in-character.

---

## Domain Choice Rationale

Interview prep was chosen because:
- Multi-turn conversation is *inherent* to the domain — every exchange builds context (question → answer → feedback → next question)
- Off-domain refusals are obvious and testable (ask for medical advice, get a coach redirect)
- The domain is distinct from "Mind Coach" and highly practical for users
- The coaching persona naturally enforces domain scope ("I'm here to prepare you for interviews, not answer unrelated questions")

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Backend | Flask 3.x (WSGI) | Spec requirement |
| LLM | Gemini 3.5 Flash-Lite (free tier) | Free tier available, low-cost, and optimized for fast coaching responses |
| ORM | Flask-SQLAlchemy | Env-driven connection string, easy model definition |
| Local DB | SQLite (`instance/app.db`) | Zero setup for local dev |
| Frontend | Vanilla HTML/CSS/JS | Spec requirement, no frameworks |
| Font | Inter (Google Fonts) | Modern, clean, professional |

---

## Setup

### 1. Clone & create virtual environment
```bash
git clone <repo-url>
cd CareerCoach_AI
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
copy .env.example .env
```
Edit `.env` and add your Gemini API key:
```
GEMINI_API_KEY=your_actual_key_here
```
Get a free API key at: https://ai.google.dev/

### 4. Run the app
```bash
flask --app main run --debug
```
Or:
```bash
python main.py
```
Open: http://localhost:5000

---

## Database Schema

Three tables — all accessed via SQLAlchemy, never raw SQL:

### `sessions`
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment session ID |
| `created_at` | DATETIME | UTC timestamp of session creation |
| `onboarding_data` | TEXT (JSON) | Serialised onboarding form data |

`onboarding_data` JSON structure:
```json
{
  "target_role": "Software Engineer",
  "experience_level": "Senior (5-10 years)",
  "weak_areas": "system design, concurrency",
  "interview_style": "Technical (algorithms & system design)",
  "target_company": "Google"
}
```

### `messages`
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `session_id` | INTEGER FK → sessions.id | Parent session |
| `role` | VARCHAR(10) | `"user"` or `"model"` |
| `content` | TEXT | Message content |
| `created_at` | DATETIME | UTC timestamp |

### `usage_logs`
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `session_id` | INTEGER FK → sessions.id | Parent session |
| `prompt_tokens` | INTEGER | Input tokens (from `usage_metadata`) |
| `completion_tokens` | INTEGER | Output tokens (from `usage_metadata`) |
| `total_tokens` | INTEGER | Sum of above |
| `estimated_cost_usd` | FLOAT | Computed cost — see pricing below |
| `created_at` | DATETIME | UTC timestamp |

> One `UsageLog` row per Gemini API call. Each `/chat POST` produces exactly one row.

---

## System Prompt Strategy

The system prompt is built *dynamically* from the candidate's onboarding data on every API call. It:

1. **Establishes persona** — the model is told it is an expert Interview Prep Coach with a specific candidate profile to work with
2. **Scopes behaviour** — the model is instructed to ask one question at a time, then give structured feedback (Strengths / Gaps / Action / Rephrase)
3. **Enforces domain** — explicit rules tell the model to redirect any off-domain requests in-character, using the candidate's role name in the redirect
4. **Prevents jailbreaks** — the model is told never to break character, even if asked to "pretend" or "ignore previous instructions"

Key design decision: the system prompt is passed via `system_instruction` in the `GenerativeModel` constructor (not as the first user message), which means it is not included in the visible conversation history and cannot be overridden by user messages.

---

## Pricing & Cost Calculation

**Model:** `gemini-3.5-flash-lite`

| Token type | Rate |
|---|---|
| Input (prompt) | $0.30 per 1,000,000 tokens |
| Output (completion) | $2.50 per 1,000,000 tokens |

**Source:** https://ai.google.dev/gemini-api/docs/pricing (verified July 2026)

**Formula** (see [`gemini_client.py`](gemini_client.py)):
```python
cost = (prompt_tokens / 1_000_000) * 0.30 + (completion_tokens / 1_000_000) * 2.50
```

Token counts come directly from `response.usage_metadata` — they are **never hardcoded**. This means costs grow naturally as conversation history lengthens (multi-turn token accumulation is intentional and verifiable on the dashboard).

> **Note:** The free tier does not charge real money, but the app computes and displays what the cost *would be* at paid rates, as required by the assignment.

---

## Application Routes

| Method | Route | Description |
|---|---|---|
| GET | `/` | Onboarding form |
| POST | `/` | Creates session, redirects to chat |
| GET | `/chat?session_id=` | Chat UI with message history |
| POST | `/chat` | JSON API — sends message, returns reply + tokens + cost |
| GET | `/dashboard?session_id=` | Per-session usage dashboard |
| GET | `/api/usage?session_id=` | JSON usage stats (backing the dashboard) |

---

## Key Design Decisions

- **Multi-turn:** Full message history is fetched from DB and sent to Gemini on *every* `/chat POST`. This is why `prompt_token_count` grows with conversation length — it's the intended proof of multi-turn.
- **No hardcoded costs:** `compute_cost()` always reads from `response.usage_metadata`. If Gemini changes token counts, costs update automatically.
- **Blueprint structure:** Routes are split into three blueprints (`onboarding`, `chat`, `dashboard`) to keep code modular and the commit history meaningful.
- **SQLAlchemy from day one:** No raw SQL, no file path assumptions. The connection string is swappable via `DATABASE_URL`.
