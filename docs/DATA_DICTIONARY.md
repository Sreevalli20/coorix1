# PharmaSense Data Dictionary

## Overview
This document describes the schema, relationships, and characteristics of the PharmaSense pharmaceutical R&D dataset.

## Dataset Summary

| Dataset | Rows | Columns | Description |
|---------|------|----------|-------------|
| compounds | 100 | 13 | Compound library with chemical and biological properties |
| clinical_trials | 110 | 12 | Clinical trial metadata and enrollment data |
| trial_sites | 223 | 7 | Site-level trial information and enrollment |
| lab_results | 220 | 8 | Laboratory experiment results for compounds |
| adverse_events | 176 | 11 | Safety event reports from clinical trials |
| research_documents | 46 | 9 | Internal research documents and literature reviews |
| agent_interaction_logs | 78 | 11 | Historical agent query logs |

## Schema Details

### 1. compounds.csv
**Primary Key:** compound_id

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| compound_id | string | Unique compound identifier | Format: CMP-XXXX |
| compound_name | string | Compound name | Format: XXN-XXXX |
| chemical_class | string | Chemical classification | Peptide, PROTAC, Small Molecule, Kinase Inhibitor, Monoclonal Antibody, Antisense Oligonucleotide, siRNA Therapeutic |
| therapeutic_area | string | Target therapeutic area | Neurology, Metabolic Disease, Oncology, Infectious Disease, Respiratory, Cardiology, Immunology |
| target_protein | string | Primary target protein | JAK2, TNF-alpha, BTK, BCL-2, VEGFR2, PCSK9, ALK, IL-6R, HER2, CDK4/6, SGLT2, EGFR, NLRP3, PD-1, GLP-1R, KRAS G12C, mTOR, BRAF |
| mechanism_of_action | string | Detailed mechanism description | Text description of biological mechanism |
| discovery_phase | string | Development phase | Discovery, Preclinical, Phase I, Phase II, Phase III, Phase IV, Approved, Discontinued |
| molecular_weight_da | float | Molecular weight in Daltons | Range: 191.68 - 1449.64 |
| solubility_mg_ml | float | Solubility in mg/mL | Range: 0.0 - 14.237 |
| toxicity_score | float | Toxicity score | Range: 0.037 - 0.618 |
| lead_scientist | string | Lead scientist name | |
| synthesis_date | date | Synthesis date | |
| created_at | date | Record creation date | |

**Relationships:**
- One-to-many with clinical_trials (via compound_id)
- One-to-many with lab_results (via compound_id)
- One-to-many with research_documents (via compound_id)

### 2. clinical_trials.csv
**Primary Key:** trial_id
**Foreign Key:** compound_id → compounds.compound_id

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| trial_id | string | Unique trial identifier | Format: TRL-XXXX |
| compound_id | string | Associated compound | FK to compounds |
| trial_phase | string | Clinical trial phase | Phase I, Phase II, Phase III, Phase IV |
| therapeutic_area | string | Therapeutic area | Matches compound therapeutic_area |
| sponsor | string | Trial sponsor | PharmaSense Global R&D, PharmaSense Oncology Division, etc. |
| start_date | date | Trial start date | |
| planned_end_date | date | Planned end date | |
| actual_end_date | date | Actual end date | NULL if ongoing |
| status | string | Trial status | Completed, Recruiting, "Active, not recruiting", Suspended, Terminated |
| target_enrollment | int | Target enrollment count | Range: 32 - 596 |
| actual_enrollment | int | Actual enrollment count | Range: 25 - 529 |
| primary_endpoint | string | Primary endpoint | Reduction in LDL Cholesterol, Change in HbA1c from Baseline, etc. |

**Relationships:**
- Many-to-one with compounds (via compound_id)
- One-to-many with trial_sites (via trial_id)
- One-to-many with adverse_events (via trial_id)
- One-to-many with research_documents (via trial_id)

### 3. trial_sites.csv
**Primary Key:** site_id
**Foreign Key:** trial_id → clinical_trials.trial_id

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| site_id | string | Unique site identifier | Format: SITE-XXXXX |
| trial_id | string | Associated trial | FK to clinical_trials |
| site_name | string | Site name | |
| country | string | Country | United States, United Kingdom, Japan, Brazil, Germany, etc. |
| principal_investigator | string | Principal investigator | |
| enrollment_count | int | Enrollment count at site | Range: 5 - 505 |
| site_status | string | Site status | Active, Closed, Pending Activation |

**Relationships:**
- Many-to-one with clinical_trials (via trial_id)

### 4. lab_results.csv
**Primary Key:** result_id
**Foreign Key:** compound_id → compounds.compound_id

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| result_id | string | Unique result identifier | Format: LAB-XXXXX |
| compound_id | string | Associated compound | FK to compounds |
| experiment_type | string | Experiment type | Binding Affinity (SPR), hERG Cardiotoxicity Screen, Solubility Assay, Selectivity Panel, Enzymatic Inhibition Assay, Metabolic Stability (Microsomal), Pharmacokinetic (PK) Study, Cell Viability Assay |
| result_value | float | Result value | Numeric measurement |
| unit | string | Unit of measurement | nM (Kd), % inhibition at 10uM, mg/mL, % selectivity, nM (IC50), min (t1/2), hours (t1/2), % viability |
| result_date | date | Result date | |
| technician | string | Technician name | |
| pass_fail | string | Pass/Fail status | Pass, Fail |

**Relationships:**
- Many-to-one with compounds (via compound_id)

### 5. adverse_events.csv
**Primary Key:** event_id
**Foreign Keys:** trial_id → clinical_trials.trial_id, site_id → trial_sites.site_id

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| event_id | string | Unique event identifier | Format: AE-XXXXX |
| trial_id | string | Associated trial | FK to clinical_trials |
| site_id | string | Associated site | FK to trial_sites |
| patient_code | string | Patient identifier | Format: PT-XXXXX |
| event_date | date | Event date | |
| adverse_event_term | string | Adverse event term | Cough, Insomnia, Headache, Diarrhea, Dizziness, Rash, Anemia, QT Prolongation, Fatigue, etc. |
| severity | string | Severity level | Mild, Moderate, Severe |
| seriousness | string | Seriousness | Serious, Non-serious |
| causality_assessment | string | Causality assessment | Related, Possibly Related, Unlikely Related, Not Related |
| outcome | string | Event outcome | Resolving, Resolved, Ongoing, Fatal, Resolved with Sequelae |
| reported_by | string | Reporter name | |

**Relationships:**
- Many-to-one with clinical_trials (via trial_id)
- Many-to-one with trial_sites (via site_id)

### 6. research_documents.csv
**Primary Key:** doc_id
**Foreign Keys:** compound_id → compounds.compound_id, trial_id → clinical_trials.trial_id

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| doc_id | string | Unique document identifier | Format: DOC-XXXXX |
| compound_id | string | Associated compound (optional) | FK to compounds, can be NULL |
| trial_id | string | Associated trial (optional) | FK to clinical_trials, can be NULL |
| doc_type | string | Document type | Lab Notebook Entry, Regulatory Briefing, Literature Review, Internal Memo, SOP Deviation Report, Conference Abstract |
| title | string | Document title | |
| author | string | Author name | |
| date | date | Document date | |
| full_text | string | Full document text | Unstructured text content |
| tags | string | Comma-separated tags | Keywords for categorization |

**Relationships:**
- Many-to-one with compounds (via compound_id, optional)
- Many-to-one with clinical_trials (via trial_id, optional)

### 7. agent_interaction_logs.csv
**Primary Key:** log_id

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| log_id | string | Unique log identifier | Format: LOG-XXXXX |
| session_id | string | Session identifier | Format: SESS-XXXX |
| timestamp | datetime | Query timestamp | |
| user_role | string | User role | Medical Science Liaison, Data Scientist, Clinical Operations Manager, Research Scientist, Biostatistician, Regulatory Affairs Specialist |
| user_query | string | User query text | Natural language query |
| agent_invoked | string | Agent invoked | Router / Planner Agent, Trial Data Analyst Agent, Compound Similarity Agent, Adverse Event Triage Agent, Literature & Document Research Agent, Report Writer Agent |
| tool_called | string | Tool called | vector_search_tool, ae_severity_classifier_tool, citation_formatter_tool, statistics_tool, compound_similarity_tool, escalation_notifier_tool, sql_query_tool |
| response_summary | string | Response summary | Brief summary of agent response |
| latency_ms | int | Latency in milliseconds | Range: 495 - 3211 |
| tokens_used | int | Tokens used | Range: 553 - 7790 |
| feedback_rating | int | User feedback rating | Scale: 1-5 |
| escalated_flag | boolean | Escalation flag | Whether query was escalated |

**Relationships:**
- No direct foreign key relationships (historical log data)

## Entity Relationship Diagram

```
compounds (1) ----< (N) clinical_trials (1) ----< (N) trial_sites
    |                     |                        |
    |                     |                        |
    |                     | (1) ----< (N) adverse_events
    |                     |
    |                     | (1) ----< (N) research_documents
    |
    | (1) ----< (N) lab_results
    |
    | (1) ----< (N) research_documents

agent_interaction_logs (standalone historical data)
```

## Key Insights

### Data Quality
- **Missing Values:** Some clinical_trials have NULL actual_end_date (ongoing trials)
- **Compound Coverage:** 100 compounds across 7 therapeutic areas
- **Trial Coverage:** 110 trials with varying enrollment rates
- **Geographic Distribution:** Sites across 8+ countries
- **Document Corpus:** 46 research documents with full text for retrieval

### Important Fields for Analysis
- **Enrollment Analysis:** clinical_trials.target_enrollment vs actual_enrollment
- **Safety Monitoring:** adverse_events.severity, seriousness, causality_assessment
- **Compound Intelligence:** compounds.target_protein, mechanism_of_action, toxicity_score
- **Research Retrieval:** research_documents.full_text (unstructured corpus)
- **Lab Performance:** lab_results.pass_fail, experiment_type
- **Site Performance:** trial_sites.enrollment_count, site_status

### Demo Workflow Data Coverage
1. **Phase II oncology trials below 60% enrollment:** Available in clinical_trials
2. **JAK2 inhibitors and cardiotoxicity research:** Available in research_documents (JAK2 compounds, cardiotoxicity mentions)
3. **Adverse event triage for TRL-0032:** Available in adverse_events (filter by trial_id)
4. **Compound DKU-1042 full picture:** Available across compounds, clinical_trials, lab_results, adverse_events, research_documents

## Usage Notes
- All compound IDs follow format CMP-XXXX
- All trial IDs follow format TRL-XXXX
- All site IDs follow format SITE-XXXXX
- All lab result IDs follow format LAB-XXXXX
- All adverse event IDs follow format AE-XXXXX
- All document IDs follow format DOC-XXXXX
- Dates are in YYYY-MM-DD format
- Research documents contain unstructured text suitable for semantic search
- Agent interaction logs provide historical query patterns for training/reference
