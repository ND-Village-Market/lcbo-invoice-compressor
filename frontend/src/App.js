import React, { useState } from 'react';
import './App.css';
import FileUpload from './components/FileUpload';
import ProcessingResults from './components/ProcessingResults';

// API URL - uses environment variable in production, localhost in development
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [results, setResults] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);

  const handleUpload = async (files) => {
    setIsProcessing(true);
    setError(null);

    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });

      const response = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      setSessionId(data.session_id);
      setResults(data.processing_results);
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
    setError(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>LCBO Invoice Processor</h1>
        <p>Upload PDF invoices to process and download condensed versions</p>
      </header>

      <main className="app-main">
        {error && <div className="error-message">{error}</div>}

        {!sessionId ? (
          <FileUpload 
            onUpload={handleUpload} 
            isProcessing={isProcessing}
          />
        ) : (
          <>
            <ProcessingResults 
              results={results}
              onDownload={handleDownload}
            />
            <button 
              className="reset-button"
              onClick={handleReset}
            >
              Process More Files
            </button>
          </>
        )}
      </main>

      <footer className="app-footer">
        <p>&copy; 2024 LCBO Invoice Processor</p>
      </footer>
    </div>
  );
}

export default App;
