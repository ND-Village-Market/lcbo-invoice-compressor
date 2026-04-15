import React, { useEffect, useState } from 'react';
import './App.css';
import FileUpload from './components/FileUpload';
import ProcessingResults from './components/ProcessingResults';
import SupplierCsvResults from './components/SupplierCsvResults';

// API URL - uses environment variable in production, localhost in development
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

function App() {
  const [mode, setMode] = useState('invoice');
  const [sessionId, setSessionId] = useState(null);
  const [results, setResults] = useState([]);
  const [supplierCsvResult, setSupplierCsvResult] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showWarmupHint, setShowWarmupHint] = useState(false);
  const [error, setError] = useState(null);

  // Show a Render warmup hint if processing takes longer than a few seconds
  useEffect(() => {
    if (!isProcessing) {
      setShowWarmupHint(false);
      return undefined;
    }

    const timer = setTimeout(() => setShowWarmupHint(true), 7000);
    return () => clearTimeout(timer);
  }, [isProcessing]);

  const handleUpload = async (files) => {
    setIsProcessing(true);
    setError(null);

    try {
      let response;
      if (mode === 'invoice') {
        const formData = new FormData();
        files.forEach(file => {
          formData.append('files', file);
        });

        response = await fetch(`${API_URL}/upload`, {
          method: 'POST',
          body: formData,
        });
      } else {
        const formData = new FormData();
        formData.append('file', files[0]);

        response = await fetch(`${API_URL}/extract-supplier-csv`, {
          method: 'POST',
          body: formData,
        });
      }

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      setSessionId(data.session_id);
      if (mode === 'invoice') {
        setResults(data.processing_results);
      } else {
        setSupplierCsvResult(data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownload = async (filename) => {
    if (!sessionId) return;

    try {
      const response = await fetch(
        `${API_URL}/download/${sessionId}/${filename}`
      );

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleReset = () => {
    setSessionId(null);
    setResults([]);
    setSupplierCsvResult(null);
    setError(null);
  };

  const handleModeChange = (nextMode) => {
    setMode(nextMode);
    setSessionId(null);
    setResults([]);
    setSupplierCsvResult(null);
    setError(null);
  };

  const isInvoiceMode = mode === 'invoice';

  return (
    <div className="app">
      <header className="app-header">
        <h1>LCBO Document Tools</h1>
        <p>
          {isInvoiceMode
            ? 'Upload PDF invoices to process and download condensed versions'
            : 'Upload an item list PDF to generate a supplier SKU CSV'}
        </p>
        <div className="feature-switcher" role="tablist" aria-label="Feature switcher">
          <button
            className={`feature-switch-btn ${isInvoiceMode ? 'active' : ''}`}
            onClick={() => handleModeChange('invoice')}
          >
            Invoice Condenser
          </button>
          <button
            className={`feature-switch-btn ${!isInvoiceMode ? 'active' : ''}`}
            onClick={() => handleModeChange('supplier-csv')}
          >
            Supplier CSV Extractor
          </button>
        </div>
      </header>

      <main className="app-main">
        {error && <div className="error-message">{error}</div>}

        {isProcessing && (
          <div className="loading-card">
            <div className="spinner" aria-hidden="true" />
            <div className="loading-text">Processing your documents...</div>
            {showWarmupHint && (
              <div className="loading-subtext">
                If this takes a bit, the Render server may be spinning up. Please stay on this page.
              </div>
            )}
          </div>
        )}

        {!sessionId ? (
          <FileUpload 
            onUpload={handleUpload} 
            isProcessing={isProcessing}
            multiple={isInvoiceMode}
            title={
              isInvoiceMode
                ? 'Drop PDF files here'
                : 'Drop item list PDF here'
            }
            subtitle={
              isInvoiceMode
                ? 'or click to select files'
                : 'or click to select one PDF'
            }
            submitLabel={
              isInvoiceMode
                ? 'Process Files'
                : 'Generate Supplier CSV'
            }
          />
        ) : (
          <>
            {isInvoiceMode ? (
              <ProcessingResults 
                results={results}
                onDownload={handleDownload}
              />
            ) : (
              <SupplierCsvResults
                result={supplierCsvResult}
                onDownload={handleDownload}
              />
            )}
            <button 
              className="reset-button"
              onClick={handleReset}
            >
              {isInvoiceMode ? 'Process More Files' : 'Generate Another CSV'}
            </button>
          </>
        )}
      </main>

      <footer className="app-footer">
        <p>&copy; 2026 LCBO Document Tools</p>
      </footer>
    </div>
  );
}

export default App;
