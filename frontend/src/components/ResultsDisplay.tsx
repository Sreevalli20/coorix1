import React from 'react';
import { QueryResponse } from '../types';

interface ResultsDisplayProps {
  results: QueryResponse;
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ results }) => {
  const getUncertaintyColor = (uncertainty: string) => {
    switch (uncertainty.toLowerCase()) {
      case 'low':
        return 'green';
      case 'medium':
        return 'yellow';
      case 'high':
        return 'red';
      default:
        return 'gray';
    }
  };

  return (
    <div className="results-display">
      <div className="results-header">
        <h2>Analysis Results</h2>
        <div className="meta-info">
          <span className="agent-badge">
            Agent: {results.agent_used}
          </span>
          <span className="time-badge">
            {results.processing_time_ms.toFixed(0)}ms
          </span>
          <span className={`uncertainty-badge ${getUncertaintyColor(results.uncertainty)}`}>
            Uncertainty: {results.uncertainty}
          </span>
        </div>
      </div>

      <div className="answer-section">
        <h3>Answer</h3>
        <div className="answer-content">
          {results.answer.split('\n').map((paragraph, index) => (
            <p key={index}>{paragraph}</p>
          ))}
        </div>
      </div>

      {results.interpretation && (
        <div className="interpretation-section">
          <h3>Interpretation</h3>
          <p>{results.interpretation}</p>
        </div>
      )}

      {results.evidence.length > 0 && (
        <div className="evidence-section">
          <h3>Evidence & Sources</h3>
          <div className="evidence-list">
            {results.evidence.map((evidence, index) => (
              <div key={index} className="evidence-item">
                <div className="evidence-header">
                  <span className="evidence-source">{evidence.source}</span>
                  <span className="evidence-confidence">
                    Confidence: {(evidence.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="evidence-description">{evidence.description}</p>
                {Object.keys(evidence.data).length > 0 && (
                  <details className="evidence-details">
                    <summary>View Data</summary>
                    <pre className="evidence-data">
                      {JSON.stringify(evidence.data, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {results.sources.length > 0 && (
        <div className="sources-section">
          <h3>Data Sources</h3>
          <div className="sources-list">
            {results.sources.slice(0, 10).map((source, index) => (
              <span key={index} className="source-tag">
                {source}
              </span>
            ))}
            {results.sources.length > 10 && (
              <span className="source-tag">
                +{results.sources.length - 10} more
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultsDisplay;
