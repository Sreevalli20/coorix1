import React from 'react';
import { QueryResponse } from '../types';

interface ResultsDisplayProps {
  results: QueryResponse;
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ results }) => {
  const formatMarkdown = (text: string) => {
    // Simple markdown parser for bold text
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  };

  const renderAnswer = (answer: string) => {
    const paragraphs = answer.split('\n\n');
    return paragraphs.map((paragraph, index) => {
      if (paragraph.startsWith('- ')) {
        // Handle bullet points
        const items = paragraph.split('\n').filter(item => item.trim());
        return (
          <ul key={index} className="answer-list">
            {items.map((item, itemIndex) => (
              <li key={itemIndex} dangerouslySetInnerHTML={{ __html: formatMarkdown(item.replace(/^-\s*/, '')) }} />
            ))}
          </ul>
        );
      } else if (paragraph.startsWith('**') && paragraph.includes(':')) {
        // Handle headers like "**Section:** content"
        const parts = paragraph.split(':');
        if (parts.length >= 2) {
          return (
            <div key={index} className="answer-section-block">
              <h4 dangerouslySetInnerHTML={{ __html: formatMarkdown(parts[0] + ':') }} />
              <p dangerouslySetInnerHTML={{ __html: formatMarkdown(parts.slice(1).join(':')) }} />
            </div>
          );
        }
      }
      return (
        <p key={index} dangerouslySetInnerHTML={{ __html: formatMarkdown(paragraph) }} />
      );
    });
  };

  const isEmptyResult = results.evidence.length === 0 && 
                       (results.answer.includes("couldn't find") || 
                        results.answer.includes("not found"));

  return (
    <div className="results-display">
      <div className="answer-section">
        <h2>Answer</h2>
        <div className="answer-content">
          {renderAnswer(results.answer)}
        </div>
      </div>

      {isEmptyResult && (
        <div className="suggestions-section">
          <h3>What you can try</h3>
          <ul className="suggestions-list">
            <li>Try another compound identifier or ask about a specific trial</li>
            <li>Ask about safety events, laboratory results, or research topics</li>
            <li>Use the example questions below for guidance</li>
          </ul>
        </div>
      )}

      {results.interpretation && (
        <div className="interpretation-section">
          <h3>Key Findings</h3>
          <p>{results.interpretation}</p>
        </div>
      )}

      {results.evidence.length > 0 && (
        <div className="evidence-section">
          <h3>Evidence</h3>
          <div className="evidence-list">
            {results.evidence.map((evidence, index) => (
              <div key={index} className="evidence-item">
                <div className="evidence-header">
                  <span className="evidence-source">{evidence.source}</span>
                </div>
                <p className="evidence-description">{evidence.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultsDisplay;
