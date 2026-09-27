from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import time
from typing import Optional

from app.data.database import db
from app.retrieval.document_index import document_index
from app.data.models import (
    QueryRequest, QueryResponse,
    CompoundResponse, TrialResponse, SafetyTriage
)
from app.agents.trial_agent import TrialAgent
from app.agents.compound_agent import CompoundAgent
from app.agents.safety_agent import SafetyAgent
from app.agents.research_agent import ResearchAgent
from app.agents.synthesis_agent import SynthesisAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    logger.info("Starting PharmaSense backend...")
    
    try:
        # Initialize database
        db.connect()
        db.load_csv_data()
        
        # Initialize document index
        documents = db.get_all_research_documents()
        document_index.build_index(documents)
        
        logger.info("PharmaSense backend started successfully")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down PharmaSense backend...")
    db.close()


# Create FastAPI app
app = FastAPI(
    title="PharmaSense API",
    description="Pharmaceutical R&D Intelligence Assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize agents
trial_agent = TrialAgent()
compound_agent = CompoundAgent()
safety_agent = SafetyAgent()
research_agent = ResearchAgent()
synthesis_agent = SynthesisAgent()


# Main query endpoint
@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a natural language query"""
    try:
        # Route to appropriate agent
        query_lower = request.query.lower()
        
        # Determine which agent to use
        if "trial" in query_lower and ("enrollment" in query_lower or "phase" in query_lower):
            response = trial_agent.process_query(request.query)
        elif "compound" in query_lower:
            response = compound_agent.process_query(request.query)
        elif "adverse" in query_lower or "safety" in query_lower or "triage" in query_lower:
            response = safety_agent.process_query(request.query)
        elif "research" in query_lower or "literature" in query_lower or "document" in query_lower:
            response = research_agent.process_query(request.query)
        else:
            # Use synthesis agent for complex queries
            response = synthesis_agent.process_query(request.query)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Trial intelligence endpoint
@app.post("/api/trials/intelligence", response_model=QueryResponse)
async def trial_intelligence(request: QueryRequest):
    """Trial-specific intelligence endpoint"""
    try:
        response = trial_agent.process_query(request.query)
        return response
    except Exception as e:
        logger.error(f"Error in trial intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Compound intelligence endpoint
@app.post("/api/compounds/intelligence", response_model=QueryResponse)
async def compound_intelligence(request: QueryRequest):
    """Compound-specific intelligence endpoint"""
    try:
        response = compound_agent.process_query(request.query)
        return response
    except Exception as e:
        logger.error(f"Error in compound intelligence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Safety analysis endpoint
@app.post("/api/safety/analyze", response_model=QueryResponse)
async def safety_analysis(request: QueryRequest):
    """Safety analysis endpoint"""
    try:
        response = safety_agent.process_query(request.query)
        return response
    except Exception as e:
        logger.error(f"Error in safety analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Research retrieval endpoint
@app.post("/api/research/retrieve", response_model=QueryResponse)
async def research_retrieve(request: QueryRequest):
    """Research document retrieval endpoint"""
    try:
        response = research_agent.process_query(request.query)
        return response
    except Exception as e:
        logger.error(f"Error in research retrieval: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Synthesis endpoint
@app.post("/api/synthesis/synthesize", response_model=QueryResponse)
async def synthesize_response(request: QueryRequest):
    """Response synthesis endpoint"""
    try:
        response = synthesis_agent.process_query(request.query)
        return response
    except Exception as e:
        logger.error(f"Error in synthesis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Get compound profile
@app.get("/api/compounds/{compound_id}", response_model=CompoundResponse)
async def get_compound_profile(compound_id: str):
    """Get complete compound profile"""
    try:
        compound = db.get_compound(compound_id)
        if not compound:
            raise HTTPException(status_code=404, detail="Compound not found")
        
        # Get related data
        trials = db.execute_query(
            "SELECT * FROM clinical_trials WHERE compound_id = ?",
            (compound_id,)
        )
        lab_results = db.get_lab_results_by_compound(compound_id)
        documents = db.get_documents_by_compound(compound_id)
        
        return CompoundResponse(
            compound=compound,
            trials=trials,
            lab_results=lab_results,
            research_documents=documents
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting compound profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Get trial profile
@app.get("/api/trials/{trial_id}", response_model=TrialResponse)
async def get_trial_profile(trial_id: str):
    """Get complete trial profile"""
    try:
        trial = db.get_trial(trial_id)
        if not trial:
            raise HTTPException(status_code=404, detail="Trial not found")
        
        # Get related data
        compound = db.get_compound(trial["compound_id"])
        sites = db.get_trial_sites(trial_id)
        adverse_events = db.get_adverse_events_by_trial(trial_id)
        
        return TrialResponse(
            trial=trial,
            compound=compound,
            sites=sites,
            adverse_events=adverse_events
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trial profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Get safety triage for trial
@app.get("/api/safety/triage/{trial_id}", response_model=SafetyTriage)
async def get_safety_triage(trial_id: str):
    """Get safety triage for a trial"""
    try:
        safety_summary = db.get_safety_summary_by_trial(trial_id)
        return SafetyTriage(
            trial_id=trial_id,
            **safety_summary
        )
    except Exception as e:
        logger.error(f"Error getting safety triage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "PharmaSense API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "query": "/api/query",
            "trials": "/api/trials/intelligence",
            "compounds": "/api/compounds/intelligence",
            "safety": "/api/safety/analyze",
            "research": "/api/research/retrieve",
            "synthesis": "/api/synthesis/synthesize"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
