// API Response Types
export interface QueryRequest {
  query: string;
  user_role?: string;
}

export interface Evidence {
  source: string;
  data: Record<string, any>;
  confidence: number;
  description: string;
}

export interface QueryResponse {
  answer: string;
  evidence: Evidence[];
  sources: string[];
  interpretation: string;
}

// Domain Types
export interface Compound {
  compound_id: string;
  compound_name: string;
  chemical_class: string;
  therapeutic_area: string;
  target_protein: string;
  mechanism_of_action: string;
  discovery_phase: string;
  molecular_weight_da: number;
  solubility_mg_ml: number;
  toxicity_score: number;
  lead_scientist: string;
  synthesis_date: string;
  created_at: string;
}

export interface ClinicalTrial {
  trial_id: string;
  compound_id: string;
  trial_phase: string;
  therapeutic_area: string;
  sponsor: string;
  start_date: string;
  planned_end_date: string;
  actual_end_date?: string;
  status: string;
  target_enrollment: number;
  actual_enrollment: number;
  primary_endpoint: string;
  enrollment_pct?: number;
}

export interface AdverseEvent {
  event_id: string;
  trial_id: string;
  site_id: string;
  patient_code: string;
  event_date: string;
  adverse_event_term: string;
  severity: string;
  seriousness: string;
  causality_assessment: string;
  outcome: string;
  reported_by: string;
}

export interface ResearchDocument {
  doc_id: string;
  compound_id?: string;
  trial_id?: string;
  doc_type: string;
  title: string;
  author: string;
  date: string;
  full_text: string;
  tags: string;
  relevance_score?: number;
  snippet?: string;
}

// UI State Types
export interface AppState {
  query: string;
  results: QueryResponse | null;
  loading: boolean;
  error: string | null;
}

export interface ExampleQuestion {
  id: string;
  question: string;
  category: string;
  icon: string;
}
