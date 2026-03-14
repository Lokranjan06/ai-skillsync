# AI SkillSync — Backend API

> **AI-Powered Learning & Career Intelligence System**
> Built with FastAPI · SQLAlchemy · NetworkX · Scikit-learn

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Quick Start](#quick-start)
3. [Architecture Overview](#architecture-overview)
4. [All 8 API Endpoints](#all-8-api-endpoints)
5. [AI Components Explained](#ai-components-explained)
6. [Database Schema](#database-schema)
7. [Switching to PostgreSQL](#switching-to-postgresql)

---

## Project Structure

```
ai_skillsync/
├── main.py                          # App factory, router registration, startup
├── requirements.txt
├── skillsync.db                     # Auto-created SQLite database
│
├── app/
│   ├── database/
│   │   └── session.py               # Engine, SessionLocal, get_db dependency
│   │
│   ├── models/
│   │   └── orm.py                   # All SQLAlchemy ORM models
│   │
│   ├── schemas/
│   │   └── schemas.py               # All Pydantic request/response models
│   │
│   ├── routes/                      # One file per feature (thin controllers)
│   │   ├── skill_graph.py           # GET  /api/skill-graph/{career_id}
│   │   ├── readiness.py             # GET  /api/readiness/{user_id}/{career_id}
│   │   ├── skill_gap.py             # GET  /api/skill-gap/{user_id}/{career_id}
│   │   ├── planner.py               # POST /api/generate-plan
│   │   ├── resume.py                # POST /api/extract-resume
│   │   ├── burnout.py               # POST /api/burnout-risk
│   │   ├── simulation.py            # POST /api/simulate-score
│   │   └── dashboard.py             # GET  /api/dashboard/{user_id}
│   │
│   ├── services/                    # All business logic lives here
│   │   ├── graph_engine.py          # NetworkX graph builder
│   │   ├── scoring_engine.py        # Readiness + skill gap
│   │   ├── planner_engine.py        # Priority-based study planner
│   │   ├── resume_extractor.py      # PDF text extraction + keyword matching
│   │   ├── burnout_service.py       # Risk formula + classification
│   │   └── dashboard_service.py     # Study log aggregation
│   │
│   └── ai/
│       └── prediction_engine.py     # Scikit-learn Digital Twin model
│
└── scripts/
    └── seed.py                      # Database seeder with realistic data
```

---

## Quick Start

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Seed the database

```bash
python scripts/seed.py
```

### 3. Start the server

```bash
uvicorn main:app --reload --port 8000
```

### 4. Explore the API

- Interactive docs: **http://localhost:8000/docs**
- ReDoc:           **http://localhost:8000/redoc**

---

## Architecture Overview

```
HTTP Request
     │
     ▼
┌─────────────┐
│   FastAPI   │  ← CORS, Pydantic validation, OpenAPI docs
│   Router    │
└──────┬──────┘
       │  Dependency Injection (get_db)
       ▼
┌─────────────┐
│   Service   │  ← All business logic, pure Python classes
│   Layer     │
└──────┬──────┘
       │
   ┌───┴────────────────────┐
   ▼                        ▼
┌──────────┐         ┌────────────┐
│SQLAlchemy│         │  AI Layer  │
│  ORM     │         │ (NetworkX, │
│ (SQLite/ │         │  sklearn)  │
│ Postgres)│         └────────────┘
└──────────┘
```

**Design principles:**
- Routes are thin — they validate input, call one service method, return output
- Services contain all logic and are independently testable
- AI engines are stateless (PredictionEngine holds model state, stored in `app.state`)
- Pydantic schemas are the contract between HTTP and services

---

## All 8 API Endpoints

### 1. Skill Graph — `GET /api/skill-graph/{career_id}`

**Request:**
```
GET /api/skill-graph/1
```

**Response:**
```json
{
  "career_id": 1,
  "nodes": [
    { "id": "career_1",  "label": "Data Scientist", "type": "career"  },
    { "id": "skill_1",   "label": "Python",          "type": "skill"   },
    { "id": "subject_1", "label": "Computer Science","type": "subject" }
  ],
  "links": [
    { "source": "subject_1", "target": "skill_1",  "weight": 1.0 },
    { "source": "skill_1",   "target": "career_1", "weight": 0.9 }
  ]
}
```

---

### 2. Career Readiness — `GET /api/readiness/{user_id}/{career_id}`

**Request:**
```
GET /api/readiness/1/1
```

**Response:**
```json
{
  "user_id": 1,
  "career_id": 1,
  "career_title": "Data Scientist",
  "readiness_score": 0.6043,
  "percentage": 60.43,
  "skills_assessed": 7
}
```

---

### 3. Skill Gap — `GET /api/skill-gap/{user_id}/{career_id}`

**Request:**
```
GET /api/skill-gap/1/1
```

**Response:**
```json
{
  "user_id": 1,
  "career_id": 1,
  "strong":  [{ "skill_id": 1, "skill_name": "Python", "skill_level": 0.8, "weight": 0.9, "category": "strong" }],
  "weak":    [{ "skill_id": 3, "skill_name": "Machine Learning", "skill_level": 0.55, "weight": 1.0, "category": "weak" }],
  "missing": [{ "skill_id": 6, "skill_name": "Linear Algebra", "skill_level": 0.3, "weight": 0.6, "category": "missing" }],
  "summary": { "strong": 1, "weak": 4, "missing": 2 }
}
```

---

### 4. Study Planner — `POST /api/generate-plan`

**Request:**
```json
{
  "user_id": 1,
  "career_id": 1,
  "exam_days_left": 14,
  "top_n": 3
}
```

**Response:**
```json
{
  "user_id": 1,
  "career_id": 1,
  "exam_days_left": 14,
  "tasks": [
    {
      "skill_id": 3,
      "skill_name": "Machine Learning",
      "priority": 0.032143,
      "skill_level": 0.55,
      "weight": 1.0,
      "reason": "Skill needs reinforcement; it is critical for the target career."
    }
  ]
}
```

---

### 5. Resume Extractor — `POST /api/extract-resume`

**Request:** `multipart/form-data` with field `file` (PDF)

```bash
curl -X POST http://localhost:8000/api/extract-resume \
  -F "file=@my_resume.pdf"
```

**Response:**
```json
{
  "filename": "my_resume.pdf",
  "total_skills_in_db": 10,
  "matched_skills": [
    {
      "skill_id": 1,
      "skill_name": "Python",
      "matched_keywords": ["python", "fastapi"]
    },
    {
      "skill_id": 2,
      "skill_name": "SQL",
      "matched_keywords": ["postgresql", "sql"]
    }
  ],
  "match_count": 2,
  "coverage_pct": 20.0
}
```

---

### 6. Burnout Risk — `POST /api/burnout-risk`

**Request:**
```json
{
  "user_id": 1,
  "sleep_hours": 5.5,
  "study_hours": 9.0,
  "focus_score": 35
}
```

**Response:**
```json
{
  "user_id": 1,
  "risk_score": 1.2425,
  "risk_level": "Medium",
  "advice": "Signs of stress are emerging. Consider reducing daily study hours, improving sleep consistency, and adding short mindfulness breaks."
}
```

---

### 7. Digital Twin Simulation — `POST /api/simulate-score`

**Request:**
```json
{
  "study_hours": 6.0,
  "focus_score": 80,
  "revision_frequency": 4
}
```

**Response:**
```json
{
  "predicted_score": 82.47,
  "confidence_note": "Score predicted by a Linear Regression model trained on synthetic data. Accuracy improves as real study_log data is used for retraining.",
  "input_summary": {
    "study_hours": 6.0,
    "focus_score": 80,
    "revision_frequency": 4
  }
}
```

---

### 8. Performance Dashboard — `GET /api/dashboard/{user_id}`

**Request:**
```
GET /api/dashboard/1
```

**Response:**
```json
{
  "user_id": 1,
  "weekly_hours": [
    { "week": "2024-W10", "hours": 18.4 },
    { "week": "2024-W11", "hours": 21.1 }
  ],
  "skill_progress": [
    { "skill_name": "Python",           "skill_level": 0.8  },
    { "skill_name": "Machine Learning", "skill_level": 0.55 }
  ],
  "focus_distribution": [
    { "range": "0-25",   "count": 0  },
    { "range": "26-50",  "count": 5  },
    { "range": "51-75",  "count": 14 },
    { "range": "76-100", "count": 9  }
  ],
  "total_study_hours": 87.3,
  "avg_focus_score": 67.4,
  "log_count": 28
}
```

---

## AI Components Explained

### Skill Graph Engine (NetworkX)
Constructs a `DiGraph` with three node types. Edges flow Subject → Skill → Career. Edge weights represent skill importance to the career. The D3.js-compatible node-link JSON lets the frontend render interactive force graphs.

### Readiness Score (Weighted Average)
A normalised dot product of `[skill_levels]` and `[weights]` for all career-required skills. Result is always in [0, 1]. Gives more influence to skills the career values most.

### Skill Gap (Threshold Classifier)
A simple three-bucket classifier using empirically chosen thresholds: >0.75 = strong, 0.4–0.75 = needs work, <0.4 = missing. Actionable and transparent for learners.

### Adaptive Planner (Priority Formula)
`priority = (1 - level) × weight × (1 / days)` elegantly combines three factors: how weak the skill is, how important it is, and how urgent the deadline is. Produces a ranked to-do list.

### Resume Extractor (Keyword Matching)
pypdf extracts text; regex normalisation removes noise; skills are matched by checking whether any stored keyword appears in the normalised text. Extend to fuzzy matching or embeddings for production.

### Burnout Detector (Linear Combination)
Three independent stress signals (sleep deficit, study overload, focus drop) are weighted and summed. Thresholds map to Low/Medium/High with actionable advice.

### Digital Twin (Scikit-learn LinearRegression)
A Pipeline with StandardScaler (prevents feature scale dominance) and LinearRegression. Trained on 500 synthetic samples at startup. Coefficients are interpretable: ~8 pts/study-hour, ~0.4 pts/focus-point. Replace with real data for production accuracy.

### Dashboard (Aggregation)
Pure SQL queries and Python grouping. ISO week numbers produce consistent weekly buckets. Focus score histogram uses fixed bands for clear visualisation.

---

## Database Schema

```
users              careers
─────────          ──────────
id (PK)            id (PK)
name               title
email              description
created_at
                   career_skills
subjects           ─────────────
────────           id (PK)
id (PK)            career_id (FK → careers)
name               skill_id  (FK → skills)
                   weight (0.0–1.0)
skills
──────             user_skill_progress
id (PK)            ───────────────────
name               id (PK)
subject_id (FK)    user_id   (FK → users)
keywords           skill_id  (FK → skills)
                   skill_level (0.0–1.0)
study_logs         updated_at
──────────
id (PK)
user_id (FK → users)
skill_id (FK → skills)
study_hours
focus_score
sleep_hours
revision_frequency
logged_at
```

---

## Switching to PostgreSQL

```bash
export DATABASE_URL="postgresql+psycopg2://user:password@localhost:5432/skillsync"
pip install psycopg2-binary
python scripts/seed.py
uvicorn main:app --reload
```

No code changes required — only the environment variable.
