"""
Demo Workflow Tests
Tests the four required demo workflows against actual data
"""
import sys
import os
import time

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.data.database import db
from app.retrieval.document_index import document_index
from app.agents.trial_agent import TrialAgent
from app.agents.compound_agent import CompoundAgent
from app.agents.safety_agent import SafetyAgent
from app.agents.research_agent import ResearchAgent
from app.agents.synthesis_agent import SynthesisAgent


def setup():
    """Setup database and document index"""
    print("Setting up database and document index...")
    db.connect()
    db.load_csv_data("./data")
    
    documents = db.get_all_research_documents()
    document_index.build_index(documents)
    print("Setup complete.")


def teardown():
    """Cleanup database connection"""
    db.close()


def test_workflow_1():
    """Test: Which Phase II oncology trials are below 60% enrollment right now?"""
    print("\n" + "="*70)
    print("WORKFLOW 1: Phase II Oncology Trials Below 60% Enrollment")
    print("="*70)
    
    query = "Which Phase II oncology trials are below 60% enrollment right now?"
    print(f"Query: {query}")
    
    agent = TrialAgent()
    start_time = time.time()
    response = agent.process_query(query)
    processing_time = (time.time() - start_time) * 1000
    
    print(f"\nAgent: {response.agent_used}")
    print(f"Processing Time: {processing_time:.0f}ms")
    print(f"\nAnswer:\n{response.answer}")
    print(f"\nUncertainty: {response.uncertainty}")
    print(f"Sources: {response.sources[:5]}")
    
    # Verify response
    assert response.agent_used == "Trial Intelligence Agent"
    assert "Phase II" in response.answer
    assert "oncology" in response.answer.lower()
    assert len(response.evidence) > 0
    assert response.uncertainty in ["Low", "Medium", "High"]
    
    print("\nWorkflow 1 PASSED")
    return True


def test_workflow_2():
    """Test: What has our internal research said about JAK2 inhibitors and cardiotoxicity?"""
    print("\n" + "="*70)
    print("WORKFLOW 2: JAK2 Inhibitors and Cardiotoxicity Research")
    print("="*70)
    
    query = "What has our internal research said about JAK2 inhibitors and cardiotoxicity?"
    print(f"Query: {query}")
    
    agent = ResearchAgent()
    start_time = time.time()
    response = agent.process_query(query)
    processing_time = (time.time() - start_time) * 1000
    
    print(f"\nAgent: {response.agent_used}")
    print(f"Processing Time: {processing_time:.0f}ms")
    print(f"\nAnswer:\n{response.answer}")
    print(f"\nUncertainty: {response.uncertainty}")
    print(f"Sources: {response.sources[:5]}")
    
    # Verify response
    assert response.agent_used == "Research Document Agent"
    assert len(response.evidence) > 0
    assert response.uncertainty in ["Low", "Medium", "High"]
    
    print("\nWorkflow 2 PASSED")
    return True


def test_workflow_3():
    """Test: A site just reported a serious adverse event for Trial TRL-0032 — triage it."""
    print("\n" + "="*70)
    print("WORKFLOW 3: Safety Triage for Trial TRL-0032")
    print("="*70)
    
    query = "A site just reported a serious adverse event for Trial TRL-0032 — triage it."
    print(f"Query: {query}")
    
    agent = SafetyAgent()
    start_time = time.time()
    response = agent.process_query(query)
    processing_time = (time.time() - start_time) * 1000
    
    print(f"\nAgent: {response.agent_used}")
    print(f"Processing Time: {processing_time:.0f}ms")
    print(f"\nAnswer:\n{response.answer}")
    print(f"\nUncertainty: {response.uncertainty}")
    print(f"Sources: {response.sources[:5]}")
    
    # Verify response
    assert response.agent_used == "Safety Intelligence Agent"
    assert "TRL-0032" in response.answer or "trial" in response.answer.lower()
    assert len(response.evidence) > 0
    assert response.uncertainty in ["Low", "Medium", "High"]
    
    print("\nWorkflow 3 PASSED")
    return True


def test_workflow_4():
    """Test: Give me the full picture on compound DKU-1001: labs, trials, safety, and related literature."""
    print("\n" + "="*70)
    print("WORKFLOW 4: Full Compound Profile for DKU-1001")
    print("="*70)
    
    query = "Give me the full picture on compound DKU-1001: labs, trials, safety, and related literature."
    print(f"Query: {query}")
    
    agent = SynthesisAgent()
    start_time = time.time()
    response = agent.process_query(query)
    processing_time = (time.time() - start_time) * 1000
    
    print(f"\nAgent: {response.agent_used}")
    print(f"Processing Time: {processing_time:.0f}ms")
    print(f"\nAnswer:\n{response.answer[:500]}...")
    print(f"\nUncertainty: {response.uncertainty}")
    print(f"Sources: {response.sources[:5]}")
    
    # Verify response
    assert response.agent_used == "Synthesis Agent"
    assert len(response.evidence) > 0
    assert response.uncertainty in ["Low", "Medium", "High"]
    
    print("\nWorkflow 4 PASSED")
    return True


def run_all_workflows():
    """Run all demo workflows"""
    print("\n" + "="*70)
    print("PHARMASENSE DEMO WORKFLOW TESTS")
    print("="*70)
    
    try:
        setup()
        
        results = []
        results.append(("Workflow 1", test_workflow_1()))
        results.append(("Workflow 2", test_workflow_2()))
        results.append(("Workflow 3", test_workflow_3()))
        results.append(("Workflow 4", test_workflow_4()))
        
        teardown()
        
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        for name, passed in results:
            status = "PASSED" if passed else "FAILED"
            print(f"{name}: {status}")
        
        all_passed = all(result[1] for result in results)
        
        if all_passed:
            print("\nALL WORKFLOWS PASSED")
            return 0
        else:
            print("\nSOME WORKFLOWS FAILED")
            return 1
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        teardown()
        return 1


if __name__ == "__main__":
    exit_code = run_all_workflows()
    sys.exit(exit_code)
