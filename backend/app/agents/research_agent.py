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
                answer=f"I searched for research on {compound_id} but couldn't find this compound in our research records. Please verify the compound identifier or let me know if you'd like me to search for a different compound.",
                evidence=[],
                sources=[],
                interpretation="No verified evidence was found for this compound. You may want to verify the compound identifier or ask about available compounds."
            )
        
        # Get research documents
        documents = db.get_documents_by_compound(compound_id)
        
        if not documents:
            return QueryResponse(
                answer=f"While I found the compound record for {compound_id} ({compound['compound_name']}), I couldn't locate any research documents in our current database. This might indicate that research documentation hasn't been fully integrated yet. Would you like me to check for clinical trials or laboratory results for this compound instead?",
                evidence=[],
                sources=[compound_id],
                interpretation=f"While the compound record exists, no research documentation is available in the current evidence base. You may want to ask about clinical trials or laboratory results for this compound instead."
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
        
        # Build conversational answer
        answer_parts = [
            f"**Research Literature for {compound_id}**",
            f"I found {len(documents)} research document(s) related to {compound['compound_name']} in our database.",
            f""
        ]
        
        # Add document type summary
        doc_types = self._summarize_document_types(documents)
        if doc_types:
            answer_parts.append(f"**Document Types Available:**")
            for doc_type, count in doc_types.items():
                answer_parts.append(f"- {doc_type}: {count} document(s)")
            answer_parts.append(f"")
        
        # Add specific document evidence
        answer_parts.append(f"**Key Research Documents:**")
        for doc in documents[:3]:
            answer_parts.append(f"- **{doc['title']}** (Document: {doc['doc_id']})")
            answer_parts.append(f"  - Type: {doc['doc_type']}")
            answer_parts.append(f"  - Author: {doc['author']}")
            answer_parts.append(f"  - Date: {doc['date']}")
            answer_parts.append(f"")
            
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
        
        # Add key insights from documents
        if documents:
            key_insights = self._extract_key_insights(documents)
            if key_insights:
                answer_parts.append(f"**Key Takeaways from Research:**")
                for insight in key_insights[:3]:
                    answer_parts.append(f"- {insight}")
        
        answer = "\n".join(answer_parts)
        
        sources = [compound_id] + [doc["doc_id"] for doc in documents]
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=sources,
            interpretation=f"Research documentation includes {len(documents)} document(s) covering various aspects of {compound_id}."
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
                    answer="No relevant research documents were found for your query.",
                    evidence=[],
                    sources=[],
                    interpretation="No matching documents were found in the available research corpus. You may want to try different search terms or ask about specific compounds or trials."
                )
            
            return self._format_search_results(search_results, query)
        
        # Search for documents mentioning this target
        search_results = document_index.search_by_target_protein(target_protein)
        
        if not search_results:
            return QueryResponse(
                answer=f"No research documents were found mentioning {target_protein}.",
                evidence=[],
                sources=[],
                interpretation=f"No research documentation for {target_protein} was found in the available evidence. You may want to ask about compounds targeting this protein or try a different target."
            )
        
        return self._format_search_results(search_results, query)
    
    def _handle_therapeutic_research_query(self, therapeutic_area: str) -> QueryResponse:
        """Handle research queries for therapeutic areas"""
        search_results = document_index.search_by_therapeutic_area(therapeutic_area.title())
        
        if not search_results:
            return QueryResponse(
                answer=f"No research documents were found for {therapeutic_area}.",
                evidence=[],
                sources=[],
                interpretation=f"No research documentation for {therapeutic_area} was found in the available evidence. You may want to try a different therapeutic area or ask about specific compounds in this area."
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
                answer="No research documents were found regarding cardiotoxicity or toxicity in the available research corpus.",
                evidence=[],
                sources=[],
                interpretation="No toxicity-related research was found. You may want to try different search terms or ask about specific compounds where toxicity data might be available."
            )
        
        # Add specific cardiotoxicity analysis
        cardiotoxicity_docs = [
            doc for doc in search_results
            if "cardiotoxicity" in doc.get("full_text", "").lower() or 
               "toxicity" in doc.get("full_text", "").lower()
        ]
        
        answer_parts = [
            f"**Research Findings**",
            f"",
            f"I searched our research database for information about {target_protein if target_protein else 'cardiotoxicity and toxicity'} and found {len(search_results)} relevant document(s).",
            f""
        ]
        
        if cardiotoxicity_docs:
            answer_parts.append(f"I found {len(cardiotoxicity_docs)} research document(s) discussing cardiotoxicity/toxicity.")
            if target_protein:
                answer_parts.append(f"Specifically related to {target_protein} inhibitors.")
        else:
            answer_parts.append(f"I found {len(search_results)} research document(s) that may be relevant to your toxicity query.")
        
        answer_parts.append(f"\n**Relevant Documents:**")
        for doc in search_results[:3]:
            answer_parts.append(f"- {doc['doc_id']}: {doc['title']}")
            if doc.get("snippet"):
                answer_parts.append(f"  {doc['snippet'][:100]}...")
        
        answer = "\n".join(answer_parts)
        
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
            interpretation=f"Research documents provide toxicity insights with {len(cardiotoxicity_docs)} document(s) specifically discussing cardiotoxicity."
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
                answer="No literature review documents were found in the available research records.",
                evidence=[],
                sources=[],
                interpretation="No literature reviews are available in the current evidence base. You may want to ask about other document types or specific research topics."
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
        
        answer_parts = [
            f"**Literature Reviews**",
            f"I found {len(literature_reviews)} literature review document(s) in the available research records.",
            f"\n**Available Literature Reviews:**"
        ]
        
        for doc in literature_reviews[:5]:
            answer_parts.append(f"- {doc['doc_id']}: {doc['title']} by {doc['author']}")
            if doc["tags"]:
                answer_parts.append(f"  Tags: {doc['tags']}")
        
        answer = "\n".join(answer_parts)
        
        sources = [doc["doc_id"] for doc in literature_reviews]
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=sources,
            interpretation=f"Literature reviews are available covering various topics across {len(literature_reviews)} document(s)."
        )
    
    def _handle_document_search_query(self, query: str) -> QueryResponse:
        """Handle general document search queries"""
        search_results = document_index.search(query, top_k=5)
        
        if not search_results:
            return QueryResponse(
                answer="No research documents were found matching your query in the available research corpus.",
                evidence=[],
                sources=[],
                interpretation="No matching documents were found. You may want to try different search terms or ask about specific compounds, trials, or therapeutic areas."
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
        
        answer = f"**Research Findings**\n\nI searched our research database and found {len(search_results)} document(s) matching your query.\n\n"
        answer += "**Most Relevant Documents:**\n"
        
        for i, doc in enumerate(search_results[:3], 1):
            answer += f"{i}. **{doc['title']}** ({doc['doc_type']})\n"
            if doc.get('snippet'):
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
