import React, { useState } from 'react';
import { DATASETS } from '../../utils/constants.js';
import './DatasetSelector.css';

const DatasetCard = ({ dataset, isSelected, onClick }) => {
  return (
    <div
      className={`dataset-card ${isSelected ? 'selected' : ''} ${dataset.custom ? 'custom' : ''}`}
      onClick={onClick}
      role="button"
      tabIndex={0}
    >
      <div className="card-icon">{dataset.icon}</div>
      <div className="card-content">
        <h3>{dataset.name}</h3>
        <p className="card-description">{dataset.description}</p>
        <div className="card-stats">
          {Object.entries(dataset.stats).map(([key, value]) => (
            <div key={key} className="stat">
              <span className="stat-label">{key}:</span>
              <span className="stat-value">
                {typeof value === 'number' ? value.toLocaleString() : value}
              </span>
            </div>
          ))}
        </div>
      </div>
      <div className="card-check">✓</div>
    </div>
  );
};

const DatasetDetail = ({ dataset, onProceed, isLoading }) => {
  if (!dataset) {
    return (
      <div className="detail-placeholder">
        <p>Select a dataset to view details</p>
      </div>
    );
  }

  return (
    <div className="dataset-detail">
      <div className="detail-header">
        <span className="detail-icon">{dataset.icon}</span>
        <div>
          <h2>{dataset.name}</h2>
          <p>{dataset.description}</p>
        </div>
      </div>

      <div className="detail-section">
        <h4>Dataset Statistics</h4>
        <div className="detail-stats">
          {Object.entries(dataset.stats).map(([key, value]) => (
            <div key={key} className="detail-stat">
              <span className="stat-label">{key}</span>
              <span className="stat-value">
                {typeof value === 'number' ? value.toLocaleString() : value}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="detail-section">
        <h4>Key Insights</h4>
        <ul className="insights-list">
          {dataset.insights.map((insight, idx) => (
            <li key={idx}>
              <span className="insight-dot"></span>
              {insight}
            </li>
          ))}
        </ul>
      </div>

      <div className="detail-actions">
        <button
          className="btn btn-primary btn-lg"
          onClick={onProceed}
          disabled={isLoading}
        >
          {isLoading ? 'Processing...' : 'Proceed to Allocation'}
        </button>
      </div>
    </div>
  );
};

const DatasetSelector = ({ onSelectDataset, onProceed, isLoading }) => {
  const [selectedId, setSelectedId] = useState(null);
  const selectedDataset = DATASETS.find(d => d.id === selectedId);

  const handleSelect = (id) => {
    setSelectedId(id);
    onSelectDataset(id);
  };

  const handleProceed = () => {
    if (selectedId) {
      onProceed(selectedId);
    }
  };

  return (
    <section className="dataset-selector">
      <div className="container">
        <div className="section-header">
          <h2>Choose Your Dataset</h2>
          <p>Select from pre-loaded datasets or upload your own</p>
        </div>

        <div className="selector-layout">
          <div className="cards-grid">
            {DATASETS.map(dataset => (
              <DatasetCard
                key={dataset.id}
                dataset={dataset}
                isSelected={selectedId === dataset.id}
                onClick={() => handleSelect(dataset.id)}
              />
            ))}
          </div>

          <div className="detail-panel">
            <DatasetDetail
              dataset={selectedDataset}
              onProceed={handleProceed}
              isLoading={isLoading}
            />
          </div>
        </div>
      </div>
    </section>
  );
};

export default DatasetSelector;
