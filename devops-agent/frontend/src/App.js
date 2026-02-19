import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [repoUrl, setRepoUrl] = useState('');
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [polling, setPolling] = useState(false);

  useEffect(() => {
    if (jobId && polling) {
      const interval = setInterval(() => {
        checkStatus();
      }, 2000); // Poll every 2 seconds

      return () => clearInterval(interval);
    }
  }, [jobId, polling]);

  const checkStatus = async () => {
    if (!jobId) return;
    
    try {
      const response = await axios.get(`/api/status/${jobId}`);
      const jobStatus = response.data;
      setStatus(jobStatus);
      
      if (jobStatus.status === 'completed') {
        setPolling(false);
        setResults(jobStatus.results);
      } else if (jobStatus.status === 'failed') {
        setPolling(false);
        setError(jobStatus.error || 'Job failed');
      }
    } catch (err) {
      console.error('Error checking status:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setResults(null);
    setStatus(null);
    setPolling(true);

    try {
      const response = await axios.post('/api/analyze', {
        repo_url: repoUrl
      });
      
      setJobId(response.data.job_id);
      setStatus(response.data);
      
      if (response.data.results) {
        setPolling(false);
        setResults(response.data.results);
      }
    } catch (err) {
      setPolling(false);
      console.error('API Error:', err);
      console.error('Error Response:', err.response?.data);
      
      let errorMessage = 'Failed to start analysis';
      
      if (err.response?.data?.error) {
        errorMessage = err.response.data.error;
      } else if (err.response?.data?.message) {
        errorMessage = err.response.data.message;
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      // Add helpful context
      if (err.response?.status === 500) {
        errorMessage += '\n\nCheck the backend terminal for detailed error logs.';
        errorMessage += '\nCommon issues:';
        errorMessage += '\n- Git not installed or not in PATH';
        errorMessage += '\n- Repository URL invalid or inaccessible';
        errorMessage += '\n- Network connectivity issues';
      }
      
      setError(errorMessage);
    }
  };

  return (
    <div className="App">
      <div className="container">
        <header className="header">
          <h1>🤖 Autonomous DevOps Agent</h1>
          <p>CI/CD Healing & Test Automation Dashboard</p>
        </header>

        <div className="main-content">
          <div className="input-section">
            <form onSubmit={handleSubmit} className="repo-form">
              <div className="input-group">
                <label htmlFor="repo-url">GitHub Repository URL</label>
                <input
                  id="repo-url"
                  type="text"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/username/repo.git"
                  disabled={polling}
                  required
                />
              </div>
              <button 
                type="submit" 
                disabled={polling || !repoUrl}
                className="submit-btn"
              >
                {polling ? 'Analyzing...' : 'Analyze Repository'}
              </button>
            </form>
          </div>

          {error && (
            <div className="error-box">
              <h3>❌ Error</h3>
              <p style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{error}</p>
            </div>
          )}

          {status && status.status && status.status !== 'completed' && (
            <div className="status-box">
              <h3>Status: {(status.status || 'processing').replace(/_/g, ' ').toUpperCase()}</h3>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${status.progress || 0}%` }}
                ></div>
              </div>
              <p>{status.progress || 0}% Complete</p>
            </div>
          )}

          {results && (
            <div className="results-section">
              <h2>📊 Analysis Results</h2>
              
              <div className="summary-cards">
                <div className="card">
                  <h3>Repository</h3>
                  <p>{results.repository || 'N/A'}</p>
                </div>
                <div className="card">
                  <h3>Branch</h3>
                  <p>{results.branch || 'N/A'}</p>
                </div>
                {results.team_leader && (
                  <div className="card">
                    <h3>Team Leader</h3>
                    <p>{results.team_leader}</p>
                  </div>
                )}
                <div className="card">
                  <h3>Status</h3>
                  <p className={results.final_status === 'PASSED' ? 'status-passed' : 'status-failed'}>
                    {results.final_status || 'UNKNOWN'}
                  </p>
                </div>
                <div className="card">
                  <h3>Failures</h3>
                  <p>{results.total_failures || 0}</p>
                </div>
                <div className="card">
                  <h3>Fixes</h3>
                  <p>{results.total_fixes || 0}</p>
                </div>
                <div className="card">
                  <h3>Iterations</h3>
                  <p>{results.iterations || 0}</p>
                </div>
              </div>

              {results.test_files && results.test_files.length > 0 && (
                <div className="test-files">
                  <h3>Test Files Discovered</h3>
                  <ul>
                    {results.test_files.map((file, idx) => (
                      <li key={idx}>{file}</li>
                    ))}
                  </ul>
                </div>
              )}

              {results.fixes && results.fixes.length > 0 && (
                <div className="fixes-section">
                  <h3>🔧 Errors Detected & Fixes Applied</h3>
                  <div className="fixes-table-container">
                    <table className="fixes-table">
                      <thead>
                        <tr>
                          <th>File</th>
                          <th>Bug Type</th>
                          <th>Line</th>
                          <th>Commit Message</th>
                          <th>AI Providers</th>
                          <th>Status</th>
                          <th>Debug</th>
                        </tr>
                      </thead>
                      <tbody>
                        {results.fixes.map((fix, idx) => (
                          <tr key={idx}>
                            <td className="file-cell">{fix.file || 'unknown'}</td>
                            <td>
                              <span className={`bug-type ${(fix.bug_type || 'LOGIC').toLowerCase()}`}>
                                {fix.bug_type || 'LOGIC'}
                              </span>
                            </td>
                            <td>{fix.line || '-'}</td>
                            <td className="commit-cell">{fix.commit_message || fix.fix_description || '-'}</td>
                            <td>{fix.ai_provider || 'AI/LLM'}</td>
                            <td>
                              <span className={`fix-status ${(fix.status || 'pending').toLowerCase()}`}>
                                {fix.status || 'Pending'}
                              </span>
                            </td>
                            <td className="debug-cell" title={fix.debug || ''}>
                              {fix.debug ? (fix.debug.length > 50 ? fix.debug.substring(0, 50) + '...' : fix.debug) : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {results.test_output && (
                <div className="test-output">
                  <h3>Test Output</h3>
                  <pre>{results.test_output}</pre>
                </div>
              )}

              <div className="download-section">
                <button 
                  onClick={() => {
                    const dataStr = JSON.stringify(results, null, 2);
                    const dataBlob = new Blob([dataStr], { type: 'application/json' });
                    const url = URL.createObjectURL(dataBlob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = 'results.json';
                    link.click();
                  }}
                  className="download-btn"
                >
                  Download results.json
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
