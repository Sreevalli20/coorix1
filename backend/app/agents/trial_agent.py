from typing import Dict, List, Optional
import logging
from app.agents.base_agent import BaseAgent
from app.data.database import db
from app.data.models import QueryResponse, Evidence

logger = logging.getLogger(__name__)


class TrialAgent(BaseAgent):
    """Specialist agent for clinical trial intelligence"""
    
    def __init__(self):
        super().__init__("Trial Intelligence Agent")
        
    def process_query(self, query: str, context: Optional[Dict] = None) -> QueryResponse:
        """Process trial-related queries"""
        query_lower = query.lower()
        
        # Check for enrollment queries
        if "enrollment" in query_lower and "below" in query_lower:
            return self._handle_enrollment_query(query)
        
        # Check for phase-specific queries
        if "phase" in query_lower:
            return self._handle_phase_query(query)
        
        # Check for trial status queries
        if "status" in query_lower:
            return self._handle_status_query(query)
        
        # Default: general trial information
        return self._handle_general_trial_query(query)
    
    def _handle_enrollment_query(self, query: str) -> QueryResponse:
        """Handle queries about trial enrollment"""
        query_lower = query.lower()
        
        # Extract phase and therapeutic area if specified
        phase = None
        therapeutic_area = None
        threshold = 60.0
        
        # Parse phase (check for Phase II first, then others)
        if "phase ii" in query_lower:
            phase = "Phase II"
        elif "phase i" in query_lower:
            phase = "Phase I"
        elif "phase iii" in query_lower:
            phase = "Phase III"
        elif "phase iv" in query_lower:
            phase = "Phase IV"
        
        # Parse therapeutic area
        areas = ["oncology", "cardiology", "neurology", "metabolic disease", 
                "respiratory", "immunology", "infectious disease"]
        for area in areas:
            if area in query_lower:
                therapeutic_area = area.title()
                break
        
        # Parse threshold
        import re
        threshold_match = re.search(r'(\d+)%', query)
        if threshold_match:
            threshold = float(threshold_match.group(1))
        
        # Query database
        if phase and therapeutic_area:
            trials = db.get_trials_by_phase_and_area(phase, therapeutic_area)
            trials_below = [t for t in trials if t.get("enrollment_pct", 0) < threshold]
            
            evidence = [
                self.create_evidence(
                    source="clinical_trials",
                    data={"total_trials": len(trials), "below_threshold": len(trials_below), "trials": trials_below},
                    confidence=0.95,
                    description=f"{phase} {therapeutic_area} trials below {threshold}% enrollment"
                )
            ]
            
            answer_parts = [
                f"**Enrollment Analysis**",
                f"I found {len(trials_below)} {phase} {therapeutic_area} trial(s) below {threshold}% enrollment out of {len(trials)} total {phase} {therapeutic_area} trials.",
                f"\n**Trials Below Target:**"
            ]
            
            for trial in trials_below[:5]:
                enrollment_pct = trial.get("enrollment_pct", 0)
                answer_parts.append(f"- {trial['trial_id']}: {enrollment_pct:.1f}% enrollment (Target: {trial['target_enrollment']}, Actual: {trial['actual_enrollment']}) - Status: {trial['status']}")
            
            if len(trials_below) > 5:
                answer_parts.append(f"- ... and {len(trials_below) - 5} more trial(s)")
            
            answer = "\n".join(answer_parts)
            sources = [t["trial_id"] for t in trials_below]
            
        else:
            trials = db.get_trials_below_enrollment_threshold(threshold)
            
            evidence = [
                self.create_evidence(
                    source="clinical_trials",
                    data={"total_below_threshold": len(trials), "trials": trials},
                    confidence=0.90,
                    description=f"Trials below {threshold}% enrollment"
                )
            ]
            
            answer_parts = [
                f"**Enrollment Analysis**",
                f"I found {len(trials)} trial(s) below {threshold}% enrollment across all phases and therapeutic areas.",
                f"\n**Trials Below Target:**"
            ]
            
            for trial in trials[:5]:
                enrollment_pct = trial.get("enrollment_pct", 0)
                answer_parts.append(f"- {trial['trial_id']} ({trial['trial_phase']}, {trial['therapeutic_area']}): {enrollment_pct:.1f}% enrollment - Status: {trial['status']}")
            
            if len(trials) > 5:
                answer_parts.append(f"- ... and {len(trials) - 5} more trial(s)")
            
            answer = "\n".join(answer_parts)
            sources = [t["trial_id"] for t in trials]
        
        interpretation = f"These trials may require recruitment intervention to meet enrollment targets. {len(trials_below if phase and therapeutic_area else trials)} trial(s) are below the {threshold}% threshold."
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=sources,
            interpretation=interpretation
        )
    
    def _handle_phase_query(self, query: str) -> QueryResponse:
        """Handle phase-specific queries"""
        query_lower = query.lower()
        
        # Extract phase
        phase = None
        for p in ["phase i", "phase ii", "phase iii", "phase iv"]:
            if p in query_lower:
                phase = p.replace(" ", " ").title()
                break
        
        if not phase:
            return QueryResponse(
                answer="I can help you analyze trials by phase. Please specify which clinical trial phase you're interested in (Phase I, II, III, or IV).",
                evidence=[],
                sources=[],
                interpretation="This query requires a specific phase to provide relevant trial information."
            )
        
        # Get trials by phase
        query_sql = "SELECT * FROM clinical_trials WHERE trial_phase = ?"
        trials = db.execute_query(query_sql, (phase,))
        
        if not trials:
            return QueryResponse(
                answer=f"I couldn't find any {phase} trials in the available research records.",
                evidence=[],
                sources=[],
                interpretation=f"No evidence was found for {phase} trials."
            )
        
        # Calculate statistics
        total_trials = len(trials)
        status_counts = {}
        therapeutic_areas = {}
        
        for trial in trials:
            status = trial["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            
            area = trial["therapeutic_area"]
            therapeutic_areas[area] = therapeutic_areas.get(area, 0) + 1
        
        evidence = [
            self.create_evidence(
                source="clinical_trials",
                data={
                    "total_trials": total_trials,
                    "status_breakdown": status_counts,
                    "therapeutic_areas": therapeutic_areas
                },
                confidence=0.95,
                description=f"{phase} trial statistics"
            )
        ]
        
        answer_parts = [
            f"**Phase Analysis**",
            f"I found {total_trials} {phase} trial(s) in the available research records.",
            f"\n**Status Distribution:**",
        ]
        
        for status, count in sorted(status_counts.items()):
            answer_parts.append(f"- {status}: {count} trial(s)")
        
        answer_parts.append(f"\n**Therapeutic Areas:**")
        for area, count in sorted(therapeutic_areas.items()):
            answer_parts.append(f"- {area}: {count} trial(s)")
        
        answer_parts.append(f"\n**Sample Trials:**")
        for trial in trials[:5]:
            answer_parts.append(f"- {trial['trial_id']}: {trial['therapeutic_area']} - Status: {trial['status']}")
        
        answer = "\n".join(answer_parts)
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=[t["trial_id"] for t in trials[:10]],
            interpretation=f"{phase} includes {total_trials} trial(s) across {len(therapeutic_areas)} therapeutic area(s)."
        )
    
    def _handle_status_query(self, query: str) -> QueryResponse:
        """Handle trial status queries"""
        query_lower = query.lower()
        
        # Extract trial ID if specified
        import re
        trial_id_match = re.search(r'TRL-\d+', query, re.IGNORECASE)
        
        if trial_id_match:
            trial_id = trial_id_match.group(0).upper()
            trial = db.get_trial(trial_id)
            
            if trial:
                evidence = [
                    self.create_evidence(
                        source="clinical_trials",
                        data=trial,
                        confidence=1.0,
                        description=f"Trial {trial_id} status information"
                    )
                ]
                
                enrollment_pct = (trial['actual_enrollment'] / trial['target_enrollment'] * 100) if trial['target_enrollment'] > 0 else 0
                
                answer_parts = [
                    f"**Trial Status**",
                    f"**Trial:** {trial_id}",
                    f"**Status:** {trial['status']}",
                    f"**Phase:** {trial['trial_phase']}",
                    f"**Therapeutic Area:** {trial['therapeutic_area']}",
                    f"**Enrollment:** {trial['actual_enrollment']} / {trial['target_enrollment']} ({enrollment_pct:.1f}%)",
                    f"**Primary Endpoint:** {trial['primary_endpoint']}",
                    f"**Sponsor:** {trial['sponsor']}"
                ]
                
                answer = "\n".join(answer_parts)
                
                return QueryResponse(
                    answer=answer,
                    evidence=evidence,
                    sources=[trial_id],
                    interpretation=f"Trial {trial_id} is currently {trial['status']} with {enrollment_pct:.1f}% enrollment achieved."
                )
            else:
                return QueryResponse(
                    answer=f"I couldn't find trial {trial_id} in the available research records.",
                    evidence=[],
                    sources=[],
                    interpretation="No verified evidence was found for this trial. You may want to verify the trial identifier or ask about available trials."
                )
        
        # General status query
        query_sql = "SELECT status, COUNT(*) as count FROM clinical_trials GROUP BY status"
        status_data = db.execute_query(query_sql)
        
        status_summary = {row["status"]: row["count"] for row in status_data}
        
        evidence = [
            self.create_evidence(
                source="clinical_trials",
                data=status_summary,
                confidence=0.95,
                description="Overall trial status distribution"
            )
        ]
        
        answer_parts = [
            f"**Trial Status Overview**",
            f"Current trial status distribution across the portfolio:",
        ]
        
        for status, count in sorted(status_summary.items()):
            answer_parts.append(f"- {status}: {count} trial(s)")
        
        answer = "\n".join(answer_parts)
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=[],
            interpretation=f"The portfolio includes {sum(status_summary.values())} trials across {len(status_summary)} different status categories."
        )
    
    def _handle_general_trial_query(self, query: str) -> QueryResponse:
        """Handle general trial queries"""
        return QueryResponse(
            answer="I can help you with trial enrollment analysis, phase-specific information, and trial status. Please specify what you'd like to know about clinical trials.",
            evidence=[],
            sources=[],
            interpretation="General trial information request"
        )
