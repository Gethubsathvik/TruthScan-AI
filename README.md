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

## 📰 Trusted News Sources
### 📺 Live News Channels

| Source | URL |
|--------|-----|
| 🇮🇳 NDTV | https://www.ndtv.com/ |
| 🇮🇳 Aaj Tak | https://www.aajtak.in/ |
| 🇮🇳 India Today | https://www.indiatoday.in/ |
| 🇮🇳 News18 | https://www.news18.com/ |
| 🇮🇳 Times Now | https://www.timesnownews.com/ |
| 🇮🇳 Republic World | https://www.republicworld.com/ |
| 🇮🇳 ABP Live | https://www.abplive.com/ |
| 🇮🇳 India TV | https://www.indiatvnews.com/ |
| 🇮🇳 TV9 Hindi | https://www.tv9hindi.com/ |
| 🇮🇳 Zee News | https://zeenews.india.com/ |
| 🇮🇳 DD News | https://ddnews.gov.in/ |
| 🇮🇳 Sansad TV | https://sansadtv.nic.in/ |
| 🇮🇳 WIONews | https://www.wionews.com/ |
| 🇮🇳 CNBC TV18 | https://www.cnbctv18.com/ |
| 🇮🇳 The Hindu | https://www.thehindu.com/ |
| 🇮🇳 Times of India | https://timesofindia.indiatimes.com/ |
| 🇮🇳 Hindustan Times | https://www.hindustantimes.com/ |
| 🇮🇳 Indian Express | https://indianexpress.com/ |
| 🇮🇳 Economic Times | https://economictimes.indiatimes.com/ |
| 🇬🇧 BBC News | https://www.bbc.com/news |
| 🇺🇸 CNN | https://www.cnn.com/ |
| 🇬🇧 Reuters | https://www.reuters.com/ |
| 🇶🇦 Al Jazeera | https://www.aljazeera.com/ |
| 🇺🇸 AP News | https://apnews.com/ |
| 🇫🇷 France 24 | https://www.france24.com/ |
| 🇩🇪 DW News | https://www.dw.com/ |
| 🇪🇺 Euronews | https://www.euronews.com/ |
| 🇬🇧 Sky News | https://news.sky.com/ |
| 🇯🇵 NHK World | https://www3.nhk.or.jp/nhkworld/ |
| 🇺🇸 Bloomberg | https://www.bloomberg.com/ |
| 🇺🇸 CNBC | https://www.cnbc.com/ |

### 📺 Telugu News Channels

| Source | URL |
|--------|-----|
| 🇮🇳 TV9 Telugu | https://tv9telugu.com/ |
| 🇮🇳 NTV Telugu | https://www.ntvtelugu.com/ |
| 🇮🇳 TV5 News | https://www.tv5news.in/ |
| 🇮🇳 Andhra Jyothy | https://www.andhrajyothy.com/ |
| 🇮🇳 Sakshi | https://www.sakshi.com/ |
| 🇮🇳 Eenadu | https://www.eenadu.net/ |
| 🇮🇳 ETV Bharat | https://www.etvbharat.com/ |
| 🇮🇳 ABP Live AP | https://www.abplive.com/andhra-pradesh |
| 🇮🇳 ABP Live Telangana | https://www.abplive.com/telangana |
| 🇮🇳 10TV | https://www.10tv.in/ |
| 🇮🇳 HMTV Live | https://www.hmtvlive.com/ |
| 🇮🇳 V6 Velugu | https://www.v6velugu.com/ |
| 🇮🇳 T News | https://www.tnews.tv/ |
| 🇮🇳 Raj News Live | https://www.rajnewslive.com/ |
| 🇮🇳 CVR News | https://www.cvrnews.com/ |
| 🇮🇳 Mahaa TV | https://www.mahaatv.com/ |
| 🇮🇳 Telugu News18 | https://telugu.news18.com/ |
| 🇮🇳 The Hans India | https://www.thehansindia.com/ |
| 🇮🇳 Siasat | https://www.siasat.com/ |

### 📝 Articles & Analysis

| Source | URL |
|--------|-----|
| 🇺🇸 New York Times | https://www.nytimes.com/ |
| 🇬🇧 The Guardian | https://www.theguardian.com/ |
| 🇺🇸 Washington Post | https://www.washingtonpost.com/ |
| 🇺🇸 Wall Street Journal | https://www.wsj.com/ |
| 🇺🇸 The Atlantic | https://www.theatlantic.com/ |
| 🇺🇸 The New Yorker | https://www.newyorker.com/ |
| 🇺🇸 Time | https://time.com/ |
| 🇬🇧 The Economist | https://www.economist.com/ |
| 🌐 The Conversation | https://theconversation.com/ |
| 🇺🇸 ProPublica | https://www.propublica.org/ |
| 🇺🇸 Vox | https://www.vox.com/ |
| 🇺🇸 Slate | https://slate.com/ |
| 🇺🇸 Wired | https://www.wired.com/ |
| 🇺🇸 The Verge | https://www.theverge.com/ |
| 🇺🇸 MIT Tech Review | https://www.technologyreview.com/ |
| 🌐 National Geographic | https://www.nationalgeographic.com/ |
| 🇺🇸 Smithsonian | https://www.smithsonianmag.com/ |
| 🇺🇸 Scientific American | https://www.scientificamerican.com/ |
| 🇬🇧 Nature | https://www.nature.com/ |
| 🌐 Aeon | https://aeon.co/ |
| 🇺🇸 Longreads | https://www.longreads.com/ |
| 🌐 Longform | https://longform.org/ |
| 🌐 Medium | https://medium.com/ |
| 🌐 Substack | https://substack.com/ |
| 🇺🇸 Inc. | https://www.inc.com/ |
| 🇺🇸 Forbes | https://www.forbes.com/ |
| 🇺🇸 HBR | https://hbr.org/ |
| 🇺🇸 McKinsey Insights | https://www.mckinsey.com/insights/ |
| 🇺🇸 Fast Company | https://www.fastcompany.com/ |
| 🇺🇸 Entrepreneur | https://www.entrepreneur.com/ |
| 🇺🇸 ESPN | https://www.espn.com/ |
| 🇺🇸 ESPNcricinfo | https://www.espncricinfo.com/ |
| 🇺🇸 Sports Illustrated | https://www.si.com/ |
| 🇺🇸 GQ | https://www.gq.com/ |
| 🇺🇸 Vanity Fair | https://www.vanityfair.com/ |
| 🇺🇸 National Review | https://www.nationalreview.com/ |
| 🇺🇸 Foreign Policy | https://foreignpolicy.com/ |
| 🇺🇸 Foreign Affairs | https://foreignaffairs.com/ |

### 📰 Hindi News Sources

| Source | URL |
|--------|-----|
| 🇮🇳 Aaj Tak | https://www.aajtak.in/ |
| 🇮🇳 ABP Live Hindi | https://www.abplive.com/ |
| 🇮🇳 Amar Ujala | https://www.amarujala.com/ |
| 🇮🇳 Bhaskar | https://www.bhaskar.com/ |
| 🇮🇳 Jagran | https://www.jagran.com/ |
| 🇮🇳 Live Hindustan | https://www.livehindustan.com/ |
| 🇮🇳 Zee News Hindi | https://zeenews.india.com/ |
| 🇮🇳 News18 Hindi | https://hindi.news18.com/ |
| 🇮🇳 India TV | https://www.indiatvnews.com/ |
| 🇮🇳 TV9 Hindi | https://www.tv9hindi.com/ |
| 🇮🇳 Republic Bharat | https://www.republicbharat.com/ |
| 🇮🇳 Navbharat Times | https://navbharattimes.indiatimes.com/ |
| 🇮🇳 Jansatta | https://www.jansatta.com/ |
| 🇮🇳 Nai Dunia | https://www.naidunia.com/ |
| 🇮🇳 Hari Bhoomi | https://www.haribhoomi.in/ |

### 📰 Other Language Sources

| Language | Sources |
|----------|---------|
| Tamil | Dinamalar, Dinamani, Daily Thanthi, Dinakaran, Maalaimalar, Puthiya Thalaimurai, Polimer News, News18 Tamil, Zee News Tamil, Vikatan, Nakkheeran, Hindu Tamil |
| Kannada | Udayavani, Vijay Karnataka, Kannada News18, Public TV, TV9 Kannada, Prajavani, Kannada Prabha, Vartha Bharathi, Eesanje, Suvarna News |
| Malayalam | Manorama Online, Mathrubhumi, Asianet News, 24 News, Kaumudy Global, Madhyamam, Deepika, Deshabhimani, Malayalam News18, Media One, Reporter Live, Janmabhumi |
| Bengali | Ananda Bazar, Sangbad Pratidin, Bartaman Patrika, Aajkaal, Ei Samay, Kolkata TV, ABP Live Bengali, Bengali News18, Somoy News, Zee Bangla |
| Marathi | Loksatta, Lokmat, Esakal, Sakal Media, Maharashtra Times, Lokmat News18, Marathi ABP Live, Saam TV, TV9 Marathi, Zee Marathi, Pudhari News |
| Gujarati | Divya Bhaskar, Gujarat Samachar, Sandesh, ABP Live Gujarat, Gujarati News18, TV9 Gujarati, VTV Gujarati, Akila News, Gujarati Mid Day, Chitralekha |
| Punjabi | Ajit Jalandhar, Punjab Kesari, Jagbani Punjab, Punjabi ABP Live, Punjabi News18, PTC News, Punjabi Tribune, Rozana Spokesman, Punjabi Jagran |
| Odia | Sambad, Dharitri, Odisha TV, Kanak News, Prameya News, Odisha Bytes, News18 Odia, Zee News Odia, Nandighosh TV |
| Assamese | Asomiya Pratidin, Assam Tribune, Pratidin Time, DY 365, News18 Assam, Prag News, Guwahati Plus |
| Urdu | Siasat, Urdu Point, Qaumi Awaz, Etemaad Daily, Munsif Daily, Roznama Sahara, Baseerat Online |
| Kashmiri | Greater Kashmir, Rising Kashmir, Kashmir Observer |
| Nepali | Epaper Ekantipur, Nepal News |
| Konkani | Herald Goa, The Goan, Navhind Times |
| Sindhi | Sindhi Dunya, Sindhi Sangat |

> **Full source registry**: See `backend/app/data/news_sources.json` for all 179 sources with metadata.


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
