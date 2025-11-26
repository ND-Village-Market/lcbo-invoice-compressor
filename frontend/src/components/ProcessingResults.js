import React from 'react';
import './ProcessingResults.css';

function ProcessingResults({ results, onDownload }) {
  const successCount = results.filter(r => r.status === 'success').length;
  const errorCount = results.filter(r => r.status === 'error').length;

  return (
    <div className="processing-results">
      <div className="results-summary">
        <h2>Processing Complete</h2>
        <p>
          {successCount} file{successCount !== 1 ? 's' : ''} processed successfully
          {errorCount > 0 && `, ${errorCount} error${errorCount !== 1 ? 's' : ''}`}
        </p>
      </div>

      <div className="results-list">
        {results.map((result, index) => (
          <div
            key={index}
            className={`result-item ${result.status === 'success' ? 'success' : 'error'}`}
          >
            <div className="result-header">
              <span className="result-status-icon">
                {result.status === 'success' ? '✓' : '✕'}
              </span>
              <div className="result-info">
                <h3>{result.original_file}</h3>
                {result.status === 'success' && (
                  <p className="result-details">
                    Order #{result.order_number} • {result.customer_name} • {result.item_count} items
                  </p>
                )}
                {result.status === 'error' && (
                  <p className="result-error">{result.error}</p>
                )}
              </div>
            </div>

            {result.status === 'success' && (
              <button
                className="download-btn"
                onClick={() => onDownload(result.output_file)}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                Download
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default ProcessingResults;
