# NextNoteBook

AI-powered document summarization and Q&A application with Corrective RAG, hybrid retrieval, and multi-agent LangGraph workflows.

![Vue](https://img.shields.io/badge/Vue-3.4-green?logo=vue.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-blue?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.11+-yellow?logo=python)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0-green?logo=mongodb)
![Milvus](https://img.shields.io/badge/Zilliz-Cloud-purple)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-orange)

## Screenshots

### Notebook View - Chat & AI Studio
![Notebook View](docs/images/notebook-view.png)

### Quiz View - Practice Mode
![Quiz View](docs/images/quiz-view.png)

## Features

- **User Authentication**: Login/Signup with JWT tokens and bcrypt password hashing
- **Document Upload**: Support PDF, DOCX, TXT files (up to 50MB)
- **AI Chat (CRAG)**: Corrective RAG with query rewriting and web search fallback
- **Hybrid Retrieval**: BM25 lexical search + vector semantic search combined
- **Summarization**: Document-level and notebook-level summaries via LangGraph workflow
- **Quiz Generation (MCQ)**: Multi-step pipeline with diversity sampling and validation
- **FAQ Generation**: Topic-aware FAQ with single/multi-topic routing and deduplication
- **Document Classification**: ACM Computing Classification System with embedding-based similarity
- **Semantic Search**: Zilliz Cloud (Milvus managed) with configurable similarity threshold
- **Input Guardrails**: Rule-based junk detection + LLM-based safety checks
- **Query Router**: Hybrid rule-based + LLM classifier for intelligent routing (greeting/chitchat/meta/retrieval)
- **Citation Policy**: Strict `[cid:X]` citation enforcement with validation
- **Evaluation Framework**: MultiHopRAG-based eval for retrieval and generation quality
- **Multi-LLM Provider**: Support Groq, xAI (Grok), Google Gemini, OpenAI

## Tech Stack

### Backend
| Component | Technology |
|-----------|------------|
| Framework | FastAPI + Python 3.11+ |
| LLM | Groq (Llama 3.3 70B) / xAI (Grok) / Gemini / OpenAI |
| Embedding | Google Gemini text-embedding-004 (768d) |
| Vector DB | Zilliz Cloud (Milvus managed) |
| Lexical Search | BM25 (rank_bm25) |
| Database | MongoDB (local) |
| Orchestration | LangGraph (4 workflows: RAG, MCQ, FAQ, Summarizer) |
| Auth | JWT + bcrypt |
| Web Search | Tavily / SerpAPI / Google CSE (optional) |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | Vue 3 + TypeScript |
| Build Tool | Vite 5 |
| Styling | TailwindCSS |
| State | Pinia |
| HTTP Client | Axios |
| Icons | Lucide Vue Next |

## Project Structure

```
NextNoteBook/
├── backend/
│   ├── app/
│   │   ├── api/routes/           # API endpoints (auth, notebooks, documents, chat, quiz, faq, summary, categories, admin)
│   │   ├── core/                 # Document processing, text chunking, text cleaning
│   │   ├── database/             # MongoDB & Milvus clients
│   │   ├── models/               # Pydantic schemas (user, notebook, document, chat, quiz, faq, summary, category)
│   │   ├── services/
│   │   │   ├── rag/              # CRAG workflow (retrieve → grade → rewrite/web_search → generate)
│   │   │   ├── mcq_generator/    # MCQ workflow (retrieve → diversity_sampling → batch_generate → validate → format)
│   │   │   ├── faq_generator/    # FAQ workflow (retrieve → topic_extraction → generate → deduplicate)
│   │   │   ├── summarizer/       # Summarizer workflow (retrieve → route_by_style → document/notebook summary)
│   │   │   └── shared/           # LLM, embedding, auth, BM25, web search, query router, guardrails, citation, classification
│   │   ├── utils/                # Logger, exceptions
│   │   └── config.py             # Pydantic settings from .env
│   └── uploads/                  # Uploaded files
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/             # ChatWindow, ChatInput, MessageBubble, WebSourcesPanel
│   │   │   ├── common/           # ConfirmDialog, ErrorMessage, LoadingSpinner, Toast
│   │   │   ├── notebook/         # NotebookOverview, SourcesList, StudioPanel, UploadModal, CategoryBadge/Filter
│   │   │   └── quiz/             # QuestionCard, QuestionNavigator, QuizProgress, ResultsSummary
│   │   ├── views/                # AuthView, HomeView, NotebookView, QuizView
│   │   ├── stores/               # Pinia stores (auth, chat, notebook, quiz)
│   │   ├── services/             # API client (Axios)
│   │   ├── router/               # Vue Router
│   │   └── types/                # TypeScript type definitions
│   └── package.json
├── eval/                         # Evaluation framework (MultiHopRAG)
│   ├── ingest_corpus.py          # Ingest corpus into Milvus
│   ├── prepare_qrels.py          # Build query relevance judgments
│   ├── retrieval_eval.py         # BM25 vs Vector vs Hybrid retrieval eval
│   ├── generation_eval.py        # End-to-end QA + citation eval
│   ├── run_eval.py               # One-shot runner
│   └── sample_*.json             # Dataset files (182 docs, 170 questions)
├── docker-compose.yml
└── README_.md
```

## LangGraph Workflows

### 1. Corrective RAG (CRAG) - Chat

```
START → retrieve → grade_documents → [decision]
                                        ↓ enough docs → generate → END
                                        ↓ few docs (1st try) → rewrite_query → retrieve (loop)
                                        ↓ few docs (2nd try) → web_search → generate → END
```

### 2. MCQ Generator - Quiz

```
START → retrieve_chunks → diversity_sampling → batch_generate → validate_questions → format_output → END
```

### 3. FAQ Generator

```
START → retrieve_chunks → topic_extraction → [route]
                                                ↓ single topic → generate_focused_faq → deduplicate → END
                                                ↓ multi topic → generate_diverse_faq → deduplicate → END
```

### 4. Summarizer

```
START → retrieve_documents → [route_by_style]
                                ↓ document → generate_document_summary → END
                                ↓ notebook → generate_notebook_overview → END
```

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **MongoDB** (running locally)
- **API Keys** (at least one LLM provider):
  - Groq API Key (free at https://console.groq.com)
  - Google Gemini API Key (for embeddings)
  - Zilliz Cloud account (free tier at https://cloud.zilliz.com)

### 1. Clone & Setup

```bash
git clone <repo-url>
cd NextNoteBook
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys (see Configuration section)
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### 4. Start MongoDB

```bash
# Windows (if MongoDB is installed as service)
net start MongoDB

# Or run directly
mongod

# Linux/Mac
sudo systemctl start mongod
```

### 5. Run Application

**Manual start:**
```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 6. Access Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |

## Configuration

Create `backend/.env` file:

```env
# ===========================================
# LLM PROVIDER (choose one: groq, xai, gemini, openai)
# ===========================================
LLM_PROVIDER=groq

# Groq API (FREE - 30 req/min)
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# xAI (Grok) - optional
XAI_API_KEY=your_xai_api_key_here
XAI_MODEL=grok-beta

# Google Gemini (for embeddings + optional LLM)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
GEMINI_EMBEDDING_MODEL=models/text-embedding-004

# OpenAI - optional
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# ===========================================
# VECTOR DATABASE - Zilliz Cloud
# ===========================================
ZILLIZ_CLOUD_URI=https://your-instance.cloud.zilliz.com
ZILLIZ_CLOUD_TOKEN=your_zilliz_token_here
ZILLIZ_COLLECTION_NAME=documents

# ===========================================
# MONGODB (local)
# ===========================================
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=notebooklm

# ===========================================
# JWT AUTHENTICATION
# ===========================================
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080

# ===========================================
# RETRIEVAL & CHUNKING
# ===========================================
EMBEDDING_DIMENSION=768
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.3

# ===========================================
# WEB SEARCH (optional - for CRAG fallback)
# ===========================================
TAVILY_API_KEY=your_tavily_key_here
# SERPAPI_API_KEY=your_serpapi_key_here
# GOOGLE_API_KEY=your_google_api_key_here
# GOOGLE_CSE_ID=your_google_cse_id_here

# ===========================================
# GUARDRAILS & ROUTING
# ===========================================
ENABLE_INPUT_GUARDRAILS=true
ENABLE_INPUT_SAFETY=true
ENABLE_INTELLIGENT_ROUTING=true
MAX_INPUT_LENGTH=2000

# ===========================================
# APP SETTINGS
# ===========================================
DEBUG=true
MAX_FILE_SIZE_MB=50
```

## Usage

### 1. Create Account
- Go to http://localhost:5173
- Register a new account and login

### 2. Create Notebook
- Click "Create New Notebook"
- Enter notebook name

### 3. Upload Documents
- Open a notebook
- Upload PDF, DOCX, or TXT files
- Documents are chunked, embedded, and stored in Milvus

### 4. Chat with Documents
Ask questions about your uploaded documents. The CRAG workflow will:
1. Retrieve relevant chunks (hybrid: BM25 + vector)
2. Grade document relevance
3. Rewrite query if needed, or fall back to web search
4. Generate answer with strict `[cid:X]` citations

### 5. Special Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/quiz [count]` | Generate MCQ quiz | `/quiz 10` |
| `/summary` | Summarize documents | `/summary` |
| `/faq [count]` | Generate FAQ | `/faq 5` |
| `/help` | Show commands | `/help` |

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user

### Notebooks
- `GET /api/v1/notebooks/` - List user's notebooks
- `POST /api/v1/notebooks/` - Create notebook
- `GET /api/v1/notebooks/{id}` - Get notebook
- `DELETE /api/v1/notebooks/{id}` - Delete notebook

### Documents
- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/documents/notebook/{notebook_id}` - List documents
- `DELETE /api/v1/documents/{id}` - Delete document

### Chat
- `POST /api/v1/chat/` - Send message (CRAG workflow)

### Quiz
- `POST /api/v1/quiz/` - Generate MCQ quiz

### Summary
- `POST /api/v1/summary/` - Generate summary

### FAQ
- `POST /api/v1/faq/` - Generate FAQ

### Categories
- `GET /api/v1/categories/` - List categories
- `POST /api/v1/categories/` - Create/update categories

### Admin
- `POST /api/v1/admin/reset-vectors` - Reset vector DB
- `POST /api/v1/admin/reset-mongodb` - Reset MongoDB

## Evaluation Framework

The `eval/` directory contains a MultiHopRAG-based evaluation framework that tests the production pipeline end-to-end:

- **Retrieval eval**: BM25 vs Vector vs Hybrid comparison (Recall@K, MRR, MAP)
- **Generation eval**: QA quality (Exact Match, Token F1) + Citation quality (coverage, validity, precision/recall)

```bash
# One-shot: ingest + qrels + retrieval + generation eval
cd eval
python run_eval.py --mode all --corpus eval/sample_corpus.json --qa eval/sample_MultiHopRAG.json --notebook-id eval_multihoprag --reset
```

See [eval/README.md](eval/README.md) for detailed instructions.

## Docker Deployment

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# Stop
docker-compose down
```

| Service | URL |
|---------|-----|
| Frontend (nginx) | http://localhost:3000 |
| Backend API | http://localhost:8000 |

## Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   Vue Frontend  │────▶│   FastAPI Backend     │────▶│  Zilliz Cloud   │
│   (Port 5173)   │     │    (Port 8000)        │     │  (Vector DB)    │
└─────────────────┘     └──────────┬───────────┘     └─────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
           ┌────────▼─────┐ ┌─────▼──────┐ ┌────▼────────┐
           │   MongoDB    │ │  BM25      │ │ Web Search  │
           │  (Users,     │ │ (Lexical)  │ │ (Tavily/    │
           │  Notebooks,  │ │            │ │  SerpAPI)   │
           │  Documents)  │ └────────────┘ └─────────────┘
           └──────────────┘
                    │
           ┌────────▼──────────────────────────────────┐
           │            LangGraph Workflows             │
           │  ┌───────┐ ┌─────┐ ┌─────┐ ┌───────────┐ │
           │  │ CRAG  │ │ MCQ │ │ FAQ │ │ Summarizer│ │
           │  └───────┘ └─────┘ └─────┘ └───────────┘ │
           └────────────────────┬───────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   LLM Providers       │
                    │  Groq / xAI / Gemini  │
                    │  / OpenAI             │
                    └───────────────────────┘
```

## Troubleshooting

### MongoDB Connection Error
```
MongoServerError: connect ECONNREFUSED
```
**Solution**: Start MongoDB service
```bash
# Windows
net start MongoDB
# Linux
sudo systemctl start mongod
```

### LLM API Rate Limit
```
Error: Rate limit exceeded
```
**Solution**: Groq free tier allows 30 requests/minute. Wait and retry, or switch to another provider in `.env`.

### Zilliz Connection Error
```
Error: Failed to connect to Zilliz
```
**Solution**: Check `ZILLIZ_CLOUD_URI` and `ZILLIZ_CLOUD_TOKEN` in `.env`.

### Frontend Proxy Error
```
[vite] http proxy error: ECONNREFUSED
```
**Solution**: Backend is not running. Start backend first.

## License

MIT

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request
