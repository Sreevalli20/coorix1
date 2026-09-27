from typing import Dict, List, Optional
import logging
from app.agents.base_agent import BaseAgent
from app.data.database import db
from app.data.models import QueryResponse, Evidence

logger = logging.getLogger(__name__)


class CompoundAgent(BaseAgent):
    """Specialist agent for compound intelligence"""
    
    def __init__(self):
        super().__init__("Compound Intelligence Agent")
        
    def process_query(self, query: str, context: Optional[Dict] = None) -> QueryResponse:
        """Process compound-related queries"""
        query_lower = query.lower()
        
        # Check for specific compound query
        import re
        compound_id_match = re.search(r'CMP-\d+', query, re.IGNORECASE)
        compound_name_match = re.search(r'[A-Z]{2,4}-\d{4}', query, re.IGNORECASE)
        
        if compound_id_match or compound_name_match:
            compound_id = (compound_id_match or compound_name_match).group(0).upper()
            # Try compound_id first, if not found try compound_name
            compound = db.get_compound(compound_id)
            if not compound and compound_name_match:
                # Search by compound name
                compound_name = compound_name_match.group(0).upper()
                query_sql = "SELECT * FROM compounds WHERE compound_name = ?"
                results = db.execute_query(query_sql, (compound_name,))
                if results:
                    compound_id = results[0]["compound_id"]
            return self._handle_compound_specific_query(compound_id)
        
        # Check for target protein queries
        if "target" in query_lower or "protein" in query_lower:
            return self._handle_target_protein_query(query)
        
        # Check for therapeutic area queries
        if "therapeutic" in query_lower or "area" in query_lower:
            return self._handle_therapeutic_area_query(query)
        
        # Default: general compound information
        return self._handle_general_compound_query(query)
    
    def _handle_compound_specific_query(self, compound_id: str) -> QueryResponse:
        """Handle queries about a specific compound"""
        compound = db.get_compound(compound_id)
        
        if not compound:
            return QueryResponse(
                answer=f"I couldn't find {compound_id} in the available research records.",
                evidence=[],
                sources=[],
                interpretation="No verified evidence was found for this compound, so there isn't enough information to provide a clinical, laboratory, safety, or research summary.",
                uncertainty="High",
                agent_used=self.name,
                processing_time_ms=50.0
            )
        
        # Get related data
        trials = db.execute_query(
            "SELECT * FROM clinical_trials WHERE compound_id = ?",
            (compound_id,)
        )
        lab_results = db.get_lab_results_by_compound(compound_id)
        documents = db.get_documents_by_compound(compound_id)
        
        # Build comprehensive response
        evidence = [
            self.create_evidence(
                source="compounds",
                data=compound,
                confidence=1.0,
                description=f"Compound {compound_id} basic information"
            )
        ]
        
        if trials:
            evidence.append(
                self.create_evidence(
                    source="clinical_trials",
                    data={"trial_count": len(trials), "trials": trials},
                    confidence=0.95,
                    description=f"Associated clinical trials ({len(trials)})"
                )
            )
        
        if lab_results:
            pass_fail_counts = {"Pass": 0, "Fail": 0}
            for result in lab_results:
                pass_fail_counts[result["pass_fail"]] = pass_fail_counts.get(result["pass_fail"], 0) + 1
            
            evidence.append(
                self.create_evidence(
                    source="lab_results",
                    data={
                        "total_results": len(lab_results),
                        "pass_fail_counts": pass_fail_counts
                    },
                    confidence=0.90,
                    description=f"Laboratory results ({len(lab_results)} tests)"
                )
            )
        
        if documents:
            evidence.append(
                self.create_evidence(
                    source="research_documents",
                    data={"document_count": len(documents)},
                    confidence=0.85,
                    description=f"Research documents ({len(documents)})"
                )
            )
        
        # Build answer
        answer_parts = [
            f"**Compound Overview**",
            f"**Compound:** {compound_id} ({compound['compound_name']})",
            f"**Clinical Evidence:** {compound['chemical_class']} targeting {compound['target_protein']} for {compound['therapeutic_area']}. Current phase: {compound['discovery_phase']}. Mechanism: {compound['mechanism_of_action']}."
        ]
        
        if trials:
            active_trials = [t for t in trials if t["status"] in ["Recruiting", "Active, not recruiting"]]
            answer_parts.append(f"**Trial Evidence:** Associated with {len(trials)} clinical trials ({len(active_trials)} currently active).")
        
        if lab_results:
            pass_rate = pass_fail_counts.get("Pass", 0) / len(lab_results) * 100
            answer_parts.append(f"**Laboratory Evidence:** {len(lab_results)} tests completed with {pass_rate:.1f}% pass rate.")
        
        if documents:
            answer_parts.append(f"**Research Evidence:** {len(documents)} related documents available.")
        
        answer = "\n\n".join(answer_parts)
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=[compound_id] + [t["trial_id"] for t in trials[:5]] + [d["doc_id"] for d in documents[:3]],
            interpretation="Summary of available evidence for this compound.",
            uncertainty="Low",
            agent_used=self.name,
            processing_time_ms=200.0
        )
    
    def _handle_target_protein_query(self, query: str) -> QueryResponse:
        """Handle queries about target proteins"""
        query_lower = query.lower()
        
        # Try to extract target protein from query
        targets = ["JAK2", "TNF-alpha", "BTK", "BCL-2", "VEGFR2", "PCSK9", "ALK", 
                  "IL-6R", "HER2", "CDK4/6", "SGLT2", "EGFR", "NLRP3", "PD-1", 
                  "GLP-1R", "KRAS G12C", "mTOR", "BRAF"]
        
        target_protein = None
        for target in targets:
            if target.lower() in query_lower:
                target_protein = target
                break
        
        if not target_protein:
            return QueryResponse(
                answer="Please specify which target protein you're interested in (e.g., JAK2, BTK, HER2).",
                evidence=[],
                sources=[],
                interpretation="Query requires target protein specification",
                uncertainty="High",
                agent_used=self.name,
                processing_time_ms=50.0
            )
        
        compounds = db.get_compounds_by_target(target_protein)
        
        if not compounds:
            return QueryResponse(
                answer=f"No compounds found targeting {target_protein}.",
                evidence=[],
                sources=[],
                interpretation=f"No compounds target {target_protein}",
                uncertainty="Medium",
                agent_used=self.name,
                processing_time_ms=80.0
            )
        
        # Analyze compounds
        phase_distribution = {}
        for compound in compounds:
            phase = compound["discovery_phase"]
            phase_distribution[phase] = phase_distribution.get(phase, 0) + 1
        
        evidence = [
            self.create_evidence(
                source="compounds",
                data={
                    "total_compounds": len(compounds),
                    "phase_distribution": phase_distribution
                },
                confidence=0.95,
                description=f"Compounds targeting {target_protein}"
            )
        ]
        
        answer = f"**Compound Overview**\n\nI found {len(compounds)} compounds targeting {target_protein}. "
        answer += f"Phase distribution: {', '.join(f'{k}: {v}' for k, v in phase_distribution.items())}."
        
        sources = [c["compound_id"] for c in compounds[:10]]
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=sources,
            interpretation=f"Portfolio shows {len(compounds)} compounds targeting {target_protein}",
            uncertainty="Low",
            agent_used=self.name,
            processing_time_ms=150.0
        )
    
    def _handle_therapeutic_area_query(self, query: str) -> QueryResponse:
        """Handle queries about therapeutic areas"""
        query_lower = query.lower()
        
        areas = ["oncology", "cardiology", "neurology", "metabolic disease", 
                "respiratory", "immunology", "infectious disease"]
        
        therapeutic_area = None
        for area in areas:
            if area in query_lower:
                therapeutic_area = area.title()
                break
        
        if not therapeutic_area:
            return QueryResponse(
                answer="Please specify which therapeutic area you're interested in (e.g., Oncology, Cardiology, Neurology).",
                evidence=[],
                sources=[],
                interpretation="Query requires therapeutic area specification",
                uncertainty="High",
                agent_used=self.name,
                processing_time_ms=50.0
            )
        
        query_sql = "SELECT * FROM compounds WHERE therapeutic_area = ?"
        compounds = db.execute_query(query_sql, (therapeutic_area,))
        
        if not compounds:
            return QueryResponse(
                answer=f"No compounds found for {therapeutic_area}.",
                evidence=[],
                sources=[],
                interpretation=f"No compounds in {therapeutic_area}",
                uncertainty="Medium",
                agent_used=self.name,
                processing_time_ms=80.0
            )
        
        # Analyze compounds
        class_distribution = {}
        for compound in compounds:
            chem_class = compound["chemical_class"]
            class_distribution[chem_class] = class_distribution.get(chem_class, 0) + 1
        
        evidence = [
            self.create_evidence(
                source="compounds",
                data={
                    "total_compounds": len(compounds),
                    "class_distribution": class_distribution
                },
                confidence=0.95,
                description=f"Compounds in {therapeutic_area}"
            )
        ]
        
        answer = f"**Compound Overview**\n\nI found {len(compounds)} compounds in {therapeutic_area}. "
        answer += f"Chemical class distribution: {', '.join(f'{k}: {v}' for k, v in class_distribution.items())}."
        
        sources = [c["compound_id"] for c in compounds[:10]]
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=sources,
            interpretation=f"Portfolio shows {len(compounds)} compounds in {therapeutic_area}",
            uncertainty="Low",
            agent_used=self.name,
            processing_time_ms=150.0
        )
    
    def _handle_general_compound_query(self, query: str) -> QueryResponse:
        """Handle general compound queries"""
        # Get overall compound statistics
        query_sql = "SELECT therapeutic_area, COUNT(*) as count FROM compounds GROUP BY therapeutic_area"
        area_data = db.execute_query(query_sql)
        
        area_summary = {row["therapeutic_area"]: row["count"] for row in area_data}
        
        query_sql = "SELECT discovery_phase, COUNT(*) as count FROM compounds GROUP BY discovery_phase"
        phase_data = db.execute_query(query_sql)
        
        phase_summary = {row["discovery_phase"]: row["count"] for row in phase_data}
        
        evidence = [
            self.create_evidence(
                source="compounds",
                data={
                    "therapeutic_areas": area_summary,
                    "phases": phase_summary
                },
                confidence=0.95,
                description="Overall compound portfolio statistics"
            )
        ]
        
        total_compounds = sum(area_summary.values())
        answer = f"**Compound Overview**\n\nPortfolio contains {total_compounds} compounds across {len(area_summary)} therapeutic areas. "
        answer += f"Phase distribution: {', '.join(f'{k}: {v}' for k, v in phase_summary.items())}."
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=[],
            interpretation="Portfolio shows balanced therapeutic area distribution",
            uncertainty="Low",
            agent_used=self.name,
            processing_time_ms=100.0
        )
