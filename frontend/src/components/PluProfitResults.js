import React from 'react';
import './PluProfitResults.css';

function PluProfitResults({ result, onDownload }) {
  const hasRows = (result?.row_count || 0) > 0;

  return (
    <div className="plu-results">
      <div className="plu-results-summary">
        <h2>PLU CSV Ready</h2>
        <p>
          {hasRows
            ? `Extracted ${result.row_count} rows from ${result.original_file} and sorted by %Profit`
            : `No data rows found in ${result.original_file}`}
        </p>
      </div>

      <div className="plu-results-card">
        <div className="plu-results-file">
          <h3>{result.csv_file}</h3>
          <p>Columns: plu, description, vendor_sku, label, price, cost, profit, profit_percent</p>
        </div>
        <button
          className="plu-download-btn"
          onClick={() => onDownload(result.csv_file)}
          disabled={!result.csv_file}
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
          Download PLU CSV
        </button>
      </div>
    </div>
  );
}

export default PluProfitResults;
