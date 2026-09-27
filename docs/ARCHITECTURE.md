# PharmaSense Architecture

## Overview
PharmaSense is a pharmaceutical R&D intelligence assistant built with a modern, cost-effective architecture optimized for Render Free tier deployment.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Browser                             │
│                   React/Vite/TypeScript                     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST API
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend                            │
│                  (Python 3.14.6)                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  API Layer                                             │ │
│  │  - Health endpoint                                    │ │
│  │  - Query endpoint                                      │ │
│  │  - Trial intelligence endpoint                         │ │
│  │  - Compound intelligence endpoint                      │ │
│  │  - Safety analysis endpoint                            │ │
│  │  - Research retrieval endpoint                         │ │
│  │  - Synthesis endpoint                                  │ │
│  │  - Compound profile endpoint                           │ │
│  │  - Trial profile endpoint                              │ │
│  │  - Safety triage endpoint                              │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Agent Layer                                           │ │
│  │  - Router / Planner Agent (BaseAgent)                 │ │
│  │  - Trial Intelligence Agent                            │ │
│  │  - Compound Intelligence Agent                         │ │
│  │  - Safety Intelligence Agent                           │ │
│  │  - Research Document Agent                             │ │
│  │  - Synthesis Agent                                     │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Data Layer                                           │ │
│  │  - SQLite database (local, ephemeral)                 │ │
│  │  - pandas for data manipulation                       │ │
│  │  - Keyword-based document index                       │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend
- **Framework:** FastAPI 0.104.1 (async, modern, automatic docs)
- **Data Storage:** SQLite (file-based, no external DB needed)
- **Data Processing:** pandas (for CSV loading and manipulation)
- **Retrieval:** Custom keyword-based document index (lightweight, no vector DB)
- **Validation:** Pydantic 2.5.0 (type safety, automatic validation)
- **Testing:** pytest 7.4.3 + pytest-asyncio 0.21.1
- **HTTP Client:** httpx 0.25.2
- **System Monitoring:** psutil 5.9.6

### Frontend
- **Framework:** React 18
- **Build Tool:** Vite (fast HMR, optimized builds)
- **Language:** TypeScript (type safety)
- **Styling:** Tailwind CSS (utility-first, small bundle)
- **HTTP Client:** fetch API (no external dependencies)
- **State Management:** React hooks (useState, useEffect, useContext)

### Deployment
- **Platform:** Render Free Tier
- **Backend:** Render Web Service (Python)
- **Frontend:** Render Static Site (or bundled with backend)
- **Database:** SQLite (recreated on startup from CSV files)
- **Constraints:**
  - 512MB RAM limit
  - Ephemeral storage (data loaded on startup)
  - No persistent disk storage
  - Free tier limits apply

## Component Design

### 1. Data Ingestion Module
**Purpose:** Load CSV files into SQLite database on startup

**Components:**
- `data_loader.py`: Loads all CSV files into pandas DataFrames
- `database.py`: Creates SQLite schema and inserts data
- `models.py`: Pydantic models for each table

**Flow:**
```
Startup → Load CSVs → Create SQLite DB → Index Documents → Ready
```

**Optimizations:**
- Lazy loading for large datasets
- Connection pooling
- Query optimization with indexes

### 2. Research Retrieval Module
**Purpose:** Retrieve relevant research documents using keyword-based search

**Components:**
- `document_index.py`: Keyword-based document indexing and search

**Algorithm:**
```python
# Keyword-based document retrieval
# - Tokenization: Simple word-level tokenization
# - Inverted Index: Maps tokens to document IDs
# - Scoring: Term frequency-based scoring
# - Ranking: Sort by relevance score
```

**Advantages:**
- No external vector database
- Fast for 46 documents
- Low memory footprint
- Easy to debug
- No dependencies on scikit-learn

### 3. Agent System
**Purpose:** Route queries to specialist agents and synthesize responses

**Components:**
- `base_agent.py`: Base class for all agents with common functionality
- `agents/trial_agent.py`: Trial intelligence specialist
- `agents/compound_agent.py`: Compound intelligence specialist
- `agents/safety_agent.py`: Adverse event specialist
- `agents/research_agent.py`: Research document specialist
- `agents/synthesis_agent.py`: Response synthesis and multi-agent orchestration

**Routing Logic:**
```python
def route_query(query: str) -> Agent:
    if "trial" in query.lower() and ("enrollment" in query.lower() or "phase" in query.lower()):
        return TrialAgent()
    elif "compound" in query.lower():
        return CompoundAgent()
    elif "adverse" in query.lower() or "safety" in query.lower() or "triage" in query.lower():
        return SafetyAgent()
    elif "research" in query.lower() or "literature" in query.lower() or "document" in query.lower():
        return ResearchAgent()
    else:
        return SynthesisAgent()  # Multi-agent orchestration
```

### 4. API Layer
**Purpose:** Expose functionality via REST API

**Endpoints:**
```
GET  /health                    Health check
POST /api/query                 Natural language query
POST /api/trials/intelligence   Trial-specific queries
POST /api/compounds/intelligence Compound-specific queries
POST /api/safety/analyze        Safety analysis
POST /api/research/retrieve     Document retrieval
POST /api/synthesis/synthesize  Response synthesis
```

**Response Format:**
```json
{
  "answer": "Natural language answer",
  "evidence": [
    {
      "source": "clinical_trials",
      "data": {...},
      "confidence": 0.95
    }
  ],
  "sources": ["TRL-0032", "CMP-1042"],
  "interpretation": "Human-readable interpretation",
  "uncertainty": "Low/Medium/High"
}
```

### 5. Frontend Components
**Purpose:** User interface for querying and visualizing results

**Components:**
- `App.tsx`: Main application component
- `QueryInterface.tsx`: Chat-like query interface
- `ResultsDisplay.tsx`: Structured results display
- `EvidencePanel.tsx`: Evidence source panel
- `AgentStatus.tsx`: Agent activity visualization
- `TrialAnalysis.tsx`: Trial-specific analysis view
- `CompoundAnalysis.tsx`: Compound-specific analysis view
- `SafetyTriage.tsx`: Safety event triage interface

**State Management:**
```typescript
interface AppState {
  query: string;
  results: QueryResult | null;
  loading: boolean;
  error: string | null;
  agentStatus: AgentStatus;
}
```

## Data Flow

### Query Processing Flow
```
User Query
    ↓
Frontend validation
    ↓
POST /api/query
    ↓
Router analyzes query
    ↓
Specialist agent(s) invoked
    ↓
Data retrieval (SQLite + BM25)
    ↓
Evidence collection
    ↓
Synthesis agent combines results
    ↓
Response with evidence
    ↓
Frontend displays results
```

### Example: "Which Phase II oncology trials are below 60% enrollment?"
```
Query → Router → TrialAgent
    ↓
SQLite query: SELECT * FROM clinical_trials WHERE trial_phase='Phase II' AND therapeutic_area='Oncology'
    ↓
Calculate enrollment percentage: actual_enrollment / target_enrollment
    ↓
Filter: percentage < 0.60
    ↓
Return trial list with enrollment details
    ↓
Synthesis: "Found 3 Phase II oncology trials below 60% enrollment..."
```

## Render Free Deployment Strategy

### Backend Deployment
**File Structure:**
```
backend/
├── main.py              # FastAPI app entry point
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── app/
│   ├── api/            # API routes
│   ├── agents/         # Agent implementations
│   ├── data/           # Data loading and models
│   ├── retrieval/      # Document retrieval
│   └── utils/          # Utilities
└── data/               # CSV files (loaded on startup)
```

**render.yaml:**
```yaml
services:
  - type: web
    name: pharmasense-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.14
      - key: PORT
        value: 8000
```

**Startup Optimization:**
```python
# main.py
@app.on_event("startup")
async def startup_event():
    # Load data into SQLite
    load_data()
    # Build document index
    build_document_index()
    # Pre-compute common queries
    cache_common_queries()
```

### Frontend Deployment
**Options:**
1. **Bundled with backend:** Serve static files from FastAPI
2. **Separate static site:** Render Static Site with CORS to backend

**Chosen Approach:** Bundled with backend (simpler, fewer moving parts)

**Static file serving:**
```python
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
```

### Memory Optimization
**Strategies:**
- Use SQLite instead of in-memory pandas for large datasets
- Lazy load research documents (index only, load full text on demand)
- Connection pooling for database
- Clear caches after requests
- Use generators instead of lists where possible

**Estimated Memory Usage:**
- SQLite database: ~50MB
- Document index: ~5MB
- Application code: ~30MB
- Overhead: ~100MB
- **Total: ~185MB** (well under 512MB limit)

## Security Considerations

### API Security
- CORS configuration for frontend
- Rate limiting (optional, can add if needed)
- Input validation via Pydantic
- SQL injection prevention (parameterized queries)

### Data Privacy
- No sensitive personal data in dataset
- No API keys required (local retrieval)
- Environment variables for any future external services

## Scalability Considerations

### Current Scale
- 100 compounds
- 110 clinical trials
- 223 trial sites
- 220 lab results
- 176 adverse events
- 46 research documents

### Scaling Strategy
- Current architecture handles 10x data easily
- For 100x scale, consider:
  - External database (PostgreSQL)
  - Vector database (if retrieval needs scale)
  - Caching layer (Redis)
  - Load balancing

## Monitoring and Logging

### Logging
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"Query processed: {query} in {latency}ms")
```

### Health Check
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": check_database(),
        "document_index": check_index(),
        "memory": get_memory_usage()
    }
```

## Testing Strategy

### Unit Tests
- Data loading tests
- Agent logic tests
- Retrieval accuracy tests
- API endpoint tests

### Integration Tests
- End-to-end query processing
- Agent orchestration
- Frontend-backend integration

### Demo Workflow Tests
- Test all 4 required workflows
- Verify actual data usage
- Check evidence quality

## Development Workflow

### Local Development
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Production Build
```bash
# Frontend
cd frontend
npm run build

# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Future Enhancements

### Phase 2 (Post-MVP)
- Add actual LLM integration behind `call_llm()` abstraction
- Implement user authentication
- Add query history and favorites
- Enhanced visualizations (charts, graphs)
- Export functionality (PDF reports)

### Phase 3 (Scale)
- External vector database for larger document corpus
- Real-time data streaming
- Advanced ML models for prediction
- Multi-tenant support
- Advanced analytics dashboard

## Limitations

### Current Limitations
- Ephemeral storage (data reloaded on restart)
- No persistent user sessions
- No external LLM (rule-based synthesis)
- Single instance (no horizontal scaling)

### Mitigations
- Fast startup time (<30s data loading)
- Stateless design (can scale horizontally with load balancer)
- LLM abstraction ready for future integration
- Efficient data loading (SQLite vs in-memory)

## Conclusion

This architecture provides a complete, working PharmaSense application optimized for Render Free tier deployment. It uses lightweight, practical technologies that can scale as needed while maintaining cost-effectiveness and simplicity.
