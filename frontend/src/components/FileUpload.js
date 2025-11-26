import React, { useRef, useState } from 'react';
import './FileUpload.css';

function FileUpload({ onUpload, isProcessing }) {
  const fileInputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = [...e.dataTransfer.files].filter(file => 
      file.type === 'application/pdf'
    );

    if (files.length > 0) {
      setSelectedFiles(files);
    }
  };

  const handleFileSelect = (e) => {
    const files = [...e.target.files].filter(file => 
      file.type === 'application/pdf'
    );
    if (files.length > 0) {
      setSelectedFiles(files);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleSubmit = () => {
    if (selectedFiles.length > 0) {
      onUpload(selectedFiles);
      setSelectedFiles([]);
    }
  };

  const handleRemoveFile = (index) => {
    setSelectedFiles(selectedFiles.filter((_, i) => i !== index));
  };

  return (
    <div className="file-upload">
      <div
        className={`drop-zone ${dragActive ? 'active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        <div className="drop-zone-content">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="upload-icon"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
          <h2>Drop PDF files here</h2>
          <p>or click to select files</p>
          <p className="file-types">Supported: PDF</p>
        </div>
      </div>

      {selectedFiles.length > 0 && (
        <div className="file-list">
          <h3>Selected Files ({selectedFiles.length})</h3>
          <ul>
            {selectedFiles.map((file, index) => (
              <li key={index}>
                <span className="file-name">{file.name}</span>
                <span className="file-size">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </span>
                <button
                  className="remove-btn"
                  onClick={() => handleRemoveFile(index)}
                  disabled={isProcessing}
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
          <button
            className="submit-button"
            onClick={handleSubmit}
            disabled={isProcessing}
          >
            {isProcessing ? 'Processing...' : 'Process Files'}
          </button>
        </div>
      )}
    </div>
  );
}

export default FileUpload;
