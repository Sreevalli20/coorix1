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
                    data={"total_trials": len(trials), "below_threshold": len(trials_below)},
                    confidence=0.95,
                    description=f"Found {len(trials_below)} {phase} {therapeutic_area} trials below {threshold}% enrollment"
                )
            ]
            
            answer = f"Found {len(trials_below)} {phase} {therapeutic_area} trials below {threshold}% enrollment out of {len(trials)} total {phase} {therapeutic_area} trials."
            
            sources = [t["trial_id"] for t in trials_below]
            
        else:
            trials = db.get_trials_below_enrollment_threshold(threshold)
            
            evidence = [
                self.create_evidence(
                    source="clinical_trials",
                    data={"total_below_threshold": len(trials)},
                    confidence=0.90,
                    description=f"Found {len(trials)} trials below {threshold}% enrollment"
                )
            ]
            
            answer = f"Found {len(trials)} trials below {threshold}% enrollment across all phases and therapeutic areas."
            sources = [t["trial_id"] for t in trials]
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=sources,
            interpretation="Enrollment data reflects current recruitment status. Trials below threshold may require intervention.",
            uncertainty="Low",
            agent_used=self.name,
            processing_time_ms=150.0
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
                answer="Please specify which clinical trial phase you're interested in (Phase I, II, III, or IV).",
                evidence=[],
                sources=[],
                interpretation="Query requires phase specification",
                uncertainty="High",
                agent_used=self.name,
                processing_time_ms=50.0
            )
        
        # Get trials by phase
        query_sql = "SELECT * FROM clinical_trials WHERE trial_phase = ?"
        trials = db.execute_query(query_sql, (phase,))
        
        # Calculate statistics
        total_trials = len(trials)
        status_counts = {}
        for trial in trials:
            status = trial["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        evidence = [
            self.create_evidence(
                source="clinical_trials",
                data={
                    "total_trials": total_trials,
                    "status_breakdown": status_counts
                },
                confidence=0.95,
                description=f"Phase {phase} trial statistics"
            )
        ]
        
        answer = f"Found {total_trials} {phase} trials. Status breakdown: {', '.join(f'{k}: {v}' for k, v in status_counts.items())}."
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=[t["trial_id"] for t in trials[:10]],
            interpretation="Phase distribution shows current portfolio status",
            uncertainty="Low",
            agent_used=self.name,
            processing_time_ms=120.0
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
                
                answer = f"Trial {trial_id} is currently {trial['status']}. Target enrollment: {trial['target_enrollment']}, Actual enrollment: {trial['actual_enrollment']}."
                
                return QueryResponse(
                    answer=answer,
                    evidence=evidence,
                    sources=[trial_id],
                    interpretation="Trial status reflects current operational state",
                    uncertainty="Low",
                    agent_used=self.name,
                    processing_time_ms=80.0
                )
            else:
                return QueryResponse(
                    answer=f"Trial {trial_id} not found in database.",
                    evidence=[],
                    sources=[],
                    interpretation="Specified trial ID not found",
                    uncertainty="High",
                    agent_used=self.name,
                    processing_time_ms=50.0
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
        
        answer = f"Current trial status distribution: {', '.join(f'{k}: {v}' for k, v in status_summary.items())}."
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=[],
            interpretation="Status distribution shows portfolio health",
            uncertainty="Low",
            agent_used=self.name,
            processing_time_ms=100.0
        )
    
    def _handle_general_trial_query(self, query: str) -> QueryResponse:
        """Handle general trial queries"""
        return QueryResponse(
            answer="I can help you with trial enrollment analysis, phase-specific information, and trial status. Please specify what you'd like to know about clinical trials.",
            evidence=[],
            sources=[],
            interpretation="General trial information request",
            uncertainty="Medium",
            agent_used=self.name,
            processing_time_ms=50.0
        )
