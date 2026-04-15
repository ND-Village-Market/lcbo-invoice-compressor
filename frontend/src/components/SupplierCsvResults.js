import React from 'react';
import './SupplierCsvResults.css';

function SupplierCsvResults({ result, onDownload, onContinue }) {
  const hasRows = result.supplier_count > 0;
  const csvFiles = Array.isArray(result.csv_files) && result.csv_files.length > 0
    ? result.csv_files
    : (result.csv_file ? [result.csv_file] : []);

  return (
    <div className="supplier-results">
      <div className="supplier-results-summary">
        <h2>Supplier CSV Ready</h2>
        <p>
          {hasRows
            ? `Extracted ${result.supplier_count} supplier values from ${result.original_file}`
            : `No supplier values found in ${result.original_file}`}
        </p>
        {hasRows && csvFiles.length > 1 && (
          <p className="supplier-results-split-note">
            Split into {csvFiles.length} files (max 250 items per file)
          </p>
        )}
      </div>

      <div className="supplier-results-list">
        {csvFiles.map((csvFile) => (
          <div key={csvFile} className="supplier-results-card">
            <div className="supplier-results-file">
              <h3>{csvFile}</h3>
              <p>Columns: sku, qty</p>
            </div>
            <div className="supplier-results-actions">
              <button
                className="supplier-download-btn"
                onClick={() => onDownload(csvFile)}
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
                Download CSV
              </button>
            </div>
          </div>
        ))}
      </div>

      {onContinue && (
        <div className="supplier-results-footer-actions">
          <button
            className="supplier-next-btn"
            onClick={onContinue}
          >
            Continue to Step 2
          </button>
        </div>
      )}
    </div>
  );
}

export default SupplierCsvResults;
