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
                answer=f"I couldn't find verified records matching {compound_id} in the available research evidence.",
                evidence=[],
                sources=[],
                interpretation="Without matching evidence, I can't provide a verified clinical, laboratory, safety, or research assessment for this compound. You can try another compound identifier or ask about a related clinical trial, safety event, laboratory result, or research topic."
            )
        
        # Get related data
        trials = db.execute_query(
            "SELECT * FROM clinical_trials WHERE compound_id = ?",
            (compound_id,)
        )
        lab_results = db.get_lab_results_by_compound(compound_id)
        documents = db.get_documents_by_compound(compound_id)
        
        # Build comprehensive response with question-aware formatting
        evidence = []
        answer_parts = []
        
        # Compound overview
        answer_parts.append(f"**Compound Overview**")
        answer_parts.append(f"**{compound_id}** ({compound['compound_name']}) is a {compound['chemical_class']} targeting {compound['target_protein']} for {compound['therapeutic_area']}.")
        answer_parts.append(f"**Development Phase:** {compound['discovery_phase']}")
        answer_parts.append(f"**Mechanism of Action:** {compound['mechanism_of_action']}")
        
        evidence.append(
            self.create_evidence(
                source="compounds",
                data=compound,
                confidence=1.0,
                description=f"Compound record {compound_id}"
            )
        )
        
        # Clinical trial evidence
        if trials:
            active_trials = [t for t in trials if t["status"] in ["Recruiting", "Active, not recruiting"]]
            completed_trials = [t for t in trials if t["status"] == "Completed"]
            
            answer_parts.append(f"\n**Clinical Evidence**")
            answer_parts.append(f"This compound is associated with {len(trials)} clinical trial(s).")
            if active_trials:
                answer_parts.append(f"- {len(active_trials)} trial(s) currently active or recruiting")
            if completed_trials:
                answer_parts.append(f"- {len(completed_trials)} trial(s) completed")
            
            # Add specific trial evidence
            for trial in trials[:3]:
                answer_parts.append(f"- Trial {trial['trial_id']}: {trial['trial_phase']} in {trial['therapeutic_area']} - Status: {trial['status']}")
            
            evidence.append(
                self.create_evidence(
                    source="clinical_trials",
                    data={"trial_count": len(trials), "trials": trials},
                    confidence=0.95,
                    description=f"Clinical trials for {compound_id}"
                )
            )
        
        # Laboratory evidence
        if lab_results:
            pass_fail_counts = {"Pass": 0, "Fail": 0}
            for result in lab_results:
                pass_fail_counts[result["pass_fail"]] = pass_fail_counts.get(result["pass_fail"], 0) + 1
            
            pass_rate = pass_fail_counts.get("Pass", 0) / len(lab_results) * 100
            
            answer_parts.append(f"\n**Laboratory Evidence**")
            answer_parts.append(f"{len(lab_results)} laboratory test(s) completed with a {pass_rate:.1f}% pass rate.")
            answer_parts.append(f"- Passed: {pass_fail_counts.get('Pass', 0)}")
            answer_parts.append(f"- Failed: {pass_fail_counts.get('Fail', 0)}")
            
            evidence.append(
                self.create_evidence(
                    source="lab_results",
                    data={
                        "total_results": len(lab_results),
                        "pass_fail_counts": pass_fail_counts
                    },
                    confidence=0.90,
                    description=f"Laboratory results for {compound_id}"
                )
            )
        
        # Research evidence
        if documents:
            answer_parts.append(f"\n**Research Evidence**")
            answer_parts.append(f"{len(documents)} research document(s) available for this compound.")
            
            for doc in documents[:3]:
                answer_parts.append(f"- Document {doc['doc_id']}: {doc['title']}")
            
            evidence.append(
                self.create_evidence(
                    source="research_documents",
                    data={"document_count": len(documents), "documents": documents},
                    confidence=0.85,
                    description=f"Research documents for {compound_id}"
                )
            )
        
        # Handle partial evidence
        if not trials and not lab_results and not documents:
            answer_parts.append(f"\n**Evidence Availability**")
            answer_parts.append(f"While the compound record exists, no associated clinical trials, laboratory results, or research documents were found in the available evidence.")
        
        answer = "\n\n".join(answer_parts)
        
        # Build interpretation based on available evidence
        interpretation_parts = []
        if trials:
            interpretation_parts.append(f"Clinical trial data shows {len(trials)} associated trial(s).")
        if lab_results:
            interpretation_parts.append(f"Laboratory testing shows {pass_fail_counts.get('Pass', 0)}/{len(lab_results)} tests passed.")
        if documents:
            interpretation_parts.append(f"Research documentation includes {len(documents)} document(s).")
        
        if interpretation_parts:
            interpretation = " ".join(interpretation_parts)
        else:
            interpretation = "Basic compound information is available, but additional evidence from trials, laboratory results, or research documents was not found."
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=[compound_id] + [t["trial_id"] for t in trials[:5]] + [d["doc_id"] for d in documents[:3]],
            interpretation=interpretation
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
                answer="I can help you find compounds targeting specific proteins. Please specify which target protein you're interested in (e.g., JAK2, BTK, HER2, EGFR).",
                evidence=[],
                sources=[],
                interpretation="This query requires a specific target protein to provide relevant compound information."
            )
        
        compounds = db.get_compounds_by_target(target_protein)
        
        if not compounds:
            return QueryResponse(
                answer=f"I couldn't find any compounds targeting {target_protein} in the available research records.",
                evidence=[],
                sources=[],
                interpretation=f"No evidence was found for compounds targeting {target_protein}. You may want to try a different target protein or ask about available therapeutic areas."
            )
        
        # Analyze compounds
        phase_distribution = {}
        therapeutic_areas = {}
        for compound in compounds:
            phase = compound["discovery_phase"]
            phase_distribution[phase] = phase_distribution.get(phase, 0) + 1
            
            area = compound["therapeutic_area"]
            therapeutic_areas[area] = therapeutic_areas.get(area, 0) + 1
        
        evidence = [
            self.create_evidence(
                source="compounds",
                data={
                    "total_compounds": len(compounds),
                    "phase_distribution": phase_distribution,
                    "therapeutic_areas": therapeutic_areas
                },
                confidence=0.95,
                description=f"Compounds targeting {target_protein}"
            )
        ]
        
        answer_parts = [
            f"**Target Protein Analysis**",
            f"I found {len(compounds)} compound(s) targeting {target_protein}.",
            f"\n**Development Phase Distribution:**",
        ]
        
        for phase, count in sorted(phase_distribution.items()):
            answer_parts.append(f"- {phase}: {count} compound(s)")
        
        answer_parts.append(f"\n**Therapeutic Areas:**")
        for area, count in sorted(therapeutic_areas.items()):
            answer_parts.append(f"- {area}: {count} compound(s)")
        
        answer_parts.append(f"\n**Sample Compounds:**")
        for compound in compounds[:5]:
            answer_parts.append(f"- {compound['compound_id']} ({compound['compound_name']}) - {compound['chemical_class']}")
        
        answer = "\n".join(answer_parts)
        
        sources = [c["compound_id"] for c in compounds[:10]]
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=sources,
            interpretation=f"The portfolio includes {len(compounds)} compounds targeting {target_protein} across {len(therapeutic_areas)} therapeutic area(s)."
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
                answer="I can help you explore compounds by therapeutic area. Please specify which area you're interested in (e.g., Oncology, Cardiology, Neurology, Metabolic Disease).",
                evidence=[],
                sources=[],
                interpretation="This query requires a specific therapeutic area to provide relevant compound information."
            )
        
        query_sql = "SELECT * FROM compounds WHERE therapeutic_area = ?"
        compounds = db.execute_query(query_sql, (therapeutic_area,))
        
        if not compounds:
            return QueryResponse(
                answer=f"I couldn't find any compounds for {therapeutic_area} in the available research records.",
                evidence=[],
                sources=[],
                interpretation=f"No evidence was found for compounds in {therapeutic_area}. You may want to try a different therapeutic area."
            )
        
        # Analyze compounds
        class_distribution = {}
        phase_distribution = {}
        target_proteins = {}
        
        for compound in compounds:
            chem_class = compound["chemical_class"]
            class_distribution[chem_class] = class_distribution.get(chem_class, 0) + 1
            
            phase = compound["discovery_phase"]
            phase_distribution[phase] = phase_distribution.get(phase, 0) + 1
            
            target = compound["target_protein"]
            target_proteins[target] = target_proteins.get(target, 0) + 1
        
        evidence = [
            self.create_evidence(
                source="compounds",
                data={
                    "total_compounds": len(compounds),
                    "class_distribution": class_distribution,
                    "phase_distribution": phase_distribution,
                    "target_proteins": target_proteins
                },
                confidence=0.95,
                description=f"Compounds in {therapeutic_area}"
            )
        ]
        
        answer_parts = [
            f"**Therapeutic Area Analysis**",
            f"I found {len(compounds)} compound(s) in {therapeutic_area}.",
            f"\n**Chemical Class Distribution:**",
        ]
        
        for chem_class, count in sorted(class_distribution.items()):
            answer_parts.append(f"- {chem_class}: {count} compound(s)")
        
        answer_parts.append(f"\n**Development Phase Distribution:**")
        for phase, count in sorted(phase_distribution.items()):
            answer_parts.append(f"- {phase}: {count} compound(s)")
        
        answer_parts.append(f"\n**Target Proteins:**")
        for target, count in sorted(target_proteins.items(), key=lambda x: x[1], reverse=True)[:5]:
            answer_parts.append(f"- {target}: {count} compound(s)")
        
        answer_parts.append(f"\n**Sample Compounds:**")
        for compound in compounds[:5]:
            answer_parts.append(f"- {compound['compound_id']} ({compound['compound_name']}) - {compound['chemical_class']}")
        
        answer = "\n".join(answer_parts)
        
        sources = [c["compound_id"] for c in compounds[:10]]
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=sources,
            interpretation=f"The portfolio includes {len(compounds)} compounds in {therapeutic_area} across {len(class_distribution)} chemical class(es)."
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
        
        query_sql = "SELECT chemical_class, COUNT(*) as count FROM compounds GROUP BY chemical_class"
        class_data = db.execute_query(query_sql)
        
        class_summary = {row["chemical_class"]: row["count"] for row in class_data}
        
        evidence = [
            self.create_evidence(
                source="compounds",
                data={
                    "therapeutic_areas": area_summary,
                    "phases": phase_summary,
                    "chemical_classes": class_summary
                },
                confidence=0.95,
                description="Overall compound portfolio statistics"
            )
        ]
        
        total_compounds = sum(area_summary.values())
        
        answer_parts = [
            f"**Compound Portfolio Overview**",
            f"The portfolio contains {total_compounds} compounds across {len(area_summary)} therapeutic area(s).",
            f"\n**Therapeutic Area Distribution:**",
        ]
        
        for area, count in sorted(area_summary.items()):
            answer_parts.append(f"- {area}: {count} compound(s)")
        
        answer_parts.append(f"\n**Development Phase Distribution:**")
        for phase, count in sorted(phase_summary.items()):
            answer_parts.append(f"- {phase}: {count} compound(s)")
        
        answer_parts.append(f"\n**Chemical Class Distribution:**")
        for chem_class, count in sorted(class_summary.items()):
            answer_parts.append(f"- {chem_class}: {count} compound(s)")
        
        answer = "\n".join(answer_parts)
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=[],
            interpretation=f"The compound portfolio spans {len(area_summary)} therapeutic area(s) with compounds at various development phases."
        )
