# MentorOS v3.0 — AI-Powered Personal Learning OS

> Production-grade adaptive learning system with **MongoDB Atlas**, an asynchronous Beanie ODM, and a **100% Custom Local AI Engine**. No external AI costs, no hardcoding.

---

## 🏗 Architecture

```
Frontend (HTML/JS)  ──→  FastAPI Backend  ──→  MongoDB Atlas (Beanie ODM)
                               │
                               ├──→  Custom Local AI  (Algorithmic Planner/Tutor)
                               ├──→  FAISS + SentenceTransformers  (semantic search)
                               ├──→  Redis  (caching, optional)
                               └──→  APScheduler  (reminders)
```

---

## ⚡ Quick Start (5 minutes)

### 1. Clone & Set Up Backend

```bash
cd backend
cp .env.example .env
```

Edit `.env` — **required fields:**
```
SECRET_KEY=<run: openssl rand -hex 32>
MONGODB_URI=mongodb+srv://...  # Your Atlas URI
```

### 2. Install & Run Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API is live at: **http://localhost:8000**
Swagger docs: **http://localhost:8000/docs**

### 3. Open Frontend

Open `mentoross-app.html` in your browser.

Set the **Backend API URL** to `http://localhost:8000` in the login page config box.

Register a new account → Start learning!

---

## 📱 Desktop & Mobile Installation (PWA)

MentorOS is a **Progressive Web App**. You can install it on your taskbar or home screen for a standalone experience:
1.  Open the app in your browser (Chrome Technical, Edge, or Safari).
2.  Click the **"Install"** icon in the address bar (Desktop) or **"Add to Home Screen"** (iOS/Android).
3.  Enjoy a professional, full-screen desktop experience on macOS and Windows.

---

## ▲ Vercel Deployment

MentorOS v3.0 is optimized for Vercel Serverless:
1.  Connect your GitHub repo to Vercel.
2.  Add Environment Variables: `MONGODB_URI`, `DATABASE_NAME`, `SECRET_KEY`.
3.  Vercel will automatically use `vercel.json` to route your API and serve the frontend.
4.  No extra configuration needed!

---

## 🐳 Docker Deployment

Professional deployment is ready via Docker Compose.

```bash
# Fill .env first
cp backend/.env.example backend/.env

# Build and Launch
docker-compose up -d --build
```

The stack includes:
- **Backend**: FastAPI on Gunicorn (Production grade)
- **Frontend**: Nginx serving the refined UI
- **Database**: External MongoDB Atlas link

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | JWT signing key — `openssl rand -hex 32` |
| `MONGODB_URI` | ✅ | MongoDB Atlas Connection String |
| `DATABASE_NAME` | ✅ | Default: `mentoross` |
| `ENVIRONMENT` | — | `development` or `production` |
| `ALLOWED_ORIGINS` | — | List of frontend origins |

---

## 🤖 AI Features (100% Local & Custom)

| Feature | Endpoint | Description |
|---|---|---|
| **Plan Generator** | `POST /plans/generate` | Algorithmic generation based on history |
| **AI Reviewer** | `POST /reviewer/evaluate` | Rules-based performance evaluation |
| **AI Tutor** | `POST /teacher/explain` | Concept templates for all levels |

---

## 📁 Project Structure

```
mentoross/
├── backend/
│   ├── core/
│   │   ├── config.py        ← Config via env vars
│   │   ├── constants.py     ← Domain & AI constants
│   │   ├── database.py      ← Motor/Beanie init
│   │   └── security.py      ← JWT + pure bcrypt
│   ├── models/
│   │   └── all_models.py    ← Beanie Document models
│   ├── routes/
│   │   ├── auth.py          ← Register, login (custom)
│   │   ├── tasks.py         ← MongoDB CRUD
│   │   └── extras.py        ← Analytics, AI, Resources
│   ├── services/
│   │   └── ai_agents.py     ← Local algorithmic engine
│   ├── main.py              ← FastAPI app entry
│   └── requirements.txt     ← Refined for Python 3.13
├── docker-compose.yml
├── backend.Dockerfile
├── frontend.Dockerfile
├── mentoross-app.html       ← Polished Glassmorphism UI
└── README.md
```
