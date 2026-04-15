import React from 'react';
import './ItemCostResults.css';

function ItemCostResults({ result, onDownload }) {
  const hasRows = result.item_count > 0;

  return (
    <div className="item-cost-results">
      <div className="item-cost-results-summary">
        <h2>Item Cost CSV Ready</h2>
        <p>
          {hasRows
            ? `Calculated ${result.item_count} item costs from ${result.original_file}`
            : `No matching items found in ${result.original_file}`}
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
          Download Item Cost CSV
        </button>
      </div>
    </div>
  );
}

export default ItemCostResults;
