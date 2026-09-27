from typing import Dict, List, Optional
import logging
from app.agents.base_agent import BaseAgent
from app.data.database import db
from app.data.models import QueryResponse, Evidence, SafetyTriage

logger = logging.getLogger(__name__)


class SafetyAgent(BaseAgent):
    """Specialist agent for safety and adverse event intelligence"""
    
    def __init__(self):
        super().__init__("Safety Intelligence Agent")
        
    def process_query(self, query: str, context: Optional[Dict] = None) -> QueryResponse:
        """Process safety-related queries"""
        query_lower = query.lower()
        
        # Check for trial-specific safety query
        import re
        trial_id_match = re.search(r'TRL-\d+', query, re.IGNORECASE)
        
        if trial_id_match:
            trial_id = trial_id_match.group(0).upper()
            return self._handle_trial_safety_query(trial_id)
        
        # Check for triage request
        if "triage" in query_lower or "escalate" in query_lower:
            return self._handle_triage_query(query)
        
        # Check for specific adverse event type
        if "adverse event" in query_lower or "safety signal" in query_lower:
            return self._handle_adverse_event_query(query)
        
        # Default: general safety information
        return self._handle_general_safety_query(query)
    
    def _handle_trial_safety_query(self, trial_id: str) -> QueryResponse:
        """Handle safety queries for a specific trial"""
        trial = db.get_trial(trial_id)
        
        if not trial:
            return QueryResponse(
                answer=f"I searched for trial {trial_id} but couldn't find it in our safety records. Please verify the trial identifier or let me know if you'd like me to check for a different trial.",
                evidence=[],
                sources=[],
                interpretation="No verified evidence was found for this trial. You may want to verify the trial identifier or ask about available trials."
            )
        
        # Get safety summary
        safety_summary = db.get_safety_summary_by_trial(trial_id)
        adverse_events = db.get_adverse_events_by_trial(trial_id)
        
        evidence = [
            self.create_evidence(
                source="adverse_events",
                data=safety_summary,
                confidence=0.95,
                description=f"Safety summary for trial {trial_id}"
            )
        ]
        
        # Build answer with conversational tone
        answer_parts = [
            f"**Safety Assessment for Trial {trial_id}**",
            f"I've reviewed the safety data for this trial and here's what I found:",
            f"",
            f"**Safety Overview:**",
            f"- **Total Reported Events:** {safety_summary['total_events']}",
            f"- **Serious Events:** {safety_summary['serious_events']}",
            f"- **Severe Events:** {safety_summary['severe_events']}",
            f"- **Events Related to Treatment:** {safety_summary['related_events']}",
            f"- **Current Risk Level:** {safety_summary['risk_level']}"
        ]
        
        if safety_summary['most_common_events']:
            answer_parts.append(f"\n**Most Common Adverse Events:**")
            for event, count in safety_summary['most_common_events']:
                answer_parts.append(f"- {event}: {count} occurrence(s)")
        
        if safety_summary['total_events'] == 0:
            answer_parts.append(f"\n**Good News:** No adverse events have been reported for this trial, which suggests a favorable safety profile so far.")
        
        answer = "\n".join(answer_parts)
        
        # Determine interpretation based on risk level and actual data
        if safety_summary['total_events'] == 0:
            interpretation = "No adverse events reported for this trial, indicating a positive safety profile."
        elif safety_summary['risk_level'] == "High":
            interpretation = f"High risk level detected based on {safety_summary['serious_events']} serious event(s) and {safety_summary['severe_events']} severe event(s). I recommend immediate review and possible intervention."
        elif safety_summary['risk_level'] == "Medium":
            interpretation = f"Medium risk level based on event patterns. I suggest routine monitoring and continued observation."
        else:
            interpretation = f"Low risk level based on available safety data. Standard monitoring protocols should continue."
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=[trial_id] + [ae["event_id"] for ae in adverse_events[:5]],
            interpretation=interpretation
        )
    
    def _handle_triage_query(self, query: str) -> QueryResponse:
        """Handle triage/escalation requests"""
        query_lower = query.lower()
        
        # Extract trial ID if specified
        import re
        trial_id_match = re.search(r'TRL-\d+', query, re.IGNORECASE)
        
        if trial_id_match:
            trial_id = trial_id_match.group(0).upper()
            return self._triage_trial(trial_id)
        
        # If no trial specified, check for serious events across all trials
        serious_events = db.get_serious_adverse_events()
        
        if not serious_events:
            return QueryResponse(
                answer="No serious adverse events requiring triage were found in the available research records.",
                evidence=[],
                sources=[],
                interpretation="No immediate safety concerns identified across the trial portfolio."
            )
        
        # Group by trial
        from collections import defaultdict
        trial_events = defaultdict(list)
        for event in serious_events:
            trial_events[event["trial_id"]].append(event)
        
        # Prioritize trials with most serious events
        prioritized_trials = sorted(
            trial_events.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        evidence = [
            self.create_evidence(
                source="adverse_events",
                data={
                    "total_serious_events": len(serious_events),
                    "affected_trials": len(trial_events),
                    "prioritized_trials": [
                        {
                            "trial_id": trial_id,
                            "serious_event_count": len(events),
                            "events": events[:3]
                        }
                        for trial_id, events in prioritized_trials[:5]
                    ]
                },
                confidence=0.95,
                description="Serious adverse event triage analysis"
            )
        ]
        
        answer_parts = [
            f"**Safety Triage Analysis**",
            f"I found {len(serious_events)} serious adverse event(s) across {len(trial_events)} trial(s) requiring triage.",
            f"\n**Priority Trials for Review:**"
        ]
        
        for trial_id, events in prioritized_trials[:5]:
            answer_parts.append(f"- {trial_id}: {len(events)} serious event(s)")
            for event in events[:2]:
                answer_parts.append(f"  - {event['adverse_event_term']} ({event['severity']}, {event['outcome']})")
        
        answer = "\n".join(answer_parts)
        
        sources = [event["event_id"] for event in serious_events[:10]]
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=sources,
            interpretation=f"Immediate safety review recommended for {len(prioritized_trials)} trial(s) with serious adverse events."
        )
    
    def _triage_trial(self, trial_id: str) -> QueryResponse:
        """Triage a specific trial for safety concerns"""
        trial = db.get_trial(trial_id)
        
        if not trial:
            return QueryResponse(
                answer=f"I couldn't find trial {trial_id} in the available research records.",
                evidence=[],
                sources=[],
                interpretation="No verified evidence was found for this trial. You may want to verify the trial identifier."
            )
        
        # Get adverse events
        adverse_events = db.get_adverse_events_by_trial(trial_id)
        
        # Filter for serious/severe events
        critical_events = [
            ae for ae in adverse_events
            if ae["seriousness"] == "Serious" or ae["severity"] == "Severe"
        ]
        
        if not critical_events:
            return QueryResponse(
                answer=f"Trial {trial_id} has no critical adverse events requiring immediate triage. Total events reported: {len(adverse_events)}.",
                evidence=[
                    self.create_evidence(
                        source="adverse_events",
                        data={"total_events": len(adverse_events), "critical_events": 0},
                        confidence=1.0,
                        description=f"No critical events found for trial {trial_id}"
                    )
                ],
                sources=[trial_id],
                interpretation="No immediate safety concerns identified. Routine monitoring continues."
            )
        
        # Build triage report
        evidence = [
            self.create_evidence(
                source="adverse_events",
                data={
                    "total_events": len(adverse_events),
                    "critical_events": len(critical_events),
                    "events": critical_events
                },
                confidence=1.0,
                description=f"Critical adverse events for trial {trial_id}"
            )
        ]
        
        # Categorize events
        serious_count = sum(1 for ae in critical_events if ae["seriousness"] == "Serious")
        severe_count = sum(1 for ae in critical_events if ae["severity"] == "Severe")
        fatal_count = sum(1 for ae in critical_events if ae["outcome"] == "Fatal")
        
        answer_parts = [
            f"**Safety Triage for Trial {trial_id}**",
            f"**Critical Events Requiring Attention:** {len(critical_events)}",
            f"**Serious Events:** {serious_count}",
            f"**Severe Events:** {severe_count}",
            f"**Fatal Outcomes:** {fatal_count}"
        ]
        
        # Add event details
        if critical_events:
            answer_parts.append(f"\n**Critical Event Details:**")
            for ae in critical_events[:5]:
                answer_parts.append(
                    f"- {ae['adverse_event_term']} ({ae['severity']}, {ae['seriousness']}) "
                    f"on {ae['event_date']} - {ae['outcome']}"
                )
        
        answer = "\n".join(answer_parts)
        
        # Determine triage priority based on actual data
        if fatal_count > 0:
            interpretation = f"Fatal events detected ({fatal_count}). Immediate investigation required."
        elif serious_count > 0:
            interpretation = f"Serious events detected ({serious_count}). Urgent review required."
        else:
            interpretation = f"Severe events detected ({severe_count}). Prompt review recommended."
        
        sources = [trial_id] + [ae["event_id"] for ae in critical_events]
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=sources,
            interpretation=interpretation
        )
    
    def _handle_adverse_event_query(self, query: str) -> QueryResponse:
        """Handle queries about specific adverse events"""
        query_lower = query.lower()
        
        # Try to extract event type
        event_terms = ["headache", "nausea", "diarrhea", "rash", "fatigue", "dizziness", 
                      "anemia", "pyrexia", "vomiting", "cough", "insomnia", "hypertension",
                      "qt prolongation", "elevated liver enzymes", "neutropenia", "thrombocytopenia",
                      "peripheral neuropathy", "injection site reaction", "decreased appetite"]
        
        event_term = None
        for term in event_terms:
            if term in query_lower:
                event_term = term
                break
        
        if event_term:
            events = db.search_adverse_events_by_term(event_term)
            
            if not events:
                return QueryResponse(
                    answer=f"I couldn't find adverse events matching '{event_term}' in the available research records.",
                    evidence=[],
                    sources=[],
                    interpretation=f"No data was found for the specified event type. You may want to try a different adverse event term or ask about overall safety patterns."
                )
            
            # Analyze events
            severity_counts = {}
            seriousness_counts = {}
            outcome_counts = {}
            for event in events:
                severity = event["severity"]
                seriousness = event["seriousness"]
                outcome = event["outcome"]
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                seriousness_counts[seriousness] = seriousness_counts.get(seriousness, 0) + 1
                outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
            
            evidence = [
                self.create_evidence(
                    source="adverse_events",
                    data={
                        "total_events": len(events),
                        "severity_distribution": severity_counts,
                        "seriousness_distribution": seriousness_counts,
                        "outcome_distribution": outcome_counts
                    },
                    confidence=0.90,
                    description=f"Adverse events matching '{event_term}'"
                )
            ]
            
            answer_parts = [
                f"**Adverse Event Analysis**",
                f"I found {len(events)} adverse event(s) matching '{event_term}'.",
                f"\n**Severity Distribution:**",
            ]
            
            for severity, count in sorted(severity_counts.items()):
                answer_parts.append(f"- {severity}: {count} event(s)")
            
            answer_parts.append(f"\n**Seriousness Distribution:**")
            for seriousness, count in sorted(seriousness_counts.items()):
                answer_parts.append(f"- {seriousness}: {count} event(s)")
            
            answer_parts.append(f"\n**Outcome Distribution:**")
            for outcome, count in sorted(outcome_counts.items()):
                answer_parts.append(f"- {outcome}: {count} event(s)")
            
            answer = "\n".join(answer_parts)
            
            sources = [e["event_id"] for e in events[:10]]
            
            return QueryResponse(
                answer=answer,
                evidence=evidence,
                sources=sources,
                interpretation=f"Event pattern analysis for {event_term} shows {len(events)} occurrences across the trial portfolio."
            )
        
        # General adverse event query
        query_sql = "SELECT adverse_event_term, COUNT(*) as count FROM adverse_events GROUP BY adverse_event_term ORDER BY count DESC LIMIT 10"
        common_events = db.execute_query(query_sql)
        
        evidence = [
            self.create_evidence(
                source="adverse_events",
                data={"most_common_events": common_events},
                confidence=0.95,
                description="Most common adverse events across all trials"
            )
        ]
        
        answer_parts = [
            f"**Adverse Event Overview**",
            f"Most common adverse events across the trial portfolio:",
        ]
        
        for event in common_events:
            answer_parts.append(f"- {event['adverse_event_term']}: {event['count']} occurrence(s)")
        
        answer = "\n".join(answer_parts)
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=[],
            interpretation="Overall adverse event patterns across the trial portfolio."
        )
    
    def _handle_general_safety_query(self, query: str) -> QueryResponse:
        """Handle general safety queries"""
        # Get overall safety statistics
        query_sql = "SELECT seriousness, COUNT(*) as count FROM adverse_events GROUP BY seriousness"
        seriousness_data = db.execute_query(query_sql)
        
        seriousness_summary = {row["seriousness"]: row["count"] for row in seriousness_data}
        
        query_sql = "SELECT severity, COUNT(*) as count FROM adverse_events GROUP BY severity"
        severity_data = db.execute_query(query_sql)
        
        severity_summary = {row["severity"]: row["count"] for row in severity_data}
        
        evidence = [
            self.create_evidence(
                source="adverse_events",
                data={
                    "seriousness_distribution": seriousness_summary,
                    "severity_distribution": severity_summary
                },
                confidence=0.95,
                description="Overall safety statistics"
            )
        ]
        
        total_events = sum(seriousness_summary.values())
        serious_percentage = (seriousness_summary.get("Serious", 0) / total_events * 100) if total_events > 0 else 0
        
        answer_parts = [
            f"**Safety Overview**",
            f"**Total Adverse Events:** {total_events}",
            f"**Serious Events:** {seriousness_summary.get('Serious', 0)} ({serious_percentage:.1f}%)",
            f"\n**Severity Distribution:**",
        ]
        
        for severity, count in sorted(severity_summary.items()):
            answer_parts.append(f"- {severity}: {count} event(s)")
        
        answer_parts.append(f"\n**Seriousness Distribution:**")
        for seriousness, count in sorted(seriousness_summary.items()):
            answer_parts.append(f"- {seriousness}: {count} event(s)")
        
        answer = "\n".join(answer_parts)
        
        return QueryResponse(
            answer=answer,
            evidence=evidence,
            sources=[],
            interpretation=f"Overall safety profile shows {total_events} adverse events with {serious_percentage:.1f}% classified as serious."
        )
