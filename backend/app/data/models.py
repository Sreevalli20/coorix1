from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


# Compound Models
class Compound(BaseModel):
    compound_id: str
    compound_name: str
    chemical_class: str
    therapeutic_area: str
    target_protein: str
    mechanism_of_action: str
    discovery_phase: str
    molecular_weight_da: float
    solubility_mg_ml: float
    toxicity_score: float
    lead_scientist: str
    synthesis_date: date
    created_at: date


class CompoundResponse(BaseModel):
    compound: Compound
    trials: List["ClinicalTrial"] = []
    lab_results: List["LabResult"] = []
    research_documents: List["ResearchDocument"] = []


# Clinical Trial Models
class ClinicalTrial(BaseModel):
    trial_id: str
    compound_id: str
    trial_phase: str
    therapeutic_area: str
    sponsor: str
    start_date: date
    planned_end_date: date
    actual_end_date: Optional[date] = None
    status: str
    target_enrollment: int
    actual_enrollment: int
    primary_endpoint: str

    @property
    def enrollment_percentage(self) -> float:
        if self.target_enrollment == 0:
            return 0.0
        return (self.actual_enrollment / self.target_enrollment) * 100


class TrialSite(BaseModel):
    site_id: str
    trial_id: str
    site_name: str
    country: str
    principal_investigator: str
    enrollment_count: int
    site_status: str


class TrialResponse(BaseModel):
    trial: ClinicalTrial
    compound: Optional[Compound] = None
    sites: List[TrialSite] = []
    adverse_events: List["AdverseEvent"] = []


# Lab Result Models
class LabResult(BaseModel):
    result_id: str
    compound_id: str
    experiment_type: str
    result_value: float
    unit: str
    result_date: date
    technician: str
    pass_fail: str


# Adverse Event Models
class AdverseEvent(BaseModel):
    event_id: str
    trial_id: str
    site_id: str
    patient_code: str
    event_date: date
    adverse_event_term: str
    severity: str
    seriousness: str
    causality_assessment: str
    outcome: str
    reported_by: str


class SafetyTriage(BaseModel):
    trial_id: str
    total_events: int
    serious_events: int
    severe_events: int
    related_events: int
    most_common_events: List[tuple]
    risk_level: str


# Research Document Models
class ResearchDocument(BaseModel):
    doc_id: str
    compound_id: Optional[str] = None
    trial_id: Optional[str] = None
    doc_type: str
    title: str
    author: str
    date: date
    full_text: str
    tags: str


class DocumentSearchResult(BaseModel):
    doc_id: str
    title: str
    relevance_score: float
    snippet: str
    full_document: ResearchDocument


# Query and Response Models
class QueryRequest(BaseModel):
    query: str
    user_role: Optional[str] = "user"


class Evidence(BaseModel):
    source: str
    data: dict
    confidence: float
    description: str


class QueryResponse(BaseModel):
    answer: str
    evidence: List[Evidence] = []
    sources: List[str] = []
    interpretation: str
    uncertainty: str
    agent_used: str
    processing_time_ms: float


# Agent Status Models
class AgentStatus(BaseModel):
    agent_name: str
    status: str
    last_activity: Optional[datetime] = None
    queries_processed: int = 0


class SystemStatus(BaseModel):
    status: str
    database_connected: bool
    document_index_loaded: bool
    agents_active: List[str]
    memory_usage_mb: float
