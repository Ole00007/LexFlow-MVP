# LexFlow-MVP — Project Status

**Last updated:** 2026-07-21  
**Repo:** `~/lexflow-mvp/` → `https://github.com/Ole00007/LexFlow-MVP` (branch: `main`)  
**Railway:** `lexflow-mvp-production.up.railway.app`

---

## 📋 RECAP — Previous Session

The previous session (Jul 20–21) worked on delivering **Phase 4** features for LexFlow:

### What was completed
1. **Kanban board** — drag-and-drop task cards with status columns
2. **In-app notifications** — real-time notifications when tasks change status, new tasks assigned
3. **Task subtasks/dependencies** — create subtasks, set dependencies between tasks
4. **Bulk operations** — bulk update task status, delete multiple tasks at once
5. **Event model** — calendar events linked to tasks and cases
6. **CSV export/import** — export/import tasks as CSV files
7. **Google Calendar integration** (mock mode) — sync tasks to Google Calendar

### What happened
- Committed and pushed to GitHub: commit `3943125`
- Railway auto-deployed from that commit
- **Deploy FAILED** — two blockers (see Status section below)
- Session ended without resolution

### Key decisions
- Admin email: `Olesya00007@yahoo.com` (7 zeros + 7)
- App factory pattern: `crm/__init__.py` with `create_app()`
- Procfile: `web: gunicorn --bind 0.0.0.0:$PORT wsgi:app`
- WSGI entry: `wsgi.py` imports `from crm import create_app`

---

## 🎯 PLAN FOR TODAY

### Priority 1 — Fix Railway deployment (BLOCKER)
The deploy failed after the last push. Root causes:

1. **`alembic==1.18.4` requires Python ≥ 3.10** — Railway runs 3.9  
   **Fix:** Pin to `alembic==1.16.5` (last 3.9-compatible)

2. **`notifications` table migration has boolean default bug**  
   `read` column uses `server_default=db.text("0")` — PostgreSQL rejects integer default on boolean column  
   **Fix:** Change to `server_default='false'` (SQL literal, not db.text)

3. **`crm/routes/auth.py` has local uncommitted change**  
   `create_access_token(identity=str(user.id))` — converts user.id to string for JWT  
   **Fix:** Commit this change

### Priority 2 — Verify deployment green
After fixing the above, push and confirm Railway goes green:
```bash
curl https://lexflow-mvp-production.up.railway.app/health
# Should return 200 + JSON
```

### Priority 3 — Test key endpoints
- `GET /health` — system health
- `POST /api/auth/login` — JWT auth
- `GET /api/tasks` — task list
- `GET /api/events` — event list

### Priority 4 — Optional: Frontend integration
- LexFlow-landing at `https://poetic-kleicha-28d058.netlify.app` points to Railway backend
- Chatbot widget deployed separately at Railway

---

## 📊 STATUS

### Railway Services
| Service | Status | Notes |
|---------|--------|-------|
| **LexFlow-MVP** | ❌ **FAILED** | Deploy `1a5f1b96` — build error |
| **Postgres** | ✅ SUCCESS | Connected, migrations pending |
| **LexFlow-Chatbot** | ✅ SUCCESS | Running, needs OPENROUTER_API_KEY |
| **web** | ❌ **FAILED** | Same build error |

### Git Status
- **Latest commit:** `3943125` — "feat: kanban board + in-app notifications..."
- **Pushed:** ✅ (content on `origin/main`)
- **Unpushed local change:** `crm/routes/auth.py` (3 lines modified)
- **Untracked files:** `.venv.local/` (local venv — should be in .gitignore)

### Key Configuration
- **Remote:** `https://github.com/Ole00007/LexFlow-MVP.git` (main branch)
- **WSGI:** `wsgi.py` → `from crm import create_app`
- **Procfile:** `web: gunicorn --bind 0.0.0.0:$PORT wsgi:app`
- **Requirements:** 24 packages, `alembic==1.18.4` (❌ needs downgrade)
- **Migrations:** 9 versions, last `b2c3d4e5f6g7` (notifications table — has boolean bug)

### Known Issues
1. ❌ `alembic==1.18.4` → incompatible with Python 3.9 on Railway
2. ❌ `notifications.read` column default `0` → PostgreSQL boolean mismatch
3. ⚠️ `crm/routes/auth.py` local change not committed
4. ⚠️ Chatbot needs `OPENROUTER_API_KEY` set in Railway env
5. ⚠️ Local `.venv.local/` not in `.gitignore`

---

## 📁 PROJECT STRUCTURE

```
~/lexflow-mvp/
├── Procfile              # gunicorn wsgi:app --bind 0.0.0.0:$PORT
├── wsgi.py               # WSGI entry point
├── requirements.txt      # 24 packages
├── app.py                # Intake form (legacy, not used in prod)
├── crm/                  # Main app package
│   ├── __init__.py       # create_app() factory
│   ├── config.py         # Dev/Prod/Test configs
│   ├── models/           # 8 models (Contact, Case, Task, User, Event, Notification...)
│   ├── routes/           # Blueprints (auth, tasks, cases, contacts, events, admin)
│   ├── clients/          # External service clients
│   └── services/         # Business logic services
├── migrations/           # Alembic migrations (9 versions)
├── templates/            # Jinja2 HTML templates
├── data/                 # SQLite fallback DB
├── uploads/              # File uploads
├── instance/             # Flask instance config
└── PROMPTS/              # AI prompts directory
```

---

## ✅ ACCEPTANCE CRITERIA FOR DEPLOYMENT

- [ ] `alembic==1.16.5` in requirements.txt
- [ ] `notification.read` default is `'false'` (not `'0'`)
- [ ] Auth fix committed and pushed
- [ ] Railway deployment → SUCCESS
- [ ] `curl /health` returns 200 + JSON
- [ ] Database migrations run successfully
- [ ] Auth endpoint works (JWT login)
