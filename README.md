# NovaTicket AI — Event Recommender & Sentiment Analyzer

> An AI-powered platform that recommends personalized events and analyzes review sentiment using Machine Learning.

---

## 📖 Project Overview

NovaTicket is a full-stack web application that helps users discover events tailored to their interests. It combines **Content-Based Filtering**, **Collaborative Filtering**, and a **Hybrid recommendation approach** with an integrated **Sentiment Analysis** engine that automatically classifies user reviews as *Positive*, *Neutral*, or *Negative*.

Built as a learning project demonstrating modern ML-backed web development practices.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **User Authentication** | JWT-based secure auth (register, login, protected routes) |
| **Event Discovery** | Browse, search, and filter events by category, city, keywords |
| **Personalized Recommendations** | Hybrid ML (Content + Collaborative Filtering) with Cold-Start fallback |
| **Sentiment Analysis** | Auto-classifies review sentiment (Positive/Neutral/Negative) with confidence scores |
| **User Dashboard** | Track registrations, view history, see personalized suggestions |
| **Review System** | Star ratings + text reviews with AI-powered sentiment badges |
| **Interaction Tracking** | Records views, clicks, favorites, registrations for ML training |
| **Admin Category Management** | Create and manage event categories |

---

## 🛠 Tech Stack

### Backend
- **FastAPI** — High-performance async Python web framework
- **SQLAlchemy 2.0** — ORM with async support
- **Microsoft SQL Server** — Production-grade relational database
- **scikit-learn** — ML models (TF-IDF + Logistic Regression, SVD for CF)
- **Pydantic v2** — Data validation & serialization
- **python-jose** — JWT token handling
- **bcrypt** — Password hashing
- **Alembic** — Database migrations
- **pytest** — Testing

### Frontend
- **React 19** — Component-based UI
- **Vite** — Lightning-fast build tool
- **React Router v7** — Client-side routing
- **Zustand** — Lightweight state management
- **Axios** — HTTP client with interceptors
- **Lucide React** — Beautiful icons
- **Oxlint** — Fast linting

### Infrastructure
- **Docker & Docker Compose** — Containerized deployment
- **Nginx** — Frontend reverse proxy

---

## 📁 Folder Structure

```
NovaTicket/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes (auth, events, reviews, recommendations...)
│   │   ├── core/             # Config, security, dependencies
│   │   ├── database/         # DB connection, base models
│   │   ├── ml/               # Inference services (sentiment_model, recommendation_model)
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── repositories/     # Data access layer
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic
│   │   └── main.py           # App entry point
│   ├── training/             # Offline ML training scripts
│   ├── tests/                # Pytest test suite
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/              # Axios client
│   │   ├── components/       # Reusable UI components
│   │   ├── layouts/          # Page layouts
│   │   ├── pages/            # Route pages
│   │   ├── store/            # Zustand stores
│   │   ├── utils/            # Helpers (token management)
│   │   └── App.jsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## 🚀 Quick Start (Docker — Recommended)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed
- At least 4GB RAM available for containers

### 1. Clone & Configure
```bash
git clone https://github.com/your-username/NovaTicket.git
cd NovaTicket
```

### 2. Create Environment Files
```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env with your secure values (SECRET_KEY, MSSQL_PASSWORD, etc.)

# Frontend (optional - only if you need custom API URL)
# cp frontend/.env.example frontend/.env
```

### 3. Start All Services
```bash
docker-compose up -d --build
```

### 4. Access the Application
| Service | URL |
|---------|-----|
| **Frontend** | http://localhost |
| **Backend API** | http://localhost:8000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **API Docs (ReDoc)** | http://localhost:8000/redoc |
| **Health Check** | http://localhost:8000/health |

---

## 🔧 Local Development (Without Docker)

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Start SQL Server (via Docker)
docker run -d --name sqlserver -e ACCEPT_EULA=Y -e MSSQL_SA_PASSWORD=YourPass123! -p 1433:1433 mcr.microsoft.com/mssql/server:2022-latest

# Run migrations
alembic upgrade head

# Seed demo data (optional)
python data/seed.py

# Train ML models (optional, requires seeded data)
python training/train_sentiment.py
python training/train_recommender.py

# Start dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

---

## ⚙️ Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | `development` or `production` | `development` |
| `DEBUG` | Enable debug logging | `true` |
| `SECRET_KEY` | JWT signing key (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) | **Required** |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `60` |
| `MSSQL_SERVER` | Database host | `localhost` |
| `MSSQL_PORT` | Database port | `1433` |
| `MSSQL_DATABASE` | Database name | `novaticket` |
| `MSSQL_USER` | Database user | `sa` |
| `MSSQL_PASSWORD` | Database password | **Required** |
| `MSSQL_DRIVER` | ODBC driver name | `ODBC Driver 18 for SQL Server` |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | `http://localhost:5173,http://localhost:3000` |
| `MODEL_DIR` | ML artifacts directory | `models` |

### Frontend (`frontend/.env`)

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | Backend API base URL (empty = relative) |

---

## 🧪 Running Tests

```bash
# Backend tests (requires running SQL Server)
cd backend
.venv\Scripts\python -m pytest tests/ -v

# Or via Docker (uses test database)
docker-compose exec -T backend python -m pytest tests/ -v
```

**Expected Result:** ✅ 10 tests pass (Auth, Events, Reviews, Recommendations)

---

## 📚 API Documentation

Interactive API docs are available at:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Main Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/auth/register` | Register new user | No |
| `POST` | `/auth/login` | Login, get JWT | No |
| `GET` | `/auth/me` | Current user profile | Yes |
| `GET` | `/events` | List events (paginated, filterable) | No |
| `GET` | `/events/{id}` | Event details | No |
| `POST` | `/reviews` | Submit review (auto-sentiment) | Yes |
| `GET` | `/events/{id}/reviews` | Get reviews for event | No |
| `GET` | `/events/{id}/sentiment-summary` | Aggregated sentiment stats | No |
| `POST` | `/interactions` | Record user interaction | Yes |
| `GET` | `/recommendations/me` | Personalized recommendations | Yes |
| `GET` | `/recommendations/events/{id}/similar` | Similar events | No |
| `GET` | `/categories` | List categories | No |

---

## 🏗 CI/CD Status

![CI](https://github.com/your-username/NovaTicket/workflows/CI/badge.svg)

*Configured with GitHub Actions:*
- ✅ Lint (Oxlint + Ruff)
- ✅ Type check (mypy / pyright)
- ✅ Unit tests (pytest)
- ✅ Docker build verification

---

## 💡 Tips for Beginners

1. **Start with Docker** — Avoids local SQL Server / Python version issues
2. **Check `/docs`** — Swagger UI lets you test every endpoint in the browser
3. **Seed data first** — Run `python data/seed.py` to get sample events/categories
4. **Train models** — After seeding, run both training scripts to enable ML features
5. **Use the health endpoint** — `GET /health` confirms backend is ready

---

## 📝 Final Note

> **✅ All tests pass (10/10)** — The project includes a complete test suite covering authentication, events, reviews, recommendations, and categories. Run `docker-compose exec backend python -m pytest tests/ -v` to verify.

---

## 📄 License

MIT License — feel free to use, modify, and distribute.

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Submit a PR

---

Built with ❤️ as a learning project demonstrating ML-powered full-stack development.