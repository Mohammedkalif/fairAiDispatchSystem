import React, { useState, useRef } from 'react';
import './CustomInput.css';

const CustomInput = ({ onSubmit, isLoading }) => {
  const [formStep, setFormStep] = useState(0); // 0: Upload, 1: Preview, 2: Configure
  const [drivers, setDrivers] = useState([]);
  const [clusters, setClusters] = useState([]);
  const [customConfig, setCustomConfig] = useState({
    fairness_weights: {
      workload: 0.3,
      geographic: 0.25,
      income: 0.2,
      minority: 0.15,
      response_time: 0.1,
    },
    constraints: [],
  });
  const fileInputRef = useRef(null);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const data = JSON.parse(event.target.result);
        if (data.drivers && data.clusters) {
          setDrivers(data.drivers);
          setClusters(data.clusters);
          setFormStep(1);
        } else {
          alert('Invalid file format. Expected drivers and clusters arrays.');
        }
      } catch (err) {
        alert('Error parsing JSON file.');
      }
    };
    reader.readAsText(file);
  };

  const handleWeightChange = (key, value) => {
    const numValue = parseFloat(value) || 0;
    setCustomConfig(prev => ({
      ...prev,
      fairness_weights: {
        ...prev.fairness_weights,
        [key]: numValue,
      },
    }));
  };

  const handleAddConstraint = () => {
    setCustomConfig(prev => ({
      ...prev,
      constraints: [...prev.constraints, { type: 'workload_max', value: 10 }],
    }));
  };

  const handleRemoveConstraint = (idx) => {
    setCustomConfig(prev => ({
      ...prev,
      constraints: prev.constraints.filter((_, i) => i !== idx),
    }));
  };

  const handleSubmit = () => {
    const dataToSubmit = {
      drivers,
      clusters,
      config: customConfig,
    };
    onSubmit(dataToSubmit);
  };

  const totalWeight = Object.values(customConfig.fairness_weights).reduce((a, b) => a + b, 0);
  const weightsValid = Math.abs(totalWeight - 1.0) < 0.01;

  return (
    <section className="custom-input">
      <div className="container">
        <div className="custom-header">
          <h2>Custom Data Input</h2>
          <p>Upload your own driver and cluster data with custom fairness configuration</p>
        </div>

        {/* Step 1: Upload */}
        {formStep === 0 && (
          <div className="custom-card">
            <div className="upload-section">
              <div className="upload-icon">📤</div>
              <h3>Upload Your Data</h3>
              <p>Provide a JSON file with drivers and clusters</p>

              <div className="upload-example">
                <h4>Expected Format:</h4>
                <pre>{JSON.stringify({
                  drivers: [
                    { id: 'D001', location: [40.7, -74.0], earnings: 5000 },
                    { id: 'D002', location: [40.8, -73.9], earnings: 4500 },
                  ],
                  clusters: [
                    { id: 'C01', demand: 50, location: [40.7, -74.0] },
                    { id: 'C02', demand: 30, location: [40.8, -73.9] },
                  ],
                }, null, 2)}</pre>
              </div>

              <div className="file-input-wrapper">
                <input
                  type="file"
                  accept=".json"
                  onChange={handleFileUpload}
                  ref={fileInputRef}
                  style={{ display: 'none' }}
                />
                <button
                  className="btn btn-primary btn-lg"
                  onClick={() => fileInputRef.current?.click()}
                >
                  Choose JSON File
                </button>
              </div>

              <p className="upload-hint">
                <strong>Tip:</strong> Your data will be anonymized and processed according to GDPR guidelines.
              </p>
            </div>
          </div>
        )}

        {/* Step 2: Preview */}
        {formStep === 1 && (
          <div className="custom-card">
            <div className="preview-section">
              <h3>Data Preview</h3>

              <div className="preview-grid">
                <div className="preview-box">
                  <h4>Drivers ({drivers.length})</h4>
                  <div className="preview-list">
                    {drivers.slice(0, 5).map((driver, idx) => (
                      <div key={idx} className="preview-item">
                        <code>{driver.id || `Driver ${idx + 1}`}</code>
                      </div>
                    ))}
                    {drivers.length > 5 && <div className="preview-item dim">+{drivers.length - 5} more</div>}
                  </div>
                </div>

                <div className="preview-box">
                  <h4>Clusters ({clusters.length})</h4>
                  <div className="preview-list">
                    {clusters.slice(0, 5).map((cluster, idx) => (
                      <div key={idx} className="preview-item">
                        <code>{cluster.id || `Cluster ${idx + 1}`}</code>
                      </div>
                    ))}
                    {clusters.length > 5 && <div className="preview-item dim">+{clusters.length - 5} more</div>}
                  </div>
                </div>
              </div>

              <div className="preview-actions">
                <button className="btn btn-secondary" onClick={() => setFormStep(0)}>
                  ← Upload Different File
                </button>
                <button className="btn btn-primary" onClick={() => setFormStep(2)}>
                  Configure Fairness →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Configure */}
        {formStep === 2 && (
          <div className="custom-card">
            <div className="config-section">
              <h3>Fairness Configuration</h3>

              <div className="config-group">
                <h4>Fairness Weights</h4>
                <p className="config-hint">Adjust how much weight each fairness metric receives (must sum to 1.0)</p>

                <div className="weights-container">
                  {Object.entries(customConfig.fairness_weights).map(([key, value]) => (
                    <div key={key} className="weight-input">
                      <label>{key.replace(/_/g, ' ').toUpperCase()}</label>
                      <div className="input-wrapper">
                        <input
                          type="number"
                          min="0"
                          max="1"
                          step="0.05"
                          value={value}
                          onChange={(e) => handleWeightChange(key, e.target.value)}
                        />
                        <span className="percentage">{(value * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  ))}
                </div>

                <div className={`weight-total ${weightsValid ? 'valid' : 'invalid'}`}>
                  Total: {(totalWeight * 100).toFixed(1)}% {weightsValid ? '✓' : '⚠️ Must equal 100%'}
                </div>
              </div>

              <div className="config-group">
                <h4>Allocation Constraints</h4>
                <p className="config-hint">Add custom rules to govern the allocation</p>

                <div className="constraints-list">
                  {customConfig.constraints.map((constraint, idx) => (
                    <div key={idx} className="constraint-item">
                      <select value={constraint.type} disabled>
                        <option value="workload_max">Max Workload</option>
                        <option value="workload_min">Min Workload</option>
                        <option value="geographic_range">Geographic Range</option>
                      </select>
                      <input type="number" value={constraint.value} readOnly />
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleRemoveConstraint(idx)}
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>

                <button className="btn btn-secondary" onClick={handleAddConstraint}>
                  + Add Constraint
                </button>
              </div>

              <div className="config-actions">
                <button className="btn btn-secondary" onClick={() => setFormStep(1)}>
                  ← Back
                </button>
                <button
                  className="btn btn-primary btn-lg"
                  onClick={handleSubmit}
                  disabled={!weightsValid || isLoading}
                >
                  {isLoading ? 'Processing...' : 'Run Allocation'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step Counter */}
        {formStep > 0 && (
          <div className="step-indicator">
            Step {formStep + 1} of 3
          </div>
        )}
      </div>
    </section>
  );
};

export default CustomInput;
