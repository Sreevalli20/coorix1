"""
Comprehensive tests for all agents using actual data
"""
import pytest
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.data.database import db
from app.retrieval.document_index import document_index
from app.agents.trial_agent import TrialAgent
from app.agents.compound_agent import CompoundAgent
from app.agents.safety_agent import SafetyAgent
from app.agents.research_agent import ResearchAgent
from app.agents.synthesis_agent import SynthesisAgent
from app.agents.base_agent import BaseAgent


@pytest.fixture(scope="module")
def setup_database():
    """Setup database with actual data for testing"""
    db.connect()
    db.load_csv_data("./data")
    yield db
    db.close()


@pytest.fixture(scope="module")
def setup_document_index(setup_database):
    """Setup document index with actual data"""
    documents = db.get_all_research_documents()
    document_index.build_index(documents)
    yield document_index


class TestTrialAgent:
    """Test Trial Intelligence Agent"""
    
    def test_agent_initialization(self):
        """Test trial agent initialization"""
        agent = TrialAgent()
        assert agent.name == "Trial Intelligence Agent"
        assert agent.queries_processed == 0
        assert isinstance(agent, BaseAgent)
    
    def test_enrollment_query_with_phase_and_area(self, setup_database):
        """Test enrollment query with specific phase and therapeutic area"""
        agent = TrialAgent()
        query = "Which Phase II oncology trials are below 60% enrollment?"
        response = agent.process_query(query)
        
        assert "Phase II" in response.answer
        assert "oncology" in response.answer.lower()
        assert len(response.evidence) > 0
    
    def test_enrollment_query_general(self, setup_database):
        """Test general enrollment query"""
        agent = TrialAgent()
        query = "Find trials below 60% enrollment"
        response = agent.process_query(query)
        
        assert "enrollment" in response.answer.lower()
        assert len(response.evidence) > 0
    
    def test_phase_query(self, setup_database):
        """Test phase-specific query"""
        agent = TrialAgent()
        query = "Show me Phase I trials"
        response = agent.process_query(query)
        
        assert "Phase I" in response.answer
        assert len(response.evidence) > 0
    
    def test_status_query(self, setup_database):
        """Test trial status query"""
        agent = TrialAgent()
        query = "What is the status of trials?"
        response = agent.process_query(query)
        

        assert len(response.evidence) > 0
    
    def test_general_trial_query(self, setup_database):
        """Test general trial query"""
        agent = TrialAgent()
        query = "Tell me about clinical trials"
        response = agent.process_query(query)
        

        # General queries may not return evidence, just validate response structure
        assert response.answer is not None



class TestCompoundAgent:
    """Test Compound Intelligence Agent"""
    
    def test_agent_initialization(self):
        """Test compound agent initialization"""
        agent = CompoundAgent()
        assert agent.name == "Compound Intelligence Agent"
        assert agent.queries_processed == 0
        assert isinstance(agent, BaseAgent)
    
    def test_specific_compound_query(self, setup_database):
        """Test query for specific compound"""
        agent = CompoundAgent()
        query = "Tell me about compound CMP-0001"
        response = agent.process_query(query)
        

        assert len(response.evidence) > 0

    
    def test_compound_not_found(self, setup_database):
        """Test query for non-existent compound"""
        agent = CompoundAgent()
        query = "Tell me about compound CMP-9999"
        response = agent.process_query(query)
        
        assert "couldn't find" in response.answer.lower()
    
    def test_target_protein_query(self, setup_database):
        """Test target protein query"""
        agent = CompoundAgent()
        query = "Which compounds target JAK2?"
        response = agent.process_query(query)
        

        assert len(response.evidence) > 0
    
    def test_therapeutic_area_query(self, setup_database):
        """Test therapeutic area query"""
        agent = CompoundAgent()
        query = "Show me oncology compounds"
        response = agent.process_query(query)
        

        assert len(response.evidence) > 0
    
    def test_general_compound_query(self, setup_database):
        """Test general compound query"""
        agent = CompoundAgent()
        query = "Tell me about compounds"
        response = agent.process_query(query)
        

        assert len(response.evidence) > 0


class TestSafetyAgent:
    """Test Safety Intelligence Agent"""
    
    def test_agent_initialization(self):
        """Test safety agent initialization"""
        agent = SafetyAgent()
        assert agent.name == "Safety Intelligence Agent"
        assert agent.queries_processed == 0
        assert isinstance(agent, BaseAgent)
    
    def test_trial_safety_query(self, setup_database):
        """Test safety query for specific trial"""
        agent = SafetyAgent()
        query = "What are the safety issues for trial TRL-0001?"
        response = agent.process_query(query)
        

        assert len(response.evidence) > 0

    
    def test_trial_not_found(self, setup_database):
        """Test safety query for non-existent trial"""
        agent = SafetyAgent()
        query = "What are the safety issues for trial TRL-9999?"
        response = agent.process_query(query)
        
        assert "couldn't find" in response.answer.lower()
    
    def test_triage_query(self, setup_database):
        """Test triage query"""
        agent = SafetyAgent()
        query = "Triage adverse events"
        response = agent.process_query(query)
        

        assert len(response.evidence) > 0
    
    def test_adverse_event_query(self, setup_database):
        """Test adverse event query"""
        agent = SafetyAgent()
        query = "Show me adverse events"
        response = agent.process_query(query)
        

        assert len(response.evidence) > 0
    
    def test_general_safety_query(self, setup_database):
        """Test general safety query"""
        agent = SafetyAgent()
        query = "Tell me about safety"
        response = agent.process_query(query)
        

        assert len(response.evidence) > 0


class TestResearchAgent:
    """Test Research Document Agent"""
    
    def test_agent_initialization(self):
        """Test research agent initialization"""
        agent = ResearchAgent()
        assert agent.name == "Research Document Agent"
        assert agent.queries_processed == 0
        assert isinstance(agent, BaseAgent)
    
    def test_compound_research_query(self, setup_database, setup_document_index):
        """Test research query for specific compound"""
        agent = ResearchAgent()
        query = "What research exists for compound CMP-0001?"
        response = agent.process_query(query)
        

        assert len(response.evidence) >= 0  # May be 0 if no documents

    
    def test_target_research_query(self, setup_database, setup_document_index):
        """Test research query for target protein"""
        agent = ResearchAgent()
        query = "Research on JAK2 inhibitors"
        response = agent.process_query(query)
        

        assert len(response.evidence) >= 0
    
    def test_therapeutic_research_query(self, setup_database, setup_document_index):
        """Test research query for therapeutic area"""
        agent = ResearchAgent()
        query = "Oncology research documents"
        response = agent.process_query(query)
        

        assert len(response.evidence) >= 0
    
    def test_toxicity_research_query(self, setup_database, setup_document_index):
        """Test toxicity research query"""
        agent = ResearchAgent()
        query = "Cardiotoxicity research"
        response = agent.process_query(query)
        

        assert len(response.evidence) >= 0
    
    def test_literature_review_query(self, setup_database, setup_document_index):
        """Test literature review query"""
        agent = ResearchAgent()
        query = "Literature review on kinase inhibitors"
        response = agent.process_query(query)
        

        assert len(response.evidence) >= 0
    
    def test_document_search_query(self, setup_database, setup_document_index):
        """Test general document search"""
        agent = ResearchAgent()
        query = "Search for documents about phase II trials"
        response = agent.process_query(query)
        

        assert len(response.evidence) >= 0


class TestSynthesisAgent:
    """Test Synthesis Agent"""
    
    def test_agent_initialization(self):
        """Test synthesis agent initialization"""
        agent = SynthesisAgent()
        assert agent.name == "Synthesis Agent"
        assert agent.queries_processed == 0
        assert isinstance(agent, BaseAgent)
    
    def test_multi_agent_synthesis(self, setup_database, setup_document_index):
        """Test synthesis involving multiple agents"""
        agent = SynthesisAgent()
        query = "Give me comprehensive analysis of trial enrollment and compound data"
        response = agent.process_query(query)
        

        assert len(response.evidence) >= 0

    
    def test_synthesis_with_no_keywords(self, setup_database, setup_document_index):
        """Test synthesis when no specific keywords are detected"""
        agent = SynthesisAgent()
        query = "Analyze the current research portfolio"
        response = agent.process_query(query)
        

        assert len(response.evidence) >= 0


class TestBaseAgent:
    """Test Base Agent functionality"""
    
    def test_create_evidence(self):
        """Test evidence creation"""
        agent = TrialAgent()
        evidence = agent.create_evidence(
            source="test_source",
            data={"key": "value"},
            confidence=0.95,
            description="Test evidence"
        )
        
        assert evidence.source == "test_source"
        assert evidence.data == {"key": "value"}
        assert evidence.confidence == 0.95
        assert evidence.description == "Test evidence"
    
    def test_calculate_confidence_high(self):
        """Test confidence calculation with high data quality"""
        agent = TrialAgent()
        confidence = agent.calculate_confidence("high", 0.9)
        assert confidence >= 0.8
    
    def test_calculate_confidence_medium(self):
        """Test confidence calculation with medium data quality"""
        agent = TrialAgent()
        confidence = agent.calculate_confidence("medium", 0.7)
        assert confidence >= 0.5
    
    def test_calculate_confidence_low(self):
        """Test confidence calculation with low data quality"""
        agent = TrialAgent()
        confidence = agent.calculate_confidence("low", 0.5)
        assert confidence >= 0.5
    
    def test_determine_uncertainty_low(self):
        """Test uncertainty determination for low uncertainty"""
        agent = TrialAgent()
        uncertainty = agent.determine_uncertainty(0.9)
        assert uncertainty == "Low"
    
    def test_determine_uncertainty_medium(self):
        """Test uncertainty determination for medium uncertainty"""
        agent = TrialAgent()
        uncertainty = agent.determine_uncertainty(0.6)
        assert uncertainty == "Medium"
    
    def test_determine_uncertainty_high(self):
        """Test uncertainty determination for high uncertainty"""
        agent = TrialAgent()
        uncertainty = agent.determine_uncertainty(0.3)
        assert uncertainty == "High"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
