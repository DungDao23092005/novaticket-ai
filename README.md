# NovaTicket AI — Event Recommender & Sentiment Analyzer

> An AI-powered platform that recommends personalized events and analyzes review sentiment using Machine Learning.

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Tests](https://img.shields.io/badge/tests-10%20passed-brightgreen)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 📖 Project Overview

NovaTicket is a full-stack web application that helps users discover events tailored to their interests. It combines **Content-Based Filtering**, **Collaborative Filtering**, and a **Hybrid recommendation approach** with an integrated **Sentiment Analysis** engine that automatically classifies user reviews as *Positive*, *Neutral*, or *Negative* with confidence scores.

Built as a learning project demonstrating modern ML-backed web development practices.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **User Authentication** | JWT-based secure auth (register, login, protected routes) |
| **Event Discovery** | Browse, search, and filter events by category, city, keywords |
| **Personalized Recommendations** | Hybrid ML (Content + Collaborative Filtering) with Cold-Start fallback |
| **Sentiment Analysis** | Auto-classifies review sentiment (Positive/Neutral/Negative) with confidence |
| **User Dashboard** | Track registrations, view history, see personalized suggestions |
| **Review System** | Star ratings + text reviews with AI-powered sentiment badges |
| **Interaction Tracking** | Records views, clicks, favorites, registrations for ML training |
| **Admin Category Management** | Create and manage event categories |

---

## 🛠 Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | High-performance async Python web framework |
| **SQLAlchemy 2.0** | ORM with async support |
| **Microsoft SQL Server** | Production-grade relational database |
| **scikit-learn** | ML models (TF-IDF + Logistic Regression, SVD for CF) |
| **Pydantic v2** | Data validation & serialization |
| **python-jose** | JWT token handling |
| **bcrypt** | Password hashing |
| **Alembic** | Database migrations |
| **pytest** | Testing framework |

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 19** | Component-based UI |
| **Vite** | Lightning-fast build tool |
| **React Router v7** | Client-side routing |
| **Zustand** | Lightweight state management |
| **Axios** | HTTP client with interceptors |
| **Lucide React** | Beautiful icons |
| **Oxlint** | Fast linting |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| **Docker & Docker Compose** | Containerized deployment |
| **Nginx** | Frontend reverse proxy |

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
# Edit backend/.env with secure values:
# - SECRET_KEY (generate: python -c "import secrets; print(secrets.token_hex(32))")
# - MSSQL_PASSWORD (strong password)

# Frontend (optional - only if custom API URL needed)
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
docker run -d --name sqlserver \
  -e ACCEPT_EULA=Y \
  -e MSSQL_SA_PASSWORD=YourPass123! \
  -p 1433:1433 \
  mcr.microsoft.com/mssql/server:2022-latest

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
| `SECRET_KEY` | **Required** JWT signing key (32+ chars) | — |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `60` |
| `MSSQL_SERVER` | Database host | `localhost` |
| `MSSQL_PORT` | Database port | `1433` |
| `MSSQL_DATABASE` | Database name | `novaticket` |
| `MSSQL_USER` | Database user | `sa` |
| `MSSQL_PASSWORD` | **Required** Database password | — |
| `MSSQL_DRIVER` | ODBC driver name | `ODBC Driver 18 for SQL Server` |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | `http://localhost:5173,http://localhost:3000` |
| `MODEL_DIR` | ML artifacts directory | `models` |

### Frontend (`frontend/.env`)

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | Backend API URL (empty = relative) |

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000
```

### Authentication
All protected endpoints require `Authorization: Bearer <token>` header.

### Key Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/auth/register` | Register new user | ❌ |
| `POST` | `/auth/login` | Login, returns JWT | ❌ |
| `GET` | `/auth/me` | Get current user profile | ✅ |
| `GET` | `/events` | List events (paginated, filterable) | ❌ |
| `GET` | `/events/{id}` | Get event detail | ❌ |
| `POST` | `/interactions` | Record user interaction | ✅ |
| `GET` | `/interactions/me` | Get user's interactions | ✅ |
| `POST` | `/reviews` | Submit review (auto sentiment) | ✅ |
| `GET` | `/events/{id}/reviews` | Get event reviews | ❌ |
| `GET` | `/events/{id}/sentiment-summary` | Get sentiment stats | ❌ |
| `GET` | `/recommendations/me` | Personalized recommendations | ✅ |
| `GET` | `/recommendations/events/{id}/similar` | Similar events | ❌ |
| `GET` | `/categories` | List categories | ❌ |
| `POST` | `/categories` | Create category | ✅ |

### Interactive Docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🧪 Testing

### Run All Tests (Docker)
```bash
docker-compose exec -T backend python -m pytest tests/ -v
```

### Run Locally
```bash
cd backend
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
python -m pytest tests/ -v
```

### Test Results
```
============================= test session starts ==============================
collected 10 items

tests/test_auth.py::test_register_user_success PASSED
tests/test_auth.py::test_register_user_duplicate_email PASSED
tests/test_auth.py::test_login_success PASSED
tests/test_auth.py::test_login_invalid_password PASSED
tests/test_auth.py::test_get_me_success PASSED
tests/test_events.py::test_create_category PASSED
tests/test_events.py::test_get_categories PASSED
tests/test_events.py::test_get_events PASSED
tests/test_recommendations.py::test_get_recommendations PASSED
tests/test_reviews.py::test_create_review PASSED

============================== 10 passed in 3.13s ==============================
```

---

## 🐳 Docker Commands

| Command | Description |
|---------|-------------|
| `docker-compose up -d --build` | Build and start all services |
| `docker-compose down` | Stop and remove containers |
| `docker-compose down -v` | Stop and remove containers + volumes |
| `docker-compose logs -f backend` | Follow backend logs |
| `docker-compose exec backend python -m pytest tests/ -v` | Run tests in container |
| `docker-compose exec backend alembic upgrade head` | Run migrations |
| `docker-compose exec backend python training/train_sentiment.py` | Train sentiment model |
| `docker-compose exec backend python training/train_recommender.py` | Train recommender model |

---

## 🔄 CI/CD Pipeline

The project includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs on every push:

1. **Lint** — Oxlint (frontend) + Ruff (backend)
2. **Type Check** — mypy (backend)
3. **Test** — pytest with SQL Server service container
4. **Build** — Docker images for backend & frontend
5. **Security** — Trivy vulnerability scan

---

## 📝 Final Notes

- ✅ **All 10 tests pass** — covering auth, events, reviews, recommendations
- ✅ **Docker builds successfully** — multi-stage builds for minimal images
- ✅ **API fully documented** — Swagger + ReDoc available
- ✅ **ML models load at startup** — graceful degradation if artifacts missing
- ✅ **Secure by default** — bcrypt passwords, JWT tokens, CORS configured
- ✅ **Production-ready structure** — clean architecture, repository pattern, dependency injection

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License — feel free to use for learning or production.

---

**Built with ❤️ for learning modern AI-backed web development.**