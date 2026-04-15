import { API_BASE_URL, MOCK_ALLOCATION } from './constants.js';

/* Simulate API delay */
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

/* Mock API client - Replace with actual axios calls to FastAPI */
export const apiClient = {
  /* Dispatch allocation */
  async dispatchAllocation(datasetId, custom = false) {
    await delay(2000); // Simulate processing

    return {
      success: true,
      jobId: `job-${Date.now()}`,
      ...MOCK_ALLOCATION,
      timestamp: new Date().toISOString(),
    };
  },

  /* Get allocation status */
  async getStatus(jobId) {
    return {
      success: true,
      status: 'completed',
      progress: 100,
      jobId,
    };
  },

  /* Stream logs */
  async *streamLogs(jobId) {
    const logs = [
      { timestamp: new Date().toISOString(), message: 'Starting dispatch allocation process...', level: 'info' },
      { timestamp: new Date(Date.now() + 500).toISOString(), message: 'Loading dataset...', level: 'info' },
      { timestamp: new Date(Date.now() + 1000).toISOString(), message: 'Dataset loaded: 5,234 drivers, 42 clusters', level: 'success' },
      { timestamp: new Date(Date.now() + 1500).toISOString(), message: 'Analyzing fairness constraints...', level: 'info' },
      { timestamp: new Date(Date.now() + 2000).toISOString(), message: 'Applying workload balancing algorithm...', level: 'info' },
      { timestamp: new Date(Date.now() + 2500).toISOString(), message: 'Computing allocation matrix...', level: 'info' },
      { timestamp: new Date(Date.now() + 3000).toISOString(), message: 'Running fairness audit...', level: 'info' },
      { timestamp: new Date(Date.now() + 3500).toISOString(), message: 'Allocation fairness score: 0.90', level: 'success' },
      { timestamp: new Date(Date.now() + 4000).toISOString(), message: 'Generating report...', level: 'info' },
      { timestamp: new Date(Date.now() + 4500).toISOString(), message: 'Process completed successfully!', level: 'success' },
    ];

    for (const log of logs) {
      await delay(500);
      yield log;
    }
  },

  /* Get detailed fairness report */
  async getFairnessReport(jobId) {
    await delay(1000);

    return {
      success: true,
      report: {
        jobId,
        timestamp: new Date().toISOString(),
        fairness_score: 0.90,
        coverage: 98.5,
        efficiency: 0.94,
        violations: [
          { severity: 'warning', message: 'Driver D004 workload 15% below average' },
          { severity: 'info', message: 'Cluster C05 has 8% fewer allocations' },
        ],
        recommendations: [
          'Consider adjusting minimum workload thresholds',
          'Increase incentives for underutilized clusters',
          'Monitor driver satisfaction in balanced groups',
        ],
      },
    };
  },

  /* Get LLM critique */
  async getLLMCritique(jobId) {
    await delay(1500);

    return {
      success: true,
      critique: {
        jobId,
        timestamp: new Date().toISOString(),
        audit: {
          title: 'AI Fairness Dispatch System Audit',
          summary: 'The allocation system demonstrates strong commitments to fairness with a 0.90 score, though some areas need refinement.',
          findings: [
            {
              category: 'Workload Equity',
              status: 'strong',
              detail: 'Gini coefficient of 0.18 shows excellent distribution.',
            },
            {
              category: 'Geographic Access',
              status: 'moderate',
              detail: 'Rural areas served at 87% of urban levels.',
            },
            {
              category: 'Minority Representation',
              status: 'strong',
              detail: 'Fair allocation parameters successfully balanced.',
            },
          ],
        },
        policy_violations: [],
        recommendations: [
          'Increase monitoring of geographic outliers',
          'Consider temporal fairness constraints',
          'Establish driver feedback loops',
        ],
      },
    };
  },

  /* Submit custom allocation */
  async submitCustomAllocation(customData) {
    await delay(3000);

    return {
      success: true,
      jobId: `job-${Date.now()}`,
      message: 'Custom allocation submitted successfully',
      ...MOCK_ALLOCATION,
    };
  },

  /* Validate custom data */
  async validateCustomData(data) {
    await delay(500);

    return {
      success: true,
      isValid: true,
      warnings: [],
    };
  },
};

export default apiClient;
