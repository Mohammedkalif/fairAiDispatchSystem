import React, { useState, useEffect } from 'react';
import './Hero.css';

const Hero = ({ onProceed }) => {
  const [activeTab, setActiveTab] = useState(0);

  const tabs = [
    {
      title: 'The Problem',
      icon: '⚠️',
      content: {
        heading: 'Dispatch Systems Are Inherently Unfair',
        points: [
          'Geographic Bias: Drivers in certain areas consistently receive fewer/more trips',
          'Income Inequality: Algorithmic bias perpetuates driver earnings gaps',
          'Minority Discrimination: Historical patterns predict worse outcomes for underrepresented groups',
          'Coverage Gaps: Underserved neighborhoods get systematically deprioritized',
          'Workers Rights: Lack of transparency in allocation decisions',
        ],
      },
    },
    {
      title: 'Our Solution',
      icon: '✨',
      content: {
        heading: 'Fair AI-Powered Dispatch Allocation',
        points: [
          'Explainable Algorithms: Full transparency in fairness calculations',
          'Multi-Metric Fairness: Balance workload, geography, income, and representation',
          'Constraint Satisfaction: Meets service requirements while maximizing equity',
          'Continuous Auditing: Real-time fairness monitoring and violation detection',
          'Policy Integration: Customizable rules for your specific fairness goals',
        ],
      },
    },
    {
      title: 'Current Limitations (V1)',
      icon: '🔍',
      content: {
        heading: 'What We\'re Still Working On',
        points: [
          'Real-time Processing: Currently optimized for hourly/shift-level allocation',
          'Temporal Dynamics: Limited support for dynamic driver availability',
          'Custom Constraints: Basic constraint language, expanding in V2',
          'Scalability: Tested on 50K drivers, larger deployments in progress',
          'Integration: Manual data export/import, API connections coming soon',
        ],
      },
    },
  ];

  return (
    <section className="hero">
      <div className="hero-container">
        {/* Hero Header */}
        <div className="hero-header">
          <h1 className="hero-title">
            <span className="gradient-text">Eliminate Bias</span>
            <br />
            in Dispatch Systems
          </h1>
          <p className="hero-subtitle">
            Fair AI allocation ensures every driver and customer is treated equitably
          </p>
        </div>

        {/* Tabs */}
        <div className="hero-tabs">
          <div className="tab-buttons">
            {tabs.map((tab, idx) => (
              <button
                key={idx}
                className={`tab-button ${activeTab === idx ? 'active' : ''}`}
                onClick={() => setActiveTab(idx)}
              >
                <span className="tab-icon">{tab.icon}</span>
                <span className="tab-title">{tab.title}</span>
              </button>
            ))}
          </div>

          <div className="tab-content">
            <div className="content-header">
              <h2>{tabs[activeTab].content.heading}</h2>
            </div>
            <ul className="content-list">
              {tabs[activeTab].content.points.map((point, idx) => (
                <li key={idx} className="content-item">
                  <span className="item-dot"></span>
                  {point}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* CTA */}
        <div className="hero-cta">
          <button className="btn btn-primary btn-lg" onClick={onProceed}>
            Get Started
            <span style={{ fontSize: '1.25rem' }}>→</span>
          </button>
          <p style={{ color: 'var(--text-muted)', marginTop: '1rem' }}>
            Choose from 5 pre-loaded datasets or upload your own data
          </p>
        </div>
      </div>
    </section>
  );
};

export default Hero;
