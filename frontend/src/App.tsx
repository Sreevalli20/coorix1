import { useState, useEffect } from 'react';
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
  const [startupError, setStartupError] = useState<string | null>(null);

  useEffect(() => {
    console.log('App component mounted');
    console.log('API Base URL:', import.meta.env.VITE_API_URL || 'https://coorix1.onrender.com');
    
    // Test if the environment is working
    try {
      console.log('Environment check passed');
    } catch (err) {
      console.error('Startup error:', err);
      setStartupError('Application failed to initialize properly');
    }
  }, []);

  const handleQuery = async (query: string) => {
    console.log('Handle query called with:', query);
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await apiService.processQuery(query);
      console.log('Query response received:', response);
      setResults(response);
      setLoading(false);
    } catch (error) {
      console.error('Query error:', error);
      setLoading(false);
      setError(error instanceof Error ? error.message : 'An error occurred');
    }
  };

  return (
    <div className="app">
      <Header />
      
      <main className="main-content">
        <div className="container">
          {startupError && (
            <div className="error-message" style={{ backgroundColor: '#fee', color: '#c33', padding: '1rem', marginBottom: '1rem', borderRadius: '4px' }}>
              <strong>Startup Error:</strong> {startupError}
            </div>
          )}
          
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
