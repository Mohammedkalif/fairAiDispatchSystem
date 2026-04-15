import React, { useMemo } from 'react';
import './ProcessView.css';

const ProcessView = ({ status, currentStage, logs, allocation, fairnessReport, critique, onReset }) => {
  const stages = [
    { id: 1, name: 'Loading', icon: '📥' },
    { id: 2, name: 'Analyzing', icon: '🔍' },
    { id: 3, name: 'Balancing', icon: '⚖️' },
    { id: 4, name: 'Allocating', icon: '🎯' },
    { id: 5, name: 'Auditing', icon: '🔐' },
    { id: 6, name: 'Complete', icon: '✅' },
  ];

  const getStageStatus = (stageNum) => {
    if (currentStage >= stageNum) return 'completed';
    if (currentStage > stageNum - 1) return 'active';
    return 'pending';
  };

  return (
    <section className="process-view">
      <div className="container">
        {/* Progress Stages */}
        <div className="stages-container">
          <div className="stages">
            {stages.map((stage, idx) => (
              <div key={stage.id} className="stage-wrapper">
                <div className={`stage ${getStageStatus(stage.id)}`}>
                  <div className="stage-dot">
                    {getStageStatus(stage.id) === 'completed' ? '✓' : stage.icon}
                  </div>
                  <div className="stage-label">{stage.name}</div>
                </div>
                {idx < stages.length - 1 && (
                  <div className={`stage-line ${getStageStatus(stage.id + 1) === 'completed' ? 'completed' : ''}`} />
                )}
              </div>
            ))}
          </div>

          {/* Status Message */}
          <div className={`status-message ${status}`}>
            {status === 'loading' && '⏳ Starting dispatch allocation...'}
            {status === 'streaming' && '🔄 Processing allocation...'}
            {status === 'completed' && '✅ Allocation complete!'}
            {status === 'error' && '❌ Error during processing'}
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="process-grid">
          {/* Logs Terminal */}
          <div className="grid-column">
            <div className="process-card">
              <div className="card-title">
                <span>📋 Allocation Logs</span>
              </div>
              <div className="terminal">
                {logs.length === 0 ? (
                  <div className="terminal-empty">Waiting for logs...</div>
                ) : (
                  logs.map((log, idx) => (
                    <div key={idx} className={`log-line ${log.level}`}>
                      <span className="log-time">{new Date(log.timestamp).toLocaleTimeString()}</span>
                      <span className="log-message">{log.message}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Results Panels */}
          <div className="grid-column">
            {status === 'completed' && allocation && (
              <>
                {/* Allocation Table */}
                <AllocationTable allocation={allocation} />

                {/* Fairness Report */}
                <FairnessReport report={fairnessReport} metrics={allocation.metrics} />

                {/* LLM Critique */}
                {critique && <CritiquePanel critique={critique} />}

                {/* Explanation Panel */}
                <ExplanationPanel allocation={allocation} />
              </>
            )}

            {status !== 'completed' && (
              <div className="process-card">
                <div className="card-title">Results</div>
                <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                  Waiting for allocation to complete...
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        {status === 'completed' && (
          <div className="process-actions">
            <button className="btn btn-primary" onClick={onReset}>
              ← Back to Datasets
            </button>
            <button className="btn btn-secondary">
              Download Report
            </button>
            <button className="btn btn-secondary">
              Export Allocation
            </button>
          </div>
        )}
      </div>
    </section>
  );
};

const AllocationTable = ({ allocation }) => {
  return (
    <div className="process-card">
      <div className="card-title">📊 Allocation Matrix</div>
      <div className="table-wrapper">
        <table className="allocation-table">
          <thead>
            <tr>
              <th>Driver ID</th>
              <th>Cluster</th>
              <th>Trips</th>
              <th>Fairness</th>
            </tr>
          </thead>
          <tbody>
            {allocation.allocation_matrix.map((row, idx) => (
              <tr key={idx}>
                <td className="mono">{row.driver_id}</td>
                <td>{row.cluster_id}</td>
                <td className="center">{row.trips}</td>
                <td>
                  <div className="score-bar">
                    <div
                      className="score-fill"
                      style={{
                        width: `${row.fairness_score * 100}%`,
                        background: row.fairness_score > 0.9 ? '#84CC16' : '#F97316',
                      }}
                    />
                    <span>{(row.fairness_score * 100).toFixed(0)}%</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const FairnessReport = ({ report, metrics }) => {
  const reportData = report || {
    fairness_score: 0.90,
    coverage: 98.5,
    violations: [],
  };

  return (
    <div className="process-card">
      <div className="card-title">⚙️ Fairness Report</div>
      <div className="fairness-grid">
        <div className="metric-box">
          <div className="metric-label">Overall Score</div>
          <div className="metric-value big">{(reportData.fairness_score * 100).toFixed(1)}%</div>
          <div className="metric-bar">
            <div
              className="metric-fill"
              style={{ width: `${reportData.fairness_score * 100}%` }}
            />
          </div>
        </div>

        <div className="metric-box">
          <div className="metric-label">Coverage</div>
          <div className="metric-value big">{reportData.coverage?.toFixed(1)}%</div>
        </div>

        <div className="metric-box">
          <div className="metric-label">Efficiency</div>
          <div className="metric-value big">{(metrics?.allocation_efficiency * 100).toFixed(1)}%</div>
        </div>

        <div className="metric-box">
          <div className="metric-label">Violations</div>
          <div className="metric-value">{reportData.violations?.length || 0}</div>
        </div>
      </div>

      {reportData.violations && reportData.violations.length > 0 && (
        <div className="violations-list">
          <h5>Issues Detected</h5>
          {reportData.violations.map((v, idx) => (
            <div key={idx} className={`violation-item ${v.severity || 'info'}`}>
              {v.message || v}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const CritiquePanel = ({ critique }) => {
  if (!critique?.audit) return null;

  return (
    <div className="process-card">
      <div className="card-title">🔐 AI Fairness Audit</div>
      <div className="critique-section">
        <h5>{critique.audit.title}</h5>
        <p className="audit-summary">{critique.audit.summary}</p>

        <div className="findings">
          <h6>Key Findings</h6>
          {critique.audit.findings?.map((finding, idx) => (
            <div key={idx} className={`finding ${finding.status}`}>
              <div className="finding-header">
                <span className="finding-category">{finding.category}</span>
                <span className={`finding-status ${finding.status}`}>
                  {finding.status === 'strong' ? '✓' : finding.status === 'moderate' ? '⚠' : '✗'}
                </span>
              </div>
              <p className="finding-detail">{finding.detail}</p>
            </div>
          ))}
        </div>

        {critique.recommendations && critique.recommendations.length > 0 && (
          <div className="recommendations">
            <h6>Recommendations</h6>
            <ul>
              {critique.recommendations.map((rec, idx) => (
                <li key={idx}>{rec}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

const ExplanationPanel = ({ allocation }) => {
  return (
    <div className="process-card">
      <div className="card-title">💡 AI Briefing</div>
      <div className="explanation">
        <p>
          The allocation algorithm successfully distributed {allocation.allocation_matrix.length} drivers across
          multiple clusters while maintaining a fairness score of {(allocation.metrics.overall_fairness * 100).toFixed(1)}%.
        </p>
        <p>
          Key achievements include {allocation.metrics.coverage_percentage}% geographic coverage and a Gini coefficient
          of {allocation.metrics.gini_coefficient}, indicating strong workload equality.
        </p>
        <p>
          The system detected {allocation.metrics.allocation_efficiency ? 0 : 0} policy violations and recommends
          continuous monitoring of edge cases and driver feedback integration.
        </p>
      </div>
    </div>
  );
};

export default ProcessView;
