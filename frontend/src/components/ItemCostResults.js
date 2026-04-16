import React from 'react';
import './ItemCostResults.css';

function ItemCostResults({ result, onDownload }) {
  const sourceFiles = result.files_uploaded || 1;
  const hasRows = (result.item_count || 0) > 0;
  const sourceResults = Array.isArray(result.processing_results) ? result.processing_results : [];
  const failedSources = sourceResults.filter((entry) => entry.status === 'error');

  return (
    <div className="item-cost-results">
      <div className="item-cost-results-summary">
        <h2>Combined Item Cost CSV Ready</h2>
        <p>
          {hasRows
            ? `Processed ${sourceFiles} Quick Order file${sourceFiles === 1 ? '' : 's'} and calculated ${result.item_count} total item cost${result.item_count === 1 ? '' : 's'}`
            : `Processed ${sourceFiles} Quick Order file${sourceFiles === 1 ? '' : 's'} but found no matching items`}
        </p>
      </div>

      <div className="item-cost-results-card">
        <div className="item-cost-results-file">
          <h3>{result.csv_file}</h3>
          <p>Columns: item, cost</p>
        </div>
        <button
          className="item-cost-download-btn"
          onClick={() => onDownload(result.csv_file)}
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
          Download Combined Item Cost CSV
        </button>
      </div>

      {failedSources.length > 0 && (
        <div className="item-cost-warning">
          <h4>{`Could not process ${failedSources.length} source file${failedSources.length === 1 ? '' : 's'}`}</h4>
          <ul>
            {failedSources.map((entry, index) => (
              <li key={`${entry.original_file || 'failed'}-${index}`}>
                {`${entry.original_file}: ${entry.error || 'Unknown error'}`}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default ItemCostResults;
