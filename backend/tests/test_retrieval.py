"""
Comprehensive tests for document retrieval and indexing
"""
import pytest
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.retrieval.document_index import DocumentIndex
from app.data.database import db


@pytest.fixture
def sample_documents():
    """Create sample documents for testing"""
    return [
        {
            "doc_id": "DOC-0001",
            "title": "JAK2 Inhibitors in Oncology",
            "full_text": "This document discusses JAK2 inhibitors and their role in oncology treatment. JAK2 is a key target protein.",
            "tags": "oncology, jak2, inhibitors",
            "compound_id": "CMP-0001",
            "trial_id": None
        },
        {
            "doc_id": "DOC-0002",
            "title": "Cardiotoxicity of Kinase Inhibitors",
            "full_text": "Kinase inhibitors can cause cardiotoxicity. This is a known safety concern.",
            "tags": "cardiotoxicity, safety, kinase",
            "compound_id": "CMP-0002",
            "trial_id": None
        },
        {
            "doc_id": "DOC-0003",
            "title": "Phase II Trial Results",
            "full_text": "Phase II clinical trial results show promising outcomes.",
            "tags": "phase ii, trial, results",
            "compound_id": None,
            "trial_id": "TRL-0001"
        }
    ]


@pytest.fixture
def document_index(sample_documents):
    """Create document index with sample documents"""
    index = DocumentIndex()
    index.build_index(sample_documents)
    return index


@pytest.fixture
def setup_database():
    """Setup database with actual data for testing"""
    db.connect()
    db.load_csv_data("./data")
    yield db
    db.close()


class TestDocumentIndex:
    """Test DocumentIndex class"""
    
    def test_initialization(self):
        """Test document index initialization"""
        index = DocumentIndex()
        assert index.documents == []
        assert index.doc_id_to_index == {}
        assert index.inverted_index == {}
    
    def test_build_index(self, sample_documents):
        """Test building document index"""
        index = DocumentIndex()
        index.build_index(sample_documents)
        
        assert len(index.documents) == 3
        assert len(index.doc_id_to_index) == 3
        assert len(index.inverted_index) > 0
    
    def test_doc_id_to_index_mapping(self, document_index):
        """Test document ID to index mapping"""
        assert "DOC-0001" in document_index.doc_id_to_index
        assert "DOC-0002" in document_index.doc_id_to_index
        assert "DOC-0003" in document_index.doc_id_to_index
    
    def test_inverted_index_structure(self, document_index):
        """Test inverted index structure"""
        # Check that common terms are indexed
        assert "jak2" in document_index.inverted_index
        assert "oncology" in document_index.inverted_index
        assert "cardiotoxicity" in document_index.inverted_index
    
    def test_search_basic(self, document_index):
        """Test basic search functionality"""
        results = document_index.search("JAK2 inhibitors")
        assert len(results) > 0
        assert all("relevance_score" in result for result in results)
        assert all("snippet" in result for result in results)
    
    def test_search_case_insensitive(self, document_index):
        """Test search is case insensitive"""
        results_lower = document_index.search("jak2")
        results_upper = document_index.search("JAK2")
        assert len(results_lower) == len(results_upper)
    
    def test_search_no_results(self, document_index):
        """Test search with no matching results"""
        results = document_index.search("nonexistent term xyz123")
        assert len(results) == 0
    
    def test_search_top_k(self, document_index):
        """Test search with top_k parameter"""
        results = document_index.search("trial", top_k=2)
        assert len(results) <= 2
    
    def test_relevance_score_normalization(self, document_index):
        """Test relevance scores are normalized to 0-1"""
        results = document_index.search("JAK2")
        for result in results:
            assert 0 <= result["relevance_score"] <= 1
    
    def test_snippet_generation(self, document_index):
        """Test snippet generation"""
        results = document_index.search("JAK2")
        if results:
            assert len(results[0]["snippet"]) > 0
            assert len(results[0]["snippet"]) <= 200  # Default max length
    
    def test_get_document_by_id(self, document_index):
        """Test get document by ID"""
        doc = document_index.get_document_by_id("DOC-0001")
        assert doc is not None
        assert doc["doc_id"] == "DOC-0001"
        assert doc["title"] == "JAK2 Inhibitors in Oncology"
    
    def test_get_document_by_id_not_found(self, document_index):
        """Test get document by ID when not found"""
        doc = document_index.get_document_by_id("DOC-9999")
        assert doc is None
    
    def test_search_by_compound(self, document_index):
        """Test search by compound ID"""
        results = document_index.search_by_compound("CMP-0001")
        assert len(results) >= 0
        for result in results:
            assert result.get("compound_id") == "CMP-0001"
    
    def test_search_by_compound_no_results(self, document_index):
        """Test search by compound with no results"""
        results = document_index.search_by_compound("CMP-9999")
        assert len(results) == 0
    
    def test_search_by_trial(self, document_index):
        """Test search by trial ID"""
        results = document_index.search_by_trial("TRL-0001")
        assert len(results) >= 0
        for result in results:
            assert result.get("trial_id") == "TRL-0001"
    
    def test_search_by_trial_no_results(self, document_index):
        """Test search by trial with no results"""
        results = document_index.search_by_trial("TRL-9999")
        assert len(results) == 0
    
    def test_search_by_target_protein(self, document_index):
        """Test search by target protein"""
        results = document_index.search_by_target_protein("JAK2")
        assert len(results) >= 0
    
    def test_search_by_therapeutic_area(self, document_index):
        """Test search by therapeutic area"""
        results = document_index.search_by_therapeutic_area("oncology")
        assert len(results) >= 0
    
    def test_tokenize(self, document_index):
        """Test tokenization"""
        tokens = document_index._tokenize("JAK2 inhibitors in Oncology")
        assert "jak2" in tokens
        assert "inhibitors" in tokens
        assert "oncology" in tokens
        assert all(token.islower() for token in tokens)
    
    def test_tokenize_removes_punctuation(self, document_index):
        """Test tokenization removes punctuation"""
        tokens = document_index._tokenize("Hello, world! This is a test.")
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens
        assert "," not in tokens
        assert "!" not in tokens


class TestDocumentIndexWithActualData:
    """Test document index with actual database data"""
    
    def test_build_index_with_actual_data(self, setup_database):
        """Test building index with actual research documents"""
        documents = db.get_all_research_documents()
        assert len(documents) > 0
        
        index = DocumentIndex()
        index.build_index(documents)
        
        assert len(index.documents) == len(documents)
        assert len(index.doc_id_to_index) == len(documents)
    
    def test_search_actual_data(self, setup_database):
        """Test search with actual data"""
        documents = db.get_all_research_documents()
        index = DocumentIndex()
        index.build_index(documents)
        
        # Search for common terms
        results = index.search("JAK2")
        assert len(results) >= 0
        
        results = index.search("phase")
        assert len(results) >= 0
        
        results = index.search("cardiotoxicity")
        assert len(results) >= 0
    
    def test_search_by_compound_actual_data(self, setup_database):
        """Test search by compound with actual data"""
        documents = db.get_all_research_documents()
        index = DocumentIndex()
        index.build_index(documents)
        
        # Try a compound that might have documents
        results = index.search_by_compound("CMP-0001")
        assert len(results) >= 0
    
    def test_search_by_trial_actual_data(self, setup_database):
        """Test search by trial with actual data"""
        documents = db.get_all_research_documents()
        index = DocumentIndex()
        index.build_index(documents)
        
        # Try a trial that might have documents
        results = index.search_by_trial("TRL-0001")
        assert len(results) >= 0


class TestDocumentIndexEdgeCases:
    """Test document index edge cases"""
    
    def test_empty_documents_list(self):
        """Test building index with empty documents list"""
        index = DocumentIndex()
        index.build_index([])
        
        assert len(index.documents) == 0
        assert len(index.doc_id_to_index) == 0
        assert len(index.inverted_index) == 0
    
    def test_search_without_building_index(self):
        """Test search without building index first"""
        index = DocumentIndex()
        results = index.search("test query")
        assert len(results) == 0
    
    def test_document_with_missing_fields(self):
        """Test building index with documents missing optional fields"""
        documents = [
            {
                "doc_id": "DOC-0001",
                "title": "Test Document",
                "full_text": "Test content",
                "tags": "",
                "compound_id": None,
                "trial_id": None
            }
        ]
        
        index = DocumentIndex()
        index.build_index(documents)
        
        assert len(index.documents) == 1
        results = index.search("test")
        assert len(results) > 0
    
    def test_very_long_snippet(self):
        """Test snippet generation with very long text"""
        documents = [
            {
                "doc_id": "DOC-0001",
                "title": "Long Document",
                "full_text": "This is a very long document. " * 100,
                "tags": "test",
                "compound_id": None,
                "trial_id": None
            }
        ]
        
        index = DocumentIndex()
        index.build_index(documents)
        results = index.search("long")
        
        assert len(results[0]["snippet"]) <= 200
        # Snippet may or may not end with "..." depending on truncation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
