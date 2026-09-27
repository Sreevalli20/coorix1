import React, { useState } from 'react';
import { ExampleQuestion } from '../types';

interface QueryInterfaceProps {
  onQuery: (query: string) => void;
  loading: boolean;
  error: string | null;
}

const exampleQuestions: ExampleQuestion[] = [
  {
    id: '1',
    question: 'Which Phase II oncology trials are below 60% enrollment right now?',
    category: 'Trial Intelligence',
    icon: '📊'
  },
  {
    id: '2',
    question: 'What has our internal research said about JAK2 inhibitors and cardiotoxicity?',
    category: 'Research Intelligence',
    icon: '📚'
  },
  {
    id: '3',
    question: 'A site just reported a serious adverse event for Trial TRL-0032 — triage it.',
    category: 'Safety Intelligence',
    icon: '⚠️'
  },
  {
    id: '4',
    question: 'Tell me about compound DKU-1001.',
    category: 'Compound Intelligence',
    icon: '💊'
  }
];

const QueryInterface: React.FC<QueryInterfaceProps> = ({ onQuery, loading, error }) => {
  const [inputQuery, setInputQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputQuery.trim()) {
      onQuery(inputQuery.trim());
    }
  };

  const handleExampleClick = (question: string) => {
    setInputQuery(question);
    onQuery(question);
  };

  return (
    <div className="query-interface">
      <form onSubmit={handleSubmit} className="query-form">
        <div className="input-group">
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask about clinical trials, compounds, safety events, or research documents..."
            className="query-input"
            disabled={loading}
          />
          <button 
            type="submit" 
            className="submit-button"
            disabled={loading || !inputQuery.trim()}
          >
            {loading ? (
              <span className="loading-spinner"></span>
            ) : (
              'Analyze'
            )}
          </button>
        </div>
      </form>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      <div className="example-questions">
        <h3>Example Questions</h3>
        <div className="questions-grid">
          {exampleQuestions.map((example) => (
            <button
              key={example.id}
              onClick={() => handleExampleClick(example.question)}
              className="example-button"
              disabled={loading}
            >
              <span className="example-icon">{example.icon}</span>
              <div className="example-content">
                <div className="example-category">{example.category}</div>
                <div className="example-text">{example.question}</div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default QueryInterface;
