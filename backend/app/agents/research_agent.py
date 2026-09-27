from typing import Dict, List, Optional
import logging
from app.agents.base_agent import BaseAgent
from app.data.database import db
from app.retrieval.document_index import document_index
from app.data.models import QueryResponse, Evidence

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """Specialist agent for research document intelligence"""
    
    def __init__(self):
        super().__init__("Research Document Agent")
        
    def process_query(self, query: str, context: Optional[Dict] = None) -> QueryResponse:
        """Process research document queries"""
        query_lower = query.lower()
        
        # Check for compound-specific research query
        import re
        compound_id_match = re.search(r'CMP-\d+', query, re.IGNORECASE)
        compound_name_match = re.search(r'[A-Z]{2,4}-\d{4}', query, re.IGNORECASE)
        
        if compound_id_match or compound_name_match:
            compound_id = (compound_id_match or compound_name_match).group(0).upper()
            return self._handle_compound_research_query(compound_id)
        
        # Check for target protein research query
        if "inhibitor" in query_lower or "target" in query_lower:
            return self._handle_target_research_query(query)
        
        # Check for therapeutic area research query
        areas = ["oncology", "cardiology", "neurology", "metabolic disease", 
                "respiratory", "immunology", "infectious disease"]
        for area in areas:
            if area in query_lower:
                return self._handle_therapeutic_research_query(area)
        
        # Check for specific research topics
        if "cardiotoxicity" in query_lower or "toxicity" in query_lower:
            return self._handle_toxicity_research_query(query)
        
        if "literature" in query_lower or "review" in query_lower:
            return self._handle_literature_review_query(query)
        
        # Default: general document search
        return self._handle_document_search_query(query)
    
    def _handle_compound_research_query(self, compound_id: str) -> QueryResponse:
        """Handle research queries for a specific compound"""
        compound = db.get_compound(compound_id)
        
        if not compound:
            return QueryResponse(
                answer=f"I couldn't find {compound_id} in the available research records.",
                evidence=[],
                sources=[],
                interpretation="No verified evidence was found for this compound."
            )
        
        # Get research documents
        documents = db.get_documents_by_compound(compound_id)
        
        if not documents:
            return QueryResponse(
                answer=f"No research documents found for compound {compound_id}.",
                evidence=[],
                sources=[compound_id],
                interpretation=f"No research documentation available for {compound_id}"
            )
        
        # Build evidence
        evidence = [
            self.create_evidence(
                source="research_documents",
                data={
                    "document_count": len(documents),
                    "document_types": self._summarize_document_types(documents)
                },
                confidence=0.90,
                description=f"Research documents for compound {compound_id}"
            )
        ]
        
        # Add specific document evidence
        for doc in documents[:3]:
            evidence.append(
                self.create_evidence(
                    source="research_documents",
                    data={
                        "doc_id": doc["doc_id"],
                        "title": doc["title"],
                        "doc_type": doc["doc_type"],
                        "author": doc["author"],
                        "date": doc["date"],
                        "snippet": doc["full_text"][:200] + "..."
                    },
                    confidence=0.85,
                    description=f"Document: {doc['title']}"
                )
            )
        
        # Build answer
        answer_parts = [
            f"**Research Findings**",
            f"**Relevant Evidence:** Found {len(documents)} research documents for compound {compound_id} ({compound['compound_name']}).",
            f"Target protein: {compound['target_protein']}, Therapeutic area: {compound['therapeutic_area']}."
        ]
        
        # Add document type summary
        doc_types = self._summarize_document_types(documents)
        if doc_types:
            answer_parts.append(f"Document types: {', '.join(f'{k}: {v}' for k, v in doc_types.items())}.")
        
        # Add key insights from documents
        if documents:
            key_insights = self._extract_key_insights(documents)
            if key_insights:
                answer_parts.append("\n**Key Takeaways:**")
                for insight in key_insights[:3]:
                    answer_parts.append(f"- {insight}")
        
        answer = "\n".join(answer_parts)
        
        sources = [compound_id] + [doc["doc_id"] for doc in documents]
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=sources,
            interpretation="Research documentation provides comprehensive compound analysis"
        )
    
    def _handle_target_research_query(self, query: str) -> QueryResponse:
        """Handle research queries for target proteins"""
        query_lower = query.lower()
        
        # Extract target protein
        targets = ["JAK2", "TNF-alpha", "BTK", "BCL-2", "VEGFR2", "PCSK9", "ALK", 
                  "IL-6R", "HER2", "CDK4/6", "SGLT2", "EGFR", "NLRP3", "PD-1", 
                  "GLP-1R", "KRAS G12C", "mTOR", "BRAF"]
        
        target_protein = None
        for target in targets:
            if target.lower() in query_lower:
                target_protein = target
                break
        
        if not target_protein:
            # Use document search instead
            search_results = document_index.search(query, top_k=5)
            
            if not search_results:
                return QueryResponse(
                    answer="No relevant research documents found for your query.",
                    evidence=[],
                    sources=[],
                    interpretation="No matching documents found"
                )
            
            return self._format_search_results(search_results, query)
        
        # Search for documents mentioning this target
        search_results = document_index.search_by_target_protein(target_protein)
        
        if not search_results:
            return QueryResponse(
                answer=f"No research documents found mentioning {target_protein}.",
                evidence=[],
                sources=[],
                interpretation=f"No research documentation for {target_protein}"
            )
        
        return self._format_search_results(search_results, query)
    
    def _handle_therapeutic_research_query(self, therapeutic_area: str) -> QueryResponse:
        """Handle research queries for therapeutic areas"""
        search_results = document_index.search_by_therapeutic_area(therapeutic_area.title())
        
        if not search_results:
            return QueryResponse(
                answer=f"No research documents found for {therapeutic_area}.",
                evidence=[],
                sources=[],
                interpretation=f"No research documentation for {therapeutic_area}"
            )
        
        return self._format_search_results(search_results, f"{therapeutic_area} research")
    
    def _handle_toxicity_research_query(self, query: str) -> QueryResponse:
        """Handle toxicity/cardiotoxicity research queries"""
        query_lower = query.lower()
        
        # Extract target if mentioned
        targets = ["JAK2", "TNF-alpha", "BTK", "BCL-2", "VEGFR2", "PCSK9", "ALK", 
                  "IL-6R", "HER2", "CDK4/6", "SGLT2", "EGFR", "NLRP3", "PD-1", 
                  "GLP-1R", "KRAS G12C", "mTOR", "BRAF"]
        
        target_protein = None
        for target in targets:
            if target.lower() in query_lower:
                target_protein = target
                break
        
        # Build search query
        search_query = "cardiotoxicity toxicity safety"
        if target_protein:
            search_query += f" {target_protein}"
        
        search_results = document_index.search(search_query, top_k=5)
        
        if not search_results:
            return QueryResponse(
                answer="No research documents found regarding cardiotoxicity or toxicity.",
                evidence=[],
                sources=[],
                interpretation="No toxicity-related research found"
            )
        
        # Add specific cardiotoxicity analysis
        cardiotoxicity_docs = [
            doc for doc in search_results
            if "cardiotoxicity" in doc.get("full_text", "").lower() or 
               "toxicity" in doc.get("full_text", "").lower()
        ]
        
        if cardiotoxicity_docs:
            answer = f"**Research Findings**\n\nI found {len(cardiotoxicity_docs)} research documents discussing cardiotoxicity/toxicity. "
            if target_protein:
                answer += f"Specifically related to {target_protein} inhibitors."
        else:
            answer = f"**Research Findings**\n\nI found {len(search_results)} research documents that may be relevant to your toxicity query."
        
        evidence = [
            self.create_evidence(
                source="research_documents",
                data={
                    "total_results": len(search_results),
                    "cardiotoxicity_specific": len(cardiotoxicity_docs),
                    "documents": [
                        {
                            "doc_id": doc["doc_id"],
                            "title": doc["title"],
                            "relevance_score": doc.get("relevance_score", 0),
                            "snippet": doc.get("snippet", "")
                        }
                        for doc in search_results[:3]
                    ]
                },
                confidence=0.85,
                description="Toxicity-related research documents"
            )
        ]
        
        sources = [doc["doc_id"] for doc in search_results]
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=sources,
            interpretation="Research documents provide toxicity insights"
        )
    
    def _handle_literature_review_query(self, query: str) -> QueryResponse:
        """Handle literature review queries"""
        query_lower = query.lower()
        
        # Search for literature review documents
        all_docs = db.get_all_research_documents()
        literature_reviews = [
            doc for doc in all_docs
            if doc["doc_type"] == "Literature Review"
        ]
        
        if not literature_reviews:
            return QueryResponse(
                answer="No literature review documents found in the available research records.",
                evidence=[],
                sources=[],
                interpretation="No literature reviews available"
            )
        
        # Search within literature reviews
        search_results = document_index.search(query, top_k=5)
        literature_review_results = [
            doc for doc in search_results
            if doc["doc_type"] == "Literature Review"
        ]
        
        if literature_review_results:
            return self._format_search_results(literature_review_results, query)
        
        # Return all literature reviews if no specific match
        evidence = [
            self.create_evidence(
                source="research_documents",
                data={
                    "total_literature_reviews": len(literature_reviews),
                    "reviews": [
                        {
                            "doc_id": doc["doc_id"],
                            "title": doc["title"],
                            "author": doc["author"],
                            "date": doc["date"],
                            "tags": doc["tags"]
                        }
                        for doc in literature_reviews[:5]
                    ]
                },
                confidence=0.80,
                description="Available literature reviews"
            )
        ]
        
        answer = f"**Research Findings**\n\nI found {len(literature_reviews)} literature review documents. "
        answer += "Topics include: " + ", ".join([doc["tags"] for doc in literature_reviews[:5]])
        
        sources = [doc["doc_id"] for doc in literature_reviews]
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=sources,
            interpretation="Literature reviews available for various topics"
        )
    
    def _handle_document_search_query(self, query: str) -> QueryResponse:
        """Handle general document search queries"""
        search_results = document_index.search(query, top_k=5)
        
        if not search_results:
            return QueryResponse(
                answer="No research documents found matching your query.",
                evidence=[],
                sources=[],
                interpretation="No matching documents found"
            )
        
        return self._format_search_results(search_results, query)
    
    def _format_search_results(self, search_results: List[Dict], query: str) -> QueryResponse:
        """Format document search results into a response"""
        evidence = [
            self.create_evidence(
                source="research_documents",
                data={
                    "total_results": len(search_results),
                    "documents": [
                        {
                            "doc_id": doc["doc_id"],
                            "title": doc["title"],
                            "doc_type": doc["doc_type"],
                            "relevance_score": doc.get("relevance_score", 0),
                            "snippet": doc.get("snippet", "")
                        }
                        for doc in search_results[:3]
                    ]
                },
                confidence=0.85,
                description=f"Research documents matching query"
            )
        ]
        
        answer = f"**Research Findings**\n\nI found {len(search_results)} research documents matching your query.\n\n"
        answer += "Top results:\n"
        
        for i, doc in enumerate(search_results[:3], 1):
            answer += f"{i}. {doc['title']} ({doc['doc_type']}) - Relevance: {doc.get('relevance_score', 0):.2f}\n"
            answer += f"   {doc.get('snippet', '')}\n"
        
        sources = [doc["doc_id"] for doc in search_results]
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=sources,
            interpretation="Document retrieval provides relevant research materials"
        )
    
    def _summarize_document_types(self, documents: List[Dict]) -> Dict[str, int]:
        """Summarize document types"""
        doc_types = {}
        for doc in documents:
            doc_type = doc["doc_type"]
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        return doc_types
    
    def _extract_key_insights(self, documents: List[Dict]) -> List[str]:
        """Extract key insights from document full text"""
        insights = []
        
        for doc in documents:
            full_text = doc.get("full_text", "")
            
            # Look for key phrases indicating insights
            if "recommend" in full_text.lower():
                insights.append(f"Recommendation noted in {doc['title']}")
            if "significant" in full_text.lower():
                insights.append(f"Significant findings in {doc['title']}")
            if "support" in full_text.lower():
                insights.append(f"Supporting evidence in {doc['title']}")
            if "risk" in full_text.lower():
                insights.append(f"Risk assessment in {doc['title']}")
        
        return insights[:5]
