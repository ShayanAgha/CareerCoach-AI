# Interview Prep Coach — Project Plan

Domain-bounded AI assistant assignment, built with Flask + Gemini API + SQLAlchemy,
deployed on Vercel. This document is the single source of truth for structure,
build order, and delivery — keep it in the repo root and update it as you go.

---

## 1. Key Architectural Decisions (read this first)

| Decision | Choice | Why |
|---|---|---|
| Domain | Interview Prep Coach | Distinct from Mind Coach, multi-turn is inherent to the domain, refusal cases are obvious |
| Backend | Flask (WSGI) | Required by spec |
| LLM | Gemini API (`google-generativeai` SDK), Flash-tier model | Free tier, matches Mind Coach reference implementation |
| Local DB | SQLite via Flask-SQLAlchemy | Fast local dev, zero setup |
| **Production DB** | **Postgres (Neon or Vercel Postgres, free tier)** | **Vercel functions do not have a persistent filesystem — SQLite writes will not survive between invocations in production.** SQLAlchemy makes this a connection-string swap, not a rewrite. |
| Frontend | Vanilla HTML/CSS/JS, mobile-first | Required by spec, no frameworks allowed |
| Deployment | Vercel (Flask auto-detected framework) | User requirement |

**Practical implication:** write all DB access through SQLAlchemy models from day one (never raw file paths, never assume the DB file persists). Locally you point `DATABASE_URL` at `sqlite:///instance/app.db`; in Vercel's project settings you set `DATABASE_URL` to your Neon/Postgres connection string. Same code, two environments.

---

## 2. Final Project Structure

```
interview-prep-coach/
├── main.py                     # Flask entrypoint (Vercel requires this exact convention)
├── config.py                   # Config class: reads DATABASE_URL, GEMINI_API_KEY from env
├── models.py                   # SQLAlchemy models: Session, Message, UsageLog
├── extensions.py                # db = SQLAlchemy() (avoids circular imports)
├── gemini_client.py             # Gemini wrapper: build_system_prompt(), call_gemini(), compute_cost()
├── routes/
│   ├── __init__.py
│   ├── onboarding.py            # GET / , POST /
│   ├── chat.py                  # GET /chat , POST /chat
│   └── dashboard.py             # GET /dashboard , GET /api/usage
├── templates/
│   ├── base.html                # shared <head>, viewport meta, nav
│   ├── onboarding.html
│   ├── chat.html
│   └── dashboard.html
├── static/
│   ├── css/
│   │   └── style.css            # mobile-first, breakpoints for tablet/desktop
│   ├── js/
│   │   ├── chat.js               # fetch-based chat, no reload
│   │   └── dashboard.js          # fetch /api/usage, render table + Chart.js
│   └── img/
├── instance/
│   └── app.db                   # local SQLite (gitignored)
├── tests/
│   └── test_routes.py           # basic smoke tests (bonus, not required)
├── postman/
│   └── interview_coach.postman_collection.json
├── .env.example                 # documents required env vars, no real secrets
├── .gitignore
├── vercel.json                  # Vercel function config (maxDuration, etc.)
├── requirements.txt
├── README.md
└── PROJECT_PLAN.md              # this file
```

---

## 3. Requirements Checklist (from the assignment — do not skip any of these)

- [ ] Onboarding form → creates a `Session` row with JSON `onboarding_data`
- [ ] `/chat` POST → sends **full conversation history** to Gemini every call, not just the latest message
- [ ] System prompt is built dynamically from onboarding data (hardened role)
- [ ] Bot refuses off-domain requests **in character**, not with a generic disclaimer
- [ ] Three tables minimum: `Session`, `Message`, `UsageLog` (one row per API call, not per message pair)
- [ ] `estimated_cost_usd` computed from real `usage_metadata`, never hardcoded
- [ ] `/dashboard` shows: total requests, total input/output tokens, total cost, per-session breakdown
- [ ] `/api/usage` JSON endpoint backing the dashboard
- [ ] Plain HTML/CSS/JS only — no React/Vue/etc.
- [ ] Mobile-friendly UI (this conversation's addition, not in original spec, but required for your deployment)
- [ ] Real, incremental GitHub commit history
- [ ] Postman collection with 3+ real request/response screenshots, including token/cost fields populated
- [ ] 3–5 min demo video: onboarding → multi-turn in-domain chat → one off-domain refusal → dashboard update
- [ ] README: domain choice, system prompt strategy, DB schema, pricing rates + source/date

**Zero-credit triggers to actively avoid:** hardcoded token/cost numbers, single commit dump, Mind Coach reskin.

---

## 4. Epics & User Stories

### Epic 1 — Project Foundation & Data Layer
| ID | Story | Acceptance Criteria |
|---|---|---|
| 1.1 | As a developer, I set up the Flask app skeleton with config and extensions | `main.py` runs locally, `flask run` serves a placeholder route |
| 1.2 | As a developer, I define the three SQLAlchemy models | `Session`, `Message`, `UsageLog` created; `db.create_all()` builds local SQLite without errors |
| 1.3 | As a developer, I make the DB connection environment-driven | `DATABASE_URL` env var selects SQLite locally / Postgres in prod, with a working fallback |

### Epic 2 — Onboarding Flow
| ID | Story | Acceptance Criteria |
|---|---|---|
| 2.1 | As a candidate, I fill out a form with target role, experience level, and weak areas | Form renders, validates required fields client + server side |
| 2.2 | As a candidate, submitting the form creates my session | A `Session` row is created with `onboarding_data` as JSON; I'm redirected to `/chat?session_id=` |

### Epic 3 — Chat Engine & Multi-Turn Gemini Integration
| ID | Story | Acceptance Criteria |
|---|---|---|
| 3.1 | As a candidate, I can send a message and get a Gemini reply | `POST /chat` returns JSON `{reply}`, message saved to DB |
| 3.2 | As a candidate, the bot remembers earlier turns in my session | Full message history for the session is sent to Gemini on every call; verified via growing `prompt_token_count` |
| 3.3 | As a candidate, the bot only discusses interview prep | System prompt built from onboarding data enforces domain scope |
| 3.4 | As a candidate, off-domain questions get an in-character redirect | Manual test: ask for medical/legal/relationship advice, confirm refusal stays in coach persona |

### Epic 4 — Usage & Cost Tracking
| ID | Story | Acceptance Criteria |
|---|---|---|
| 4.1 | As a developer, I log token usage for every API call | One `UsageLog` row per Gemini call, pulling real `usage_metadata` |
| 4.2 | As a developer, I compute cost from published per-token rates | Constants documented with source + date; formula matches spec exactly |

### Epic 5 — Dashboard
| ID | Story | Acceptance Criteria |
|---|---|---|
| 5.1 | As a user, I see total requests/tokens/cost | `/dashboard` and `/api/usage` return correct aggregates |
| 5.2 | As a user, I see a per-session cost breakdown | Table grouped by `session_id` |
| 5.3 (stretch) | As a user, I see a chart of cost over time/session | Chart.js bar/line chart from `/api/usage` data |

### Epic 6 — Responsive Frontend (Mobile + Desktop)
| ID | Story | Acceptance Criteria |
|---|---|---|
| 6.1 | As a mobile user, the onboarding form is usable one-handed | Inputs ≥44px touch targets, no horizontal scroll at 375px width |
| 6.2 | As a mobile user, the chat UI works like a messaging app | Sticky input bar, auto-scroll to newest message, readable at 375–430px |
| 6.3 | As a desktop user, the dashboard uses the extra width well | Table + chart side-by-side above a defined breakpoint, stacked below it |

### Epic 7 — Deployment (Vercel)
| ID | Story | Acceptance Criteria |
|---|---|---|
| 7.1 | As a developer, the app runs locally against SQLite | `flask run` works end to end |
| 7.2 | As a developer, the app is deployable to Vercel | `vercel.json` present, `main.py` entrypoint, deploy succeeds |
| 7.3 | As a developer, production uses Postgres, not SQLite | `DATABASE_URL` set in Vercel project settings to Neon connection string; chat history persists across requests in the deployed app |
| 7.4 | As a developer, secrets are never committed | `GEMINI_API_KEY`, `DATABASE_URL` only in Vercel env vars + local `.env` (gitignored) |

### Epic 8 — QA, Documentation & Submission Packaging
| ID | Story | Acceptance Criteria |
|---|---|---|
| 8.1 | As a grader, I can see incremental commit history | ≥10 meaningful commits spanning the epics above |
| 8.2 | As a grader, I can hit the API directly | Postman collection exported with 3+ real requests, screenshots included |
| 8.3 | As a grader, I can watch the workflow | 3–5 min demo video covering onboarding → multi-turn → refusal → dashboard |
| 8.4 | As a grader, I understand the design decisions | README covers domain choice, prompt strategy, DB schema, pricing source |

---

## 5. Build Workflow (do the phases in this order — each phase is 1+ commits)

```
Phase 0  Repo init, .gitignore, requirements.txt, folder skeleton
Phase 1  SQLAlchemy models + local SQLite, db.create_all() sanity check
Phase 2  Onboarding route + template (no styling yet, just working forms)
Phase 3  Gemini client: single-turn call working (no history, no DB logging yet)
Phase 4  Wire multi-turn: pull Message history from DB, pass full contents to Gemini
Phase 5  UsageLog: extract usage_metadata, compute cost, persist
Phase 6  Dashboard backend: /dashboard + /api/usage aggregation queries
Phase 7  Chat frontend: fetch-based JS, mobile-first CSS
Phase 8  Dashboard frontend: table + Chart.js, responsive layout
Phase 9  Prompt hardening pass: test refusal cases, tune system prompt wording
Phase 10 Deployment prep: vercel.json, DATABASE_URL env-driven config, Postgres provisioning
Phase 11 Deploy to Vercel, smoke test onboarding → chat → dashboard on the live URL
Phase 12 Postman collection + screenshots, README, demo video, final polish commit
```

**Why this order matters:** Phase 3 before Phase 4 is deliberate — get a single Gemini call working end-to-end before adding history, so when token counts look wrong you know it's the history-wiring, not the API integration. This directly targets the assignment's stated "trap."

---

## 6. Git Workflow & Commands

### One-time setup
```bash
mkdir interview-prep-coach && cd interview-prep-coach
git init
git branch -M main

cat > .gitignore << 'EOF'
__pycache__/
*.pyc
.env
instance/
.vercel/
venv/
.DS_Store
node_modules/
EOF

# create the folder skeleton from section 2, then:
git add .
git commit -m "chore: project skeleton and gitignore"

# create the GitHub repo (via web UI, or gh CLI if installed)
gh repo create interview-prep-coach --private --source=. --remote=origin
# or manually:
git remote add origin https://github.com/<your-username>/interview-prep-coach.git

git push -u origin main
```

### Per-phase commit pattern (repeat for each phase in Section 5)
```bash
git add <files>
git commit -m "feat(models): add Session, Message, UsageLog tables"
git push
```

Use conventional prefixes so commit history reads cleanly for the grader:
- `feat:` new functionality
- `fix:` bug fix
- `chore:` tooling/config/deps
- `docs:` README/plan updates
- `style:` CSS/UI-only changes
- `refactor:` no behavior change

### Suggested commit sequence (maps to Section 5 phases)
```bash
git commit -m "chore: project skeleton and gitignore"
git commit -m "feat(models): add Session, Message, UsageLog tables"
git commit -m "feat(onboarding): form and session creation route"
git commit -m "feat(gemini): single-turn Gemini call wrapper"
git commit -m "feat(chat): multi-turn history wiring for /chat"
git commit -m "feat(usage): token/cost extraction and UsageLog persistence"
git commit -m "feat(dashboard): usage aggregation routes"
git commit -m "feat(frontend): mobile-first chat UI with fetch"
git commit -m "feat(frontend): dashboard table and chart, responsive layout"
git commit -m "fix(prompt): harden refusal behavior for off-domain requests"
git commit -m "chore(deploy): vercel.json and env-driven DB config"
git commit -m "chore(deploy): switch production DB to Postgres via DATABASE_URL"
git commit -m "docs: README with pricing sources, schema, prompt strategy"
git commit -m "test: postman collection and smoke tests"
```
Don't squash these before submission — the grader is explicitly checking timestamps and messages.

---

## 7. Responsive UI/UX Requirements

- **Viewport meta tag** in `base.html`: `<meta name="viewport" content="width=device-width, initial-scale=1">` — without this, mobile browsers render a desktop-width page and "responsive" CSS does nothing.
- **Mobile-first CSS**: write base styles for narrow screens first, then widen with `min-width` media queries (e.g. `@media (min-width: 768px)` for tablet, `@media (min-width: 1024px)` for desktop) — this is more reliable than starting desktop-first and shrinking down.
- **Touch targets**: buttons/inputs at least 44×44px on the chat and onboarding forms.
- **Chat layout**: message list scrolls independently, input bar stays fixed/sticky at the bottom on mobile (common messaging-app pattern), auto-scroll to the latest message on send/receive.
- **No horizontal scroll**: test onboarding form and chat bubbles at 375px width (iPhone SE-class) — long words/URLs need `overflow-wrap: break-word`.
- **Dashboard**: table gets `overflow-x: auto` inside a wrapper on narrow screens rather than squeezing columns unreadably; chart and table stack vertically below the tablet breakpoint, side-by-side above it.
- **Test matrix before submission**: Chrome DevTools device toolbar at 375px, 768px, 1280px minimum, plus one real phone if available.

---

## 8. Vercel Deployment Specifics (verified against current Vercel docs)

### Entry point
Vercel's Flask support auto-detects a Flask app instance named `app` in `main.py` at the project root — this is the current supported convention, not the old manual `@vercel/python` builder setup from older tutorials.

```python
# main.py
from flask import Flask
app = Flask(__name__)
# ... register blueprints from routes/
```

### vercel.json
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "functions": {
    "main.py": {
      "maxDuration": 30
    }
  }
}
```
`maxDuration` matters here specifically because Gemini calls are network round-trips that can occasionally take a few seconds — the Hobby plan default is short, so set this explicitly rather than relying on defaults.

### Static files
Don't rely on Flask's `static_folder` on Vercel — serve static assets from a `public/` directory at the project root instead (Vercel serves `public/**` directly), and reference them from templates with absolute paths.

### Database
Filesystem writes in a Vercel function are not guaranteed to persist between invocations — this is precisely why SQLite can't be your production DB here. Provision a free Neon or Vercel Postgres database, then:

```python
# config.py
import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(os.path.dirname(__file__), "instance", "app.db")
    )
```
Set `DATABASE_URL` in Vercel's Project → Settings → Environment Variables (Production + Preview) to the Postgres connection string. Locally it falls back to SQLite automatically since the env var won't be set.

### Environment variables checklist
| Variable | Where set | Notes |
|---|---|---|
| `GEMINI_API_KEY` | Vercel project settings + local `.env` | never commit |
| `DATABASE_URL` | Vercel project settings only | absent locally → SQLite fallback |

### Deploy commands
```bash
npm i -g vercel      # one-time
vercel login
vercel                # first deploy, links project, asks framework (should auto-detect Flask)
vercel --prod          # production deploy after main is stable
```
Every push to `main` (once the GitHub repo is linked in the Vercel dashboard) triggers an automatic deployment — link this early so Phase 11 is just a formality, not a scramble at the end.

---

## 9. Pricing Reference (verify again before submitting — these change)

As of late July 2026, published Gemini API standard-tier rates (check `https://ai.google.dev/gemini-api/docs/pricing` for current numbers before finalizing your README):

| Model | Input $/1M tokens | Output $/1M tokens | Note |
|---|---|---|---|
| Gemini 2.5 Flash-Lite | $0.10 | $0.40 | cheapest current option; scheduled for retirement Oct 16, 2026 |
| Gemini 3.5 Flash-Lite | $0.30 | $2.50 | likely successor |
| Gemini 3.1 Pro | $2.00 | $12.00 | flagship, $4/$18 above 200K context |

Free tier: Flash-family models can be called free of charge within rate limits (with the tradeoff that free-tier traffic may be used to improve Google's products) — this is what lets you build and demo without billing, while still hardcoding the *paid* rates for the cost simulation the assignment asks for.

---

## 10. Submission Checklist → Rubric Mapping

| Rubric Area | Weight | Where it's covered here |
|---|---|---|
| Domain originality + hardening | 20% | Epic 3 (system prompt), Epic 3.4 refusal testing |
| Multi-turn state | 20% | Epic 3.2, Phase 3→4 build split |
| DB schema + persistence | 20% | Epic 1, Epic 7.3 (Postgres in prod) |
| Token/cost accuracy | 25% | Epic 4, Section 9 |
| Dashboard + frontend | 10% | Epic 5, Epic 6 |
| Code quality/README/commits | 5% | Epic 8, Section 6 |
