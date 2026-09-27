from typing import List, Dict, Optional
import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)


class DocumentIndex:
    """Keyword-based document retrieval index (dependency-light alternative to TF-IDF)"""
    
    def __init__(self):
        self.documents: List[Dict] = []
        self.doc_id_to_index: Dict[str, int] = {}
        self.inverted_index: Dict[str, List[int]] = {}
        
    def build_index(self, documents: List[Dict]):
        """Build keyword index from documents"""
        self.documents = documents
        self.doc_id_to_index = {doc["doc_id"]: i for i, doc in enumerate(documents)}
        
        # Build inverted index
        for i, doc in enumerate(documents):
            text = f"{doc.get('title', '')} {doc.get('full_text', '')} {doc.get('tags', '')}"
            tokens = self._tokenize(text)
            
            for token in set(tokens):  # Use set to avoid duplicates in same doc
                if token not in self.inverted_index:
                    self.inverted_index[token] = []
                self.inverted_index[token].append(i)
        
        logger.info(f"Built document index with {len(documents)} documents")
        
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        text = text.lower()
        # Remove punctuation and split
        tokens = re.findall(r'\b\w+\b', text)
        return tokens
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for documents matching the query using keyword matching"""
        if not self.inverted_index:
            logger.warning("Document index not built")
            return []
        
        query_tokens = self._tokenize(query)
        
        # Score documents based on keyword matches
        doc_scores = Counter()
        
        for token in query_tokens:
            if token in self.inverted_index:
                for doc_idx in self.inverted_index[token]:
                    doc_scores[doc_idx] += 1
        
        # Get top k results
        top_results = doc_scores.most_common(top_k)
        
        results = []
        max_score = max([score for _, score in top_results]) if top_results else 1
        
        for doc_idx, score in top_results:
            doc = self.documents[doc_idx].copy()
            # Normalize score to 0-1 range
            doc["relevance_score"] = score / max_score
            doc["snippet"] = self._generate_snippet(doc, query)
            results.append(doc)
        
        return results
    
    def _generate_snippet(self, document: Dict, query: str, max_length: int = 200) -> str:
        """Generate a snippet from the document containing query terms"""
        full_text = document.get("full_text", "")
        query_terms = query.lower().split()
        
        # Find best matching sentence
        sentences = full_text.split(". ")
        best_sentence = ""
        best_score = 0
        
        for sentence in sentences:
            score = sum(1 for term in query_terms if term in sentence.lower())
            if score > best_score:
                best_score = score
                best_sentence = sentence
        
        if not best_sentence:
            best_sentence = full_text[:max_length]
        
        # Truncate if too long
        if len(best_sentence) > max_length:
            best_sentence = best_sentence[:max_length] + "..."
        
        return best_sentence
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict]:
        """Get a document by its ID"""
        idx = self.doc_id_to_index.get(doc_id)
        if idx is not None:
            return self.documents[idx]
        return None
    
    def search_by_compound(self, compound_id: str) -> List[Dict]:
        """Get all documents for a specific compound"""
        return [doc for doc in self.documents if doc.get("compound_id") == compound_id]
    
    def search_by_trial(self, trial_id: str) -> List[Dict]:
        """Get all documents for a specific trial"""
        return [doc for doc in self.documents if doc.get("trial_id") == trial_id]
    
    def search_by_target_protein(self, target_protein: str) -> List[Dict]:
        """Search documents mentioning a target protein"""
        query = f"{target_protein} inhibitor"
        return self.search(query, top_k=10)
    
    def search_by_therapeutic_area(self, therapeutic_area: str) -> List[Dict]:
        """Search documents for a therapeutic area"""
        query = therapeutic_area
        return self.search(query, top_k=10)


# Global document index instance
document_index = DocumentIndex()
