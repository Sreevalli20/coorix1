# PharmaSense - Pharmaceutical R&D Intelligence Assistant

PharmaSense is an intelligent assistant for pharmaceutical R&D that provides insights into clinical trials, compounds, safety data, and research documents using a multi-agent architecture.

## Project Purpose

PharmaSense helps pharmaceutical researchers and clinical operations teams:
- Monitor clinical trial enrollment and identify trials below enrollment thresholds
- Analyze compound profiles across development stages
- Investigate safety signals and adverse events
- Retrieve relevant research documents and literature
- Synthesize comprehensive insights across multiple data sources

## Problem Being Solved

Pharmaceutical R&D teams struggle with:
- Fragmented data across trials, compounds, lab results, and research documents
- Time-consuming manual analysis of trial enrollment trends
- Difficulty identifying safety signals across multiple trials
- Inefficient retrieval of relevant research literature
- Lack of integrated views across development portfolios

PharmaSense addresses these challenges by providing a unified, intelligent interface for querying and analyzing pharmaceutical R&D data.

## Core Workflow

1. **User Query**: Natural language query about trials, compounds, safety, or research
2. **Intelligent Routing**: Query is analyzed and routed to appropriate specialist agent
3. **Data Retrieval**: Agent retrieves relevant data from SQLite database and document index
4. **Evidence Collection**: System collects evidence with confidence scores and source citations
5. **Response Synthesis**: Multi-agent synthesis provides comprehensive, grounded answers
6. **Uncertainty Quantification**: Response includes uncertainty level based on data quality

## Architecture Overview

PharmaSense uses a multi-agent architecture with:

- **FastAPI Backend**: RESTful API serving specialist agents
- **Specialist Agents**: Trial, Compound, Safety, Research, and Synthesis agents
- **Data Layer**: SQLite database with CSV data ingestion
- **Retrieval Layer**: Keyword-based document index for research documents
- **Frontend**: React/Vite/TypeScript interface for querying

## Technology Stack

### Backend
- **Python**: 3.14.6
- **Framework**: FastAPI 0.104.1
- **Data Storage**: SQLite (file-based, ephemeral)
- **Data Processing**: pandas
- **Retrieval**: Custom keyword-based document index
- **Validation**: Pydantic 2.5.0
- **Testing**: pytest 7.4.3, pytest-asyncio 0.21.1
- **HTTP Client**: httpx 0.25.2
- **System Monitoring**: psutil 5.9.6

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **HTTP Client**: fetch API

## Dataset

PharmaSense uses seven CSV datasets containing actual pharmaceutical R&D data:

| Dataset | Records | Description |
|---------|---------|-------------|
| `compounds.csv` | 100 | Compound library with chemical and biological properties |
| `clinical_trials.csv` | 110 | Clinical trial metadata and enrollment data |
| `trial_sites.csv` | 223 | Site-level trial information and enrollment |
| `lab_results.csv` | 220 | Laboratory experiment results for compounds |
| `adverse_events.csv` | 176 | Safety event reports from clinical trials |
| `research_documents.csv` | 46 | Internal research documents and literature reviews |
| `agent_interaction_logs.csv` | 78 | Historical agent query logs |

### Dataset Relationships

```
compounds (1) ----< (N) clinical_trials (1) ----< (N) trial_sites
    |                     |                        |
    |                     | (1) ----< (N) adverse_events
    |                     |
    |                     | (1) ----< (N) research_documents
    |
    | (1) ----< (N) lab_results
    |
    | (1) ----< (N) research_documents
```

## Components

### Specialist Agents

1. **Trial Intelligence Agent**: Analyzes trial enrollment, phase status, and trial metrics
2. **Compound Intelligence Agent**: Provides compound profiles, target protein analysis, and therapeutic area insights
3. **Safety Intelligence Agent**: Investigates adverse events, safety signals, and provides triage recommendations
4. **Research Document Agent**: Retrieves and analyzes research documents using keyword search
5. **Synthesis Agent**: Combines insights from multiple agents for comprehensive analysis

### API Endpoints

- `GET /health` - Health check and system status
- `POST /api/query` - Main natural language query endpoint
- `POST /api/trials/intelligence` - Trial-specific queries
- `POST /api/compounds/intelligence` - Compound-specific queries
- `POST /api/safety/analyze` - Safety analysis queries
- `POST /api/research/retrieve` - Research document retrieval
- `POST /api/synthesis/synthesize` - Response synthesis
- `GET /api/compounds/{compound_id}` - Get compound profile
- `GET /api/trials/{trial_id}` - Get trial profile
- `GET /api/safety/triage/{trial_id}` - Get safety triage for trial

## Installation

### Prerequisites
- Python 3.14.6
- Node.js (for frontend development)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -m pytest tests/ -v
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Running the Application

### Backend

```bash
cd backend

# Activate virtual environment
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # macOS/Linux

# Start backend server
python main.py
```

The backend will start on `http://localhost:8000`

### Frontend

```bash
cd frontend

# Start development server
npm run dev
```

The frontend will start on `http://localhost:5173`

## Running Tests

### Backend Tests

```bash
cd backend

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_agents.py -v

# Run specific test class
python -m pytest tests/test_agents.py::TestTrialAgent -v

# Run specific test
python -m pytest tests/test_agents.py::TestTrialAgent::test_enrollment_query_with_phase_and_area -v
```

### Demo Workflow Tests

```bash
cd backend

# Run all four demo workflows
python tests/demo_workflows.py
```

## Demo Workflows

### Workflow 1: Trial Enrollment Analysis
**Query**: "Which Phase II oncology trials are below 60% enrollment right now?"

**Purpose**: Identify trials requiring enrollment intervention

**Expected Output**: List of Phase II oncology trials with enrollment below 60%, including trial IDs and enrollment percentages

### Workflow 2: Research Retrieval
**Query**: "What has our internal research said about JAK2 inhibitors and cardiotoxicity?"

**Purpose**: Retrieve relevant research documents on specific topics

**Expected Output**: Ranked list of research documents with relevance scores, titles, and snippets

### Workflow 3: Safety Triage
**Query**: "A site just reported a serious adverse event for Trial TRL-0032 — triage it."

**Purpose**: Prioritize safety events requiring immediate attention

**Expected Output**: Safety summary including total events, serious events, risk level, and most common events

### Workflow 4: Compound Profile
**Query**: "Give me the full picture on compound DKU-1001: labs, trials, safety, and related literature."

**Purpose**: Comprehensive compound analysis across all data sources

**Expected Output**: Synthesized view including compound details, associated trials, lab results, safety data, and research documents

## Render Free Deployment

PharmaSense is configured for Render Free tier deployment.

### Deployment Configuration

The `render.yaml` file configures the deployment:

```yaml
services:
  - type: web
    name: pharmasense-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
      - key: PORT
        value: 8000
```

### Deployment Steps

1. Push code to GitHub repository
2. Connect repository to Render
3. Render will automatically detect `render.yaml`
4. Deploy using Free tier web service
5. Application will be available at `https://pharmasense-api.onrender.com`

### Deployment Notes

- SQLite database is recreated on startup from CSV files
- Document index is built on startup
- Data is ephemeral (no persistent storage on Free tier)
- Memory usage optimized for 512MB limit
- Fast startup time (<30s data loading)

## Environment Requirements

### Backend
- Python 3.14.6
- No API keys required
- No external databases required
- No paid services required

### Frontend
- Node.js 16+
- npm or yarn

## Repository Structure

```
coorix1/
├── backend/
│   ├── app/
│   │   ├── agents/          # Specialist agent implementations
│   │   ├── api/             # FastAPI endpoints
│   │   ├── data/            # Database and models
│   │   ├── retrieval/       # Document indexing and search
│   │   └── utils/           # Utility functions
│   ├── data/                # CSV datasets
│   ├── tests/               # Test suite
│   ├── main.py              # Backend entry point
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API client
│   │   └── types/           # TypeScript types
│   └── package.json         # Node dependencies
├── docs/
│   ├── ARCHITECTURE.md      # Architecture documentation
│   └── DATA_DICTIONARY.md   # Dataset documentation
├── render.yaml             # Render deployment config
└── README.md               # This file
```

## Limitations

### Current Limitations
- Ephemeral storage (data reloaded on each restart)
- No persistent user sessions
- No external LLM integration (rule-based synthesis)
- Single instance deployment (no horizontal scaling)
- Document retrieval uses keyword matching (not semantic search)

### Data Limitations
- Static dataset (no real-time updates)
- Limited to 100 compounds, 110 trials
- Research documents limited to 46 documents
- No external literature database integration

### Deployment Limitations
- Render Free tier: 512MB RAM limit
- No persistent disk storage
- Ephemeral file system
- Cold start time for data loading

## Future Enhancements

### Potential Improvements
- External LLM integration for enhanced synthesis
- Semantic search for document retrieval
- Real-time data integration
- User authentication and session management
- Advanced visualizations and dashboards
- Export functionality (PDF reports)
- Multi-tenant support

## Contributing

Contributions are welcome. Please ensure:
- All tests pass before submitting
- Code follows existing patterns
- Documentation is updated
- No breaking changes to existing functionality

## License

This project is proprietary software for PharmaSense R&D.

## Support

For issues or questions, please contact the development team or submit an issue through the project repository.
