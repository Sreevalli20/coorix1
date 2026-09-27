import React from 'react';

interface AgentStatusProps {
  status: string;
  processingTime: number;
  systemStatus: any;
}

const AgentStatus: React.FC<AgentStatusProps> = ({ status, processingTime, systemStatus }) => {
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'ready':
        return 'green';
      case 'processing...':
        return 'blue';
      case 'error':
        return 'red';
      default:
        return 'green';
    }
  };

  return (
    <div className="agent-status">
      <div className="status-card">
        <div className="status-header">
          <h3>System Status</h3>
          <span className={`status-indicator ${getStatusColor(status)}`}>
            {status}
          </span>
        </div>
        
        {systemStatus && (
          <div className="status-details">
            <div className="status-item">
              <span className="status-label">Database:</span>
              <span className={systemStatus.database_connected ? 'status-active' : 'status-inactive'}>
                {systemStatus.database_connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Document Index:</span>
              <span className={systemStatus.document_index_loaded ? 'status-active' : 'status-inactive'}>
                {systemStatus.document_index_loaded ? 'Loaded' : 'Not Loaded'}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Memory Usage:</span>
              <span className="status-value">
                {systemStatus.memory_usage_mb?.toFixed(1)} MB
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Active Agents:</span>
              <span className="status-value">
                {systemStatus.agents_active?.length || 0}
              </span>
            </div>
          </div>
        )}

        {processingTime > 0 && (
          <div className="processing-time">
            Last query processed in {processingTime.toFixed(0)}ms
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentStatus;
