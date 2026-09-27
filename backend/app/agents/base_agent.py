from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import logging
from app.data.database import db
from app.data.models import Evidence, QueryResponse

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all specialist agents"""
    
    def __init__(self, name: str):
        self.name = name
        self.queries_processed = 0
        
    @abstractmethod
    def process_query(self, query: str, context: Optional[Dict] = None) -> QueryResponse:
        """Process a query and return a response"""
        pass
    
    def create_evidence(self, source: str, data: dict, confidence: float, description: str) -> Evidence:
        """Create an evidence object"""
        return Evidence(
            source=source,
            data=data,
            confidence=confidence,
            description=description
        )
    
    def calculate_confidence(self, data_quality: str, completeness: float) -> float:
        """Calculate confidence score based on data quality and completeness"""
        base_confidence = 0.5
        if data_quality == "high":
            base_confidence += 0.3
        elif data_quality == "medium":
            base_confidence += 0.1
        
        completeness_factor = min(completeness, 1.0) * 0.2
        return min(base_confidence + completeness_factor, 1.0)
    
    def determine_uncertainty(self, confidence: float) -> str:
        """Determine uncertainty level based on confidence"""
        if confidence >= 0.8:
            return "Low"
        elif confidence >= 0.5:
            return "Medium"
        else:
            return "High"


class RouterAgent(BaseAgent):
    """Router agent that routes queries to appropriate specialist agents"""
    
    def __init__(self):
        super().__init__("Router / Planner Agent")
        
    def process_query(self, query: str, context: Optional[Dict] = None) -> QueryResponse:
        """Route query to appropriate agent"""
        query_lower = query.lower()
        
        # Determine query type
        if "trial" in query_lower and ("enrollment" in query_lower or "phase" in query_lower):
            return {
                "answer": "Query routed to Trial Intelligence Agent",
                "evidence": [],
                "sources": [],
                "interpretation": "This query requires trial enrollment analysis",
                "uncertainty": "Low",
                "agent_used": "Trial Intelligence Agent",
                "processing_time_ms": 0
            }
        elif "compound" in query_lower:
            return {
                "answer": "Query routed to Compound Intelligence Agent",
                "evidence": [],
                "sources": [],
                "interpretation": "This query requires compound analysis",
                "uncertainty": "Low",
                "agent_used": "Compound Intelligence Agent",
                "processing_time_ms": 0
            }
        elif "adverse" in query_lower or "safety" in query_lower or "triage" in query_lower:
            return {
                "answer": "Query routed to Safety Intelligence Agent",
                "evidence": [],
                "sources": [],
                "interpretation": "This query requires safety analysis",
                "uncertainty": "Low",
                "agent_used": "Safety Intelligence Agent",
                "processing_time_ms": 0
            }
        elif "research" in query_lower or "literature" in query_lower or "document" in query_lower:
            return {
                "answer": "Query routed to Research Document Agent",
                "evidence": [],
                "sources": [],
                "interpretation": "This query requires document retrieval",
                "uncertainty": "Low",
                "agent_used": "Research Document Agent",
                "processing_time_ms": 0
            }
        else:
            return {
                "answer": "Query routed to General Synthesis Agent",
                "evidence": [],
                "sources": [],
                "interpretation": "This query requires multi-agent synthesis",
                "uncertainty": "Medium",
                "agent_used": "General Synthesis Agent",
                "processing_time_ms": 0
            }
