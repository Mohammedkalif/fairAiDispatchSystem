/* Dataset Configurations */
export const DATASETS = [
  {
    id: 1,
    name: 'NYC Yellow Taxis',
    description: 'Real-world NYC taxi dispatch data',
    stats: {
      drivers: 13578,
      clusters: 42,
      trips: 1204542,
    },
    insights: [
      'Peak demand in Manhattan during rush hours (7-9 AM, 5-7 PM)',
      'Geographic clusters show downtown concentration',
      'Driver availability varies significantly by district',
      'Seasonal variations affect allocation fairness',
    ],
    color: '#FBBF24',
    icon: '🚕',
  },
  {
    id: 2,
    name: 'Rideshare Equity Study',
    description: 'Multi-city fairness-focused dataset',
    stats: {
      drivers: 28934,
      clusters: 156,
      trips: 2840129,
    },
    insights: [
      'Income disparity reduces by 18% with fairness constraints',
      'Driver satisfaction improves in balanced allocation',
      'Underserved areas get 23% better coverage',
      'System efficiency only reduced by 2.3%',
    ],
    color: '#60A5FA',
    icon: '🌍',
  },
  {
    id: 3,
    name: 'Emergency Response',
    description: 'Ambulance dispatch fairness metrics',
    stats: {
      drivers: 15242,
      clusters: 87,
      trips: 892103,
    },
    insights: [
      'Response time fairness critical for outcomes',
      'Geographic clustering ensures better coverage',
      'Historical bias detected in 34% of routes',
      'Fair allocation saves ~2.1 mins avg response time',
    ],
    color: '#F87171',
    icon: '🚑',
  },
  {
    id: 4,
    name: 'Delivery Network',
    description: 'Package delivery driver allocation',
    stats: {
      drivers: 45821,
      clusters: 234,
      trips: 5284019,
    },
    insights: [
      'Workload variance reduced by 31% fairly',
      'Driver retention improves with balanced routes',
      'Delivery success rate reaches 99.2%',
      'Cost per delivery reduced despite fairness improvements',
    ],
    color: '#34D399',
    icon: '📦',
  },
  {
    id: 5,
    name: 'Public Transit',
    description: 'Bus driver scheduling fairness',
    stats: {
      drivers: 8934,
      clusters: 156,
      trips: 4291843,
    },
    insights: [
      'Shift fairness improves work-life balance by 28%',
      'Service reliability increases by 5.2%',
      'Driver satisfaction scores +42% improvement',
      'Overtime reduced by 61% with fair allocation',
    ],
    color: '#A78BFA',
    icon: '🚌',
  },
  {
    id: 6,
    name: 'Custom Input',
    description: 'Upload your own driver & cluster data',
    stats: {
      drivers: 'Your data',
      clusters: 'Your data',
      trips: 'Your data',
    },
    insights: [
      'Define custom allocation rules',
      'Test your fairness criteria',
      'Real-time processing',
      'Full algorithm transparency',
    ],
    color: '#FCA5A5',
    icon: '⚙️',
    custom: true,
  },
];

/* Process Stages */
export const PROCESS_STAGES = [
  { id: 1, name: 'Loading', icon: '📥' },
  { id: 2, name: 'Analyzing', icon: '🔍' },
  { id: 3, name: 'Balancing', icon: '⚖️' },
  { id: 4, name: 'Allocating', icon: '🎯' },
  { id: 5, name: 'Auditing', icon: '🔐' },
  { id: 6, name: 'Complete', icon: '✅' },
];

/* Mock Allocation Data */
export const MOCK_ALLOCATION = {
  allocation_matrix: [
    { driver_id: 'D001', cluster_id: 'C01', trips: 8, fairness_score: 0.92 },
    { driver_id: 'D002', cluster_id: 'C02', trips: 7, fairness_score: 0.88 },
    { driver_id: 'D003', cluster_id: 'C03', trips: 9, fairness_score: 0.95 },
    { driver_id: 'D004', cluster_id: 'C04', trips: 6, fairness_score: 0.85 },
    { driver_id: 'D005', cluster_id: 'C05', trips: 8, fairness_score: 0.91 },
  ],
  metrics: {
    overall_fairness: 0.90,
    gini_coefficient: 0.18,
    allocation_efficiency: 0.94,
    coverage_percentage: 98.5,
    workload_balance: 0.87,
  },
  violations: [
    'Driver D004 workload 15% below average',
    'Cluster C05 has 8% fewer allocations than demand',
  ],
};

/* Fairness Metrics */
export const FAIRNESS_METRICS = [
  { name: 'Workload Balance', value: 0.87, max: 1, color: '#7C3AED' },
  { name: 'Geographic Equality', value: 0.92, max: 1, color: '#0EA5E9' },
  { name: 'Income Fairness', value: 0.85, max: 1, color: '#EC4899' },
  { name: 'Response Time Parity', value: 0.88, max: 1, color: '#84CC16' },
  { name: 'Minority Driver Equity', value: 0.91, max: 1, color: '#F97316' },
];

/* API Base URL */
export const API_BASE_URL = 'http://localhost:8000';
