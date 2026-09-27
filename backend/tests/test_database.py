import pytest
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.data.database import Database


@pytest.fixture
def test_db():
    """Create a test database instance with actual data"""
    db = Database(":memory:")
    db.connect()
    db.load_csv_data("./data")
    return db


@pytest.fixture
def temp_data_dir():
    """Create temporary directory with test data"""
    temp_dir = tempfile.mkdtemp()
    # Copy actual data files to temp directory
    source_data_dir = Path(__file__).parent.parent.parent / "backend" / "data"
    if source_data_dir.exists():
        for csv_file in source_data_dir.glob("*.csv"):
            shutil.copy(csv_file, temp_dir)
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_database_connection(test_db):
    """Test database connection"""
    assert test_db.conn is not None
    assert test_db.db_path == ":memory:"


def test_compound_retrieval(test_db):
    """Test compound retrieval"""
    compound = test_db.get_compound("CMP-0001")
    assert compound is not None
    assert compound["compound_id"] == "CMP-0001"
    assert "compound_name" in compound
    assert "target_protein" in compound


def test_compound_not_found(test_db):
    """Test compound not found"""
    compound = test_db.get_compound("CMP-9999")
    assert compound is None


def test_compounds_by_target(test_db):
    """Test get compounds by target protein"""
    compounds = test_db.get_compounds_by_target("JAK2")
    assert len(compounds) > 0
    for compound in compounds:
        assert compound["target_protein"] == "JAK2"


def test_trial_retrieval(test_db):
    """Test trial retrieval"""
    trial = test_db.get_trial("TRL-0001")
    assert trial is not None
    assert trial["trial_id"] == "TRL-0001"
    assert "compound_id" in trial
    assert "trial_phase" in trial


def test_trial_not_found(test_db):
    """Test trial not found"""
    trial = test_db.get_trial("TRL-9999")
    assert trial is None


def test_trials_by_phase_and_area(test_db):
    """Test get trials by phase and therapeutic area"""
    trials = test_db.get_trials_by_phase_and_area("Phase II", "Oncology")
    assert len(trials) >= 0
    for trial in trials:
        assert trial["trial_phase"] == "Phase II"
        assert trial["therapeutic_area"] == "Oncology"


def test_trials_below_enrollment_threshold(test_db):
    """Test get trials below enrollment threshold"""
    trials = test_db.get_trials_below_enrollment_threshold(60.0)
    assert len(trials) >= 0
    for trial in trials:
        assert trial["enrollment_pct"] < 60.0


def test_adverse_event_retrieval(test_db):
    """Test adverse event retrieval"""
    events = test_db.get_adverse_events_by_trial("TRL-0001")
    assert len(events) >= 0
    for event in events:
        assert event["trial_id"] == "TRL-0001"


def test_serious_adverse_events(test_db):
    """Test get serious adverse events"""
    events = test_db.get_serious_adverse_events()
    assert len(events) >= 0
    for event in events:
        assert event["seriousness"] == "Serious"


def test_serious_adverse_events_by_trial(test_db):
    """Test get serious adverse events by trial"""
    events = test_db.get_serious_adverse_events("TRL-0001")
    assert len(events) >= 0
    for event in events:
        assert event["trial_id"] == "TRL-0001"
        assert event["seriousness"] == "Serious"


def test_lab_results_by_compound(test_db):
    """Test get lab results by compound"""
    results = test_db.get_lab_results_by_compound("CMP-0001")
    assert len(results) >= 0
    for result in results:
        assert result["compound_id"] == "CMP-0001"


def test_trial_sites(test_db):
    """Test get trial sites"""
    sites = test_db.get_trial_sites("TRL-0001")
    assert len(sites) >= 0
    for site in sites:
        assert site["trial_id"] == "TRL-0001"


def test_all_research_documents(test_db):
    """Test get all research documents"""
    documents = test_db.get_all_research_documents()
    assert len(documents) > 0
    for doc in documents:
        assert "doc_id" in doc
        assert "title" in doc
        assert "full_text" in doc


def test_documents_by_compound(test_db):
    """Test get documents by compound"""
    documents = test_db.get_documents_by_compound("CMP-0001")
    assert len(documents) >= 0
    for doc in documents:
        assert doc["compound_id"] == "CMP-0001"


def test_documents_by_trial(test_db):
    """Test get documents by trial"""
    documents = test_db.get_documents_by_trial("TRL-0001")
    assert len(documents) >= 0
    for doc in documents:
        assert doc["trial_id"] == "TRL-0001"


def test_search_adverse_events_by_term(test_db):
    """Test search adverse events by term"""
    events = test_db.search_adverse_events_by_term("headache")
    assert len(events) >= 0
    for event in events:
        assert "headache" in event["adverse_event_term"].lower()


def test_safety_summary_by_trial(test_db):
    """Test safety summary calculation"""
    summary = test_db.get_safety_summary_by_trial("TRL-0001")
    assert "total_events" in summary
    assert "serious_events" in summary
    assert "severe_events" in summary
    assert "related_events" in summary
    assert "most_common_events" in summary
    assert "risk_level" in summary
    assert summary["risk_level"] in ["Low", "Medium", "High"]


def test_execute_query(test_db):
    """Test execute query method"""
    results = test_db.execute_query("SELECT * FROM compounds LIMIT 5")
    assert len(results) == 5
    assert "compound_id" in results[0]


def test_execute_query_with_params(test_db):
    """Test execute query with parameters"""
    results = test_db.execute_query(
        "SELECT * FROM compounds WHERE compound_id = ?",
        ("CMP-0001",)
    )
    assert len(results) == 1
    assert results[0]["compound_id"] == "CMP-0001"


def test_database_close(test_db):
    """Test database close"""
    test_db.close()
    assert test_db.conn is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
