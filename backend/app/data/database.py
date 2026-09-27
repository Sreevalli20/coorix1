import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = "pharmasense.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """Create database connection"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        logger.info(f"Connected to database: {self.db_path}")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")

    def load_csv_data(self, data_dir: str = None):
        """Load all CSV files into database"""
        if data_dir is None:
            # Check for environment variable first
            data_dir = os.environ.get("DATA_DIR")
            
            if data_dir is None:
                # Try relative path first, then absolute path
                data_dir = "./data"
                if not Path(data_dir).exists():
                    data_dir = "../data"
                    if not Path(data_dir).exists():
                        data_dir = "data"
        
        data_path = Path(data_dir)
        
        if not data_path.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")

        # Load each CSV file
        csv_files = {
            "compounds": "compounds.csv",
            "clinical_trials": "clinical_trials.csv",
            "trial_sites": "trial_sites.csv",
            "lab_results": "lab_results.csv",
            "adverse_events": "adverse_events.csv",
            "research_documents": "research_documents.csv",
            "agent_interaction_logs": "agent_interaction_logs.csv"
        }

        for table_name, csv_file in csv_files.items():
            csv_path = data_path / csv_file
            if csv_path.exists():
                self._load_csv_to_table(csv_path, table_name)
            else:
                logger.warning(f"CSV file not found: {csv_path}")

        # Create indexes for common queries
        self._create_indexes()
        logger.info("Data loading complete")

    def _load_csv_to_table(self, csv_path: Path, table_name: str):
        """Load a single CSV file into a table"""
        try:
            df = pd.read_csv(csv_path)
            
            # Clean column names (remove spaces, lowercase)
            df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
            
            # Create table
            df.to_sql(table_name, self.conn, if_exists="replace", index=False)
            logger.info(f"Loaded {len(df)} rows into {table_name}")
        except Exception as e:
            logger.error(f"Error loading {csv_path}: {e}")
            raise

    def _create_indexes(self):
        """Create indexes for common query patterns"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_compounds_id ON compounds(compound_id)",
            "CREATE INDEX IF NOT EXISTS idx_compounds_target ON compounds(target_protein)",
            "CREATE INDEX IF NOT EXISTS idx_compounds_area ON compounds(therapeutic_area)",
            "CREATE INDEX IF NOT EXISTS idx_trials_id ON clinical_trials(trial_id)",
            "CREATE INDEX IF NOT EXISTS idx_trials_compound ON clinical_trials(compound_id)",
            "CREATE INDEX IF NOT EXISTS idx_trials_phase ON clinical_trials(trial_phase)",
            "CREATE INDEX IF NOT EXISTS idx_trials_area ON clinical_trials(therapeutic_area)",
            "CREATE INDEX IF NOT EXISTS idx_sites_trial ON trial_sites(trial_id)",
            "CREATE INDEX IF NOT EXISTS idx_adverse_trial ON adverse_events(trial_id)",
            "CREATE INDEX IF NOT EXISTS idx_adverse_severity ON adverse_events(severity)",
            "CREATE INDEX IF NOT EXISTS idx_lab_compound ON lab_results(compound_id)",
            "CREATE INDEX IF NOT EXISTS idx_docs_compound ON research_documents(compound_id)",
            "CREATE INDEX IF NOT EXISTS idx_docs_trial ON research_documents(trial_id)",
        ]

        for index_sql in indexes:
            try:
                self.conn.execute(index_sql)
            except Exception as e:
                logger.warning(f"Error creating index: {e}")

    def execute_query(self, query: str, params: tuple = ()) -> list:
        """Execute a SELECT query and return results as list of dicts"""
        try:
            cursor = self.conn.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise

    def get_compound(self, compound_id: str) -> Optional[dict]:
        """Get a single compound by ID"""
        query = "SELECT * FROM compounds WHERE compound_id = ?"
        results = self.execute_query(query, (compound_id,))
        return results[0] if results else None

    def get_trial(self, trial_id: str) -> Optional[dict]:
        """Get a single trial by ID"""
        query = "SELECT * FROM clinical_trials WHERE trial_id = ?"
        results = self.execute_query(query, (trial_id,))
        return results[0] if results else None

    def get_trials_by_phase_and_area(self, phase: str, therapeutic_area: str) -> list:
        """Get trials filtered by phase and therapeutic area"""
        query = """
            SELECT * FROM clinical_trials 
            WHERE trial_phase = ? AND therapeutic_area = ?
        """
        return self.execute_query(query, (phase, therapeutic_area))

    def get_trials_below_enrollment_threshold(self, threshold: float = 60.0) -> list:
        """Get trials with enrollment below threshold percentage"""
        query = """
            SELECT *, 
                   (CAST(actual_enrollment AS FLOAT) / target_enrollment * 100) as enrollment_pct
            FROM clinical_trials 
            WHERE target_enrollment > 0
              AND (CAST(actual_enrollment AS FLOAT) / target_enrollment * 100) < ?
        """
        return self.execute_query(query, (threshold,))

    def get_adverse_events_by_trial(self, trial_id: str) -> list:
        """Get adverse events for a specific trial"""
        query = "SELECT * FROM adverse_events WHERE trial_id = ?"
        return self.execute_query(query, (trial_id,))

    def get_serious_adverse_events(self, trial_id: str = None) -> list:
        """Get serious adverse events, optionally filtered by trial"""
        if trial_id:
            query = """
                SELECT * FROM adverse_events 
                WHERE seriousness = 'Serious' AND trial_id = ?
            """
            return self.execute_query(query, (trial_id,))
        else:
            query = "SELECT * FROM adverse_events WHERE seriousness = 'Serious'"
            return self.execute_query(query)

    def get_lab_results_by_compound(self, compound_id: str) -> list:
        """Get lab results for a specific compound"""
        query = "SELECT * FROM lab_results WHERE compound_id = ?"
        return self.execute_query(query, (compound_id,))

    def get_compounds_by_target(self, target_protein: str) -> list:
        """Get compounds targeting a specific protein"""
        query = "SELECT * FROM compounds WHERE target_protein = ?"
        return self.execute_query(query, (target_protein,))

    def get_trial_sites(self, trial_id: str) -> list:
        """Get sites for a specific trial"""
        query = "SELECT * FROM trial_sites WHERE trial_id = ?"
        return self.execute_query(query, (trial_id,))

    def get_all_research_documents(self) -> list:
        """Get all research documents"""
        query = "SELECT * FROM research_documents"
        return self.execute_query(query)

    def get_documents_by_compound(self, compound_id: str) -> list:
        """Get research documents for a specific compound"""
        query = "SELECT * FROM research_documents WHERE compound_id = ?"
        return self.execute_query(query, (compound_id,))

    def get_documents_by_trial(self, trial_id: str) -> list:
        """Get research documents for a specific trial"""
        query = "SELECT * FROM research_documents WHERE trial_id = ?"
        return self.execute_query(query, (trial_id,))

    def search_adverse_events_by_term(self, term: str) -> list:
        """Search adverse events by term"""
        query = """
            SELECT * FROM adverse_events 
            WHERE adverse_event_term LIKE ?
        """
        return self.execute_query(query, (f"%{term}%",))

    def get_safety_summary_by_trial(self, trial_id: str) -> dict:
        """Get safety summary for a trial"""
        events = self.get_adverse_events_by_trial(trial_id)
        
        if not events:
            return {
                "total_events": 0,
                "serious_events": 0,
                "severe_events": 0,
                "related_events": 0,
                "most_common_events": [],
                "risk_level": "Low"
            }

        serious_count = sum(1 for e in events if e["seriousness"] == "Serious")
        severe_count = sum(1 for e in events if e["severity"] == "Severe")
        related_count = sum(1 for e in events if e["causality_assessment"] in ["Related", "Possibly Related"])

        # Count most common events
        event_terms = [e["adverse_event_term"] for e in events]
        from collections import Counter
        common_events = Counter(event_terms).most_common(5)

        # Determine risk level
        if serious_count > 0 or severe_count > 0:
            risk_level = "High"
        elif related_count > len(events) * 0.5:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        return {
            "total_events": len(events),
            "serious_events": serious_count,
            "severe_events": severe_count,
            "related_events": related_count,
            "most_common_events": common_events,
            "risk_level": risk_level
        }


# Global database instance
db = Database()
