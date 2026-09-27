import React, { useState, useEffect } from 'react';
import QueryInterface from './components/QueryInterface';
import ResultsDisplay from './components/ResultsDisplay';
import AgentStatus from './components/AgentStatus';
import Header from './components/Header';
import { apiService } from './services/api';
import { QueryResponse, AppState } from './types';
import './App.css';

function App() {
  const [state, setState] = useState<AppState>({
    query: '',
    results: null,
    loading: false,
    error: null,
    agentStatus: 'Ready',
    processingTime: 0,
  });

  const [systemStatus, setSystemStatus] = useState<any>(null);

  useEffect(() => {
    // Check system health on mount
    apiService.healthCheck()
      .then(setSystemStatus)
      .catch(err => console.error('Health check failed:', err));
  }, []);

  const handleQuery = async (query: string) => {
    setState(prev => ({
      ...prev,
      query,
      loading: true,
      error: null,
      results: null,
      agentStatus: 'Processing...',
    }));

    try {
      const startTime = Date.now();
      const response = await apiService.processQuery(query);
      const processingTime = Date.now() - startTime;

      setState(prev => ({
        ...prev,
        results: response,
        loading: false,
        agentStatus: response.agent_used,
        processingTime,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'An error occurred',
        agentStatus: 'Error',
      }));
    }
  };

  return (
    <div className="app">
      <Header systemStatus={systemStatus} />
      
      <main className="main-content">
        <div className="container">
          <div className="welcome-section">
            <h1>PharmaSense</h1>
            <p>Pharmaceutical R&D Intelligence Assistant</p>
            <p className="subtitle">
              Ask questions about clinical trials, compounds, safety events, and research documents
            </p>
          </div>

          <AgentStatus 
            status={state.agentStatus}
            processingTime={state.processingTime}
            systemStatus={systemStatus}
          />

          <QueryInterface 
            onQuery={handleQuery}
            loading={state.loading}
            error={state.error}
          />

          {state.results && (
            <ResultsDisplay results={state.results} />
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
