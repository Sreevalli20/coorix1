import React from 'react';

interface HeaderProps {
  systemStatus: any;
}

const Header: React.FC<HeaderProps> = ({ systemStatus }) => {
  return (
    <header className="header">
      <div className="header-content">
        <div className="logo">
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="20" cy="20" r="18" stroke="#2563eb" strokeWidth="3"/>
            <path d="M12 20 L18 26 L28 14" stroke="#2563eb" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span className="logo-text">PharmaSense</span>
        </div>
        
        <div className="status-indicators">
          {systemStatus && (
            <>
              <div className={`status-indicator ${systemStatus.database_connected ? 'active' : 'inactive'}`}>
                <span className="status-dot"></span>
                Database
              </div>
              <div className={`status-indicator ${systemStatus.document_index_loaded ? 'active' : 'inactive'}`}>
                <span className="status-dot"></span>
                Document Index
              </div>
              <div className={`status-indicator ${systemStatus.status === 'healthy' ? 'active' : 'inactive'}`}>
                <span className="status-dot"></span>
                System
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
