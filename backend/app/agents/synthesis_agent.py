from typing import Dict, List, Optional
import logging
from app.agents.base_agent import BaseAgent
from app.data.database import db
from app.data.models import QueryResponse, Evidence

logger = logging.getLogger(__name__)


class SynthesisAgent(BaseAgent):
    """Agent that synthesizes responses from multiple specialist agents"""
    
    def __init__(self):
        super().__init__("Synthesis Agent")
        
    def process_query(self, query: str, context: Optional[Dict] = None) -> QueryResponse:
        """Synthesize a comprehensive response from multiple agent outputs"""
        # Import agents here to avoid circular imports
        from app.agents.trial_agent import TrialAgent
        from app.agents.compound_agent import CompoundAgent
        from app.agents.safety_agent import SafetyAgent
        from app.agents.research_agent import ResearchAgent
        
        query_lower = query.lower()
        
        # Determine which agents to invoke based on query
        agents_to_invoke = []
        
        if "trial" in query_lower or "enrollment" in query_lower:
            agents_to_invoke.append(("trial", TrialAgent()))
        
        if "compound" in query_lower:
            agents_to_invoke.append(("compound", CompoundAgent()))
        
        if "adverse" in query_lower or "safety" in query_lower or "triage" in query_lower:
            agents_to_invoke.append(("safety", SafetyAgent()))
        
        if "research" in query_lower or "literature" in query_lower or "document" in query_lower:
            agents_to_invoke.append(("research", ResearchAgent()))
        
        # If no specific agents identified, invoke all for comprehensive analysis
        if not agents_to_invoke:
            agents_to_invoke = [
                ("trial", TrialAgent()),
                ("compound", CompoundAgent()),
                ("safety", SafetyAgent()),
                ("research", ResearchAgent())
            ]
        
        # Collect responses from all agents
        agent_responses = {}
        all_evidence = []
        all_sources = []
        
        for agent_name, agent in agents_to_invoke:
            try:
                response = agent.process_query(query, context)
                agent_responses[agent_name] = response
                all_evidence.extend(response.evidence)
                all_sources.extend(response.sources)
            except Exception as e:
                logger.error(f"Error invoking {agent_name} agent: {e}")
                agent_responses[agent_name] = None
        
        # Synthesize the response
        return self._synthesize_response(query, agent_responses, all_evidence, all_sources)
    
    def _synthesize_response(self, query: str, agent_responses: Dict[str, Optional[QueryResponse]], 
                           all_evidence: List[Evidence], all_sources: List[str]) -> QueryResponse:
        """Synthesize a comprehensive response from multiple agent outputs"""
        
        # Filter out None responses
        valid_responses = {k: v for k, v in agent_responses.items() if v is not None}
        
        if not valid_responses:
            return QueryResponse(
                answer="Unable to process query. No specialist agents available.",
                evidence=[],
                sources=[],
                interpretation="System error - no agents responded",
                uncertainty="High",
                agent_used=self.name,
                processing_time_ms=0
            )
        
        # Build synthesized answer
        answer_parts = [f"**Comprehensive Analysis**\n\n"]
        
        # Add insights from each agent
        for agent_name, response in valid_responses.items():
            if response and response.answer:
                answer_parts.append(f"\n{response.answer}")
        
        # Combine all evidence
        synthesized_evidence = []
        for evidence in all_evidence:
            # Avoid duplicate evidence
            if not any(e.source == evidence.source and e.description == evidence.description 
                      for e in synthesized_evidence):
                synthesized_evidence.append(evidence)
        
        # Deduplicate sources
        unique_sources = list(set(all_sources))
        
        # Determine overall uncertainty
        uncertainties = [r.uncertainty for r in valid_responses.values() if r]
        if "High" in uncertainties:
            overall_uncertainty = "High"
        elif "Medium" in uncertainties:
            overall_uncertainty = "Medium"
        else:
            overall_uncertainty = "Low"
        
        # Build interpretation
        num_agents = len(valid_responses)
        interpretation = f"Analysis based on {num_agents} data source(s). "
        
        if num_agents > 1:
            interpretation += "Multi-source analysis provides comprehensive coverage."
        else:
            interpretation += "Single source analysis provided."
        
        answer = "\n".join(answer_parts)
        
        return QueryResponse(
            answer=answer,
            evidence=synthesized_evidence,
            sources=unique_sources,
            interpretation=interpretation,
            uncertainty=overall_uncertainty,
            agent_used=self.name,
            processing_time_ms=sum(r.processing_time_ms for r in valid_responses.values() if r)
        )
    
    def synthesize_compound_profile(self, compound_id: str) -> QueryResponse:
        """Synthesize a complete compound profile from all data sources"""
        from app.agents.compound_agent import CompoundAgent
        from app.agents.safety_agent import SafetyAgent
        from app.agents.research_agent import ResearchAgent
        from app.data.database import db as database
        
        # First, try to get the compound ID if a name was provided
        compound = database.get_compound(compound_id)
        if not compound:
            # Try to find by compound name
            query_sql = "SELECT compound_id FROM compounds WHERE compound_name = ?"
            results = database.execute_query(query_sql, (compound_id,))
            if results:
                compound_id = results[0]["compound_id"]
                compound = database.get_compound(compound_id)
        
        if not compound:
            return QueryResponse(
                answer=f"I couldn't find {compound_id} in the available research records.",
                evidence=[],
                sources=[],
                interpretation="No verified evidence was found for this compound.",
                uncertainty="High",
                agent_used=self.name,
                processing_time_ms=50.0
            )
        
        query = f"Tell me everything about compound {compound_id}"
        
        # Get compound information
        compound_agent = CompoundAgent()
        compound_response = compound_agent.process_query(query)
        
        # Get safety information for associated trials
        trials = database.execute_query("SELECT trial_id FROM clinical_trials WHERE compound_id = ?", (compound_id,))
        
        safety_insights = []
        if trials:
            safety_agent = SafetyAgent()
            for trial in trials[:3]:  # Limit to first 3 trials
                safety_query = f"Safety analysis for trial {trial['trial_id']}"
                try:
                    safety_response = safety_agent.process_query(safety_query)
                    if safety_response:
                        safety_insights.append(safety_response.answer)
                except Exception as e:
                    logger.error(f"Error getting safety for trial {trial['trial_id']}: {e}")
        
        # Get research documents
        research_agent = ResearchAgent()
        research_response = research_agent.process_query(query)
        
        # Build comprehensive profile
        answer_parts = [
            f"**Comprehensive Compound Profile**",
            f"**Compound:** {compound_id}",
            compound_response.answer if compound_response else "No compound information available"
        ]
        
        if safety_insights:
            answer_parts.append("\n\n**Safety Profile:**")
            for insight in safety_insights:
                answer_parts.append(f"- {insight}")
        
        if research_response and research_response.answer:
            answer_parts.append("\n\n**Research Documentation:**")
            answer_parts.append(research_response.answer)
        
        answer = "\n".join(answer_parts)
        
        # Combine evidence
        all_evidence = []
        if compound_response:
            all_evidence.extend(compound_response.evidence)
        if research_response:
            all_evidence.extend(research_response.evidence)
        
        # Combine sources
        all_sources = []
        if compound_response:
            all_sources.extend(compound_response.sources)
        if research_response:
            all_sources.extend(research_response.sources)
        
        return QueryResponse(
            answer=answer,
            evidence=all_evidence,
            sources=all_sources,
            interpretation="Comprehensive compound profile synthesized from multiple data sources",
            uncertainty="Low",
            agent_used=self.name,
            processing_time_ms=500.0
        )
