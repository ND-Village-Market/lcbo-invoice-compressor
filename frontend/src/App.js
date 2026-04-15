import React, { useEffect, useState } from 'react';
import './App.css';
import FileUpload from './components/FileUpload';
import ProcessingResults from './components/ProcessingResults';
import SupplierCsvResults from './components/SupplierCsvResults';
import ItemCostResults from './components/ItemCostResults';

// API URL - uses environment variable in production, localhost in development
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

function App() {
  const [mode, setMode] = useState('invoice');
  const [sessionId, setSessionId] = useState(null);
  const [results, setResults] = useState([]);
  const [supplierCsvResult, setSupplierCsvResult] = useState(null);
  const [supplierStep, setSupplierStep] = useState(1);
  const [itemCostResult, setItemCostResult] = useState(null);
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
        if (supplierStep === 1) {
          const formData = new FormData();
          formData.append('file', files[0]);

          response = await fetch(`${API_URL}/extract-supplier-csv`, {
            method: 'POST',
            body: formData,
          });
        } else {
          if (!sessionId) {
            throw new Error('Step 1 must be completed before Step 2');
          }
          const formData = new FormData();
          formData.append('file', files[0]);

          response = await fetch(
            `${API_URL}/calculate-item-cost-csv?session_id=${encodeURIComponent(sessionId)}`,
            {
              method: 'POST',
              body: formData,
            }
          );
        }
      }

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();

      if (mode === 'invoice') {
        setSessionId(data.session_id);
        setResults(data.processing_results);
      } else {
        if (supplierStep === 1) {
          setSessionId(data.session_id);
          setSupplierCsvResult(data);
        } else {
          setItemCostResult(data);
        }
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
    setSupplierStep(1);
    setItemCostResult(null);
    setError(null);
  };

  const handleModeChange = (nextMode) => {
    setMode(nextMode);
    setSessionId(null);
    setResults([]);
    setSupplierCsvResult(null);
    setSupplierStep(1);
    setItemCostResult(null);
    setError(null);
  };

  const handleContinueToStep2 = () => {
    setSupplierStep(2);
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
            : 'Step 1: Generate supplier SKU CSV, then Step 2: upload Quick Order PDF to calculate item costs'}
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
                : 'Step 1: Drop item list PDF here'
            }
            subtitle={
              isInvoiceMode
                ? 'or click to select files'
                : 'or click to select one PDF for supplier extraction'
            }
            submitLabel={
              isInvoiceMode
                ? 'Process Files'
                : 'Generate Step 1 Supplier CSV'
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
              <>
                {supplierCsvResult && (
                  <SupplierCsvResults
                    result={supplierCsvResult}
                    onDownload={handleDownload}
                    onContinue={supplierStep === 1 ? handleContinueToStep2 : undefined}
                  />
                )}

                {supplierStep === 2 && !itemCostResult && (
                  <div className="step-section">
                    <h2>Step 2: Upload Quick Order PDF</h2>
                    <p>
                      Upload the wholesale pricing document to calculate item costs for Step 1 SKUs.
                    </p>
                    <FileUpload
                      onUpload={handleUpload}
                      isProcessing={isProcessing}
                      multiple={false}
                      title="Drop Quick Order PDF here"
                      subtitle="or click to select one PDF for cost calculation"
                      submitLabel="Generate Step 2 Item Cost CSV"
                    />
                  </div>
                )}

                {itemCostResult && (
                  <ItemCostResults
                    result={itemCostResult}
                    onDownload={handleDownload}
                  />
                )}
              </>
            )}
            <button 
              className="reset-button"
              onClick={handleReset}
            >
              {isInvoiceMode ? 'Process More Files' : 'Start New Two-Step Run'}
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
