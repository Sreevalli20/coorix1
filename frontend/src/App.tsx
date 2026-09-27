import { useState } from 'react';
import QueryInterface from './components/QueryInterface';
import ResultsDisplay from './components/ResultsDisplay';
import Header from './components/Header';
import { apiService } from './services/api';
import { QueryResponse } from './types';
import './App.css';

function App() {
  const [results, setResults] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleQuery = async (query: string) => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await apiService.processQuery(query);
      setResults(response);
      setLoading(false);
    } catch (error) {
      setLoading(false);
      setError(error instanceof Error ? error.message : 'An error occurred');
    }
  };

  return (
    <div className="app">
      <Header />
      
      <main className="main-content">
        <div className="container">
          <div className="welcome-section">
            <h1>PharmaSense</h1>
            <p>Pharmaceutical R&D Intelligence Assistant</p>
            <p className="subtitle">
              Ask questions about clinical trials, compounds, safety events, and research documents
            </p>
          </div>

          <QueryInterface 
            onQuery={handleQuery}
            loading={loading}
            error={error}
          />

          {results && (
            <ResultsDisplay results={results} />
          )}
        </div>
      </main>

      <footer className="footer">
        <p>PharmaSense v1.0.0 | Pharmaceutical R&D Intelligence</p>
      </footer>
    </div>
  );
}

export default App;
