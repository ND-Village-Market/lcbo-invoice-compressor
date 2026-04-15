import React from 'react';
import './ItemCostResults.css';

function ItemCostResults({ result, onDownload }) {
  const results = Array.isArray(result.processing_results)
    ? result.processing_results
    : [result];

  const successLikeResults = results.filter(
    (entry) => entry.status === 'success' || entry.status === 'empty'
  );
  const totalItemCount = successLikeResults.reduce(
    (sum, entry) => sum + (entry.item_count || 0),
    0
  );
  const sourceFiles = results.length;

  return (
    <div className="item-cost-results">
      <div className="item-cost-results-summary">
        <h2>Item Cost CSV Output Ready</h2>
        <p>
          {`Processed ${sourceFiles} Quick Order file${sourceFiles === 1 ? '' : 's'} with ${totalItemCount} total matched item cost${totalItemCount === 1 ? '' : 's'}`}
        </p>
      </div>

      <div className="item-cost-results-list">
        {results.map((entry, index) => (
          <div key={`${entry.original_file || 'result'}-${index}`} className={`item-cost-results-card ${entry.status === 'error' ? 'error' : ''}`}>
            <div className="item-cost-results-file">
              <h3>{entry.csv_file || entry.original_file || `Result ${index + 1}`}</h3>
              {entry.status === 'error' ? (
                <p>{entry.error || 'Failed to process this file.'}</p>
              ) : (
                <p>
                  {`Source: ${entry.original_file} | Columns: item, cost | Matched rows: ${entry.item_count || 0}`}
                </p>
              )}
            </div>
            {entry.status !== 'error' && entry.csv_file && (
              <button
                className="item-cost-download-btn"
                onClick={() => onDownload(entry.csv_file)}
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
                Download Item Cost CSV
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default ItemCostResults;
