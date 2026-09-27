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
        
        # Determine query type and return natural routing message
        if "trial" in query_lower and ("enrollment" in query_lower or "phase" in query_lower):
            return QueryResponse(
                answer="I'll help you analyze trial enrollment and phase information.",
                evidence=[],
                sources=[],
                interpretation="This query focuses on clinical trial metrics."
            )
        elif "compound" in query_lower:
            return QueryResponse(
                answer="I'll help you analyze compound information.",
                evidence=[],
                sources=[],
                interpretation="This query focuses on compound intelligence."
            )
        elif "adverse" in query_lower or "safety" in query_lower or "triage" in query_lower:
            return QueryResponse(
                answer="I'll help you analyze safety information and adverse events.",
                evidence=[],
                sources=[],
                interpretation="This query focuses on safety intelligence."
            )
        elif "research" in query_lower or "literature" in query_lower or "document" in query_lower:
            return QueryResponse(
                answer="I'll help you search research documents and literature.",
                evidence=[],
                sources=[],
                interpretation="This query focuses on research document retrieval."
            )
        else:
            return QueryResponse(
                answer="I'll help you analyze this question using the available pharmaceutical research data.",
                evidence=[],
                sources=[],
                interpretation="This query may require analysis across multiple data sources."
            )
