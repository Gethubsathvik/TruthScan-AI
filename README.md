# TruthScan AI 🛡️

An evidence-based real-time news verification system that analyzes claims using real-time web evidence instead of static datasets.

[![Backend Tests](https://github.com/Gethubsathvik/TruthScan-AI-/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/Gethubsathvik/TruthScan-AI-/actions/workflows/backend-tests.yml)
[![Frontend Build](https://github.com/Gethubsathvik/TruthScan-AI-/actions/workflows/frontend-build.yml/badge.svg)](https://github.com/Gethubsathvik/TruthScan-AI-/actions/workflows/frontend-build.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- **Real-Time Evidence**: No static datasets — all evidence from live web search
- **Multilingual Support**: 179 news sources across 18 Indian languages
- **URL Auto-Scan**: Submit URLs and get True/Fake verdicts automatically
- **Three-Cycle Verification**: Claim extraction → Evidence gathering → Cross-validation
- **Source Credibility Analysis**: Evaluates publisher independence and reliability
- **Media Reuse Detection**: Identifies recycled images/videos from old contexts
- **Transparent Verdicts**: Every decision comes with evidence and explanations

## 🌐 Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| 🪟 Windows | ✅ Fully Supported | Native PowerShell & CMD support |
| 🐧 Linux | ✅ Fully Supported | Tested on Ubuntu, Debian, RHEL |
| 🤖 Android | ✅ Supported | Termux compatible |
| 🍎 macOS | ✅ Supported | Homebrew compatible |

## 💻 Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Backend | Python 3.9+ / FastAPI | Async API server, verification pipeline |
| Frontend | React 18 + TypeScript | Modern UI with type safety |
| Styling | Tailwind CSS | Utility-first responsive design |
| Database | SQLite (dev) / PostgreSQL (prod) | SQLAlchemy ORM |
| AI | OpenAI GPT-4o-mini | Claim extraction, reasoning |
| Search | Tavily / Brave / SerpAPI | Real-time web evidence |

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- OpenAI API key
- Search API key (Tavily recommended)

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys

# Run server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` for the UI and `http://localhost:8000/docs` for API documentation.

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/verify` | Verify a claim (text or URL) |
| `GET` | `/api/v1/verification/{id}` | Get verification result |
| `GET` | `/api/v1/history` | List verification history |
| `GET` | `/api/v1/auto-scan/trending` | Get trending news |
| `GET` | `/api/v1/auto-scan/daily-updates` | Get daily updates |
| `POST` | `/api/v1/auto-scan/scan-urls` | Scan URLs for True/Fake verdict |
| `POST` | `/api/v1/auto-scan/run` | Trigger full auto-scan |

### Example: Scan URLs

```bash
curl -X POST "http://localhost:8000/api/v1/auto-scan/scan-urls" \
  -H "Content-Type: application/json" \
  -d '["https://www.bbc.com/news/article", "https://www.thehindu.com/news/article"]'
```

## 🌍 Languages Supported

18 Indian languages: English, Hindi, Telugu, Tamil, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi, Odia, Assamese, Urdu, Kashmiri, Nepali, Konkani, Sindhi, and Multilingual sources.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (TypeScript)                │
└─────────────────────────────┬───────────────────────────────┘
                              ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Router Layer                       │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Verification Pipeline                        │
│  Claim Extraction → Evidence Search → Scoring → Verdict     │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│     OpenAI API | Tavily/Brave/SerpAPI | Web Scraping        │
└─────────────────────────────────────────────────────────────┘
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend build check
cd frontend
npm run build
```

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
