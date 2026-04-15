import { useState, useCallback, useRef } from 'react';
import apiClient from '../utils/api.js';

export const useDispatch = () => {
  const [state, setState] = useState({
    status: 'idle', // idle, loading, streaming, completed, error
    currentStage: 0,
    jobId: null,
    logs: [],
    allocation: null,
    fairnessReport: null,
    critique: null,
    error: null,
  });

  const logStreamRef = useRef([]);

  const startDispatch = useCallback(async (datasetId, isCustom = false) => {
    try {
      setState(prev => ({
        ...prev,
        status: 'loading',
        logs: [],
        currentStage: 1,
        error: null,
      }));

      const response = await apiClient.dispatchAllocation(datasetId, isCustom);

      if (response.success) {
        setState(prev => ({
          ...prev,
          jobId: response.jobId,
          allocation: response,
          status: 'streaming',
        }));

        await streamLogs(response.jobId);
      } else {
        throw new Error('Failed to start dispatch');
      }
    } catch (err) {
      setState(prev => ({
        ...prev,
        status: 'error',
        error: err.message,
      }));
    }
  }, []);

  const streamLogs = useCallback(async (jobId) => {
    try {
      logStreamRef.current = [];

      for await (const log of apiClient.streamLogs(jobId)) {
        logStreamRef.current.push(log);
        setState(prev => ({
          ...prev,
          logs: [...logStreamRef.current],
          currentStage: Math.min(6, prev.currentStage + 0.15),
        }));
      }

      setState(prev => ({
        ...prev,
        currentStage: 6,
        status: 'completed',
      }));

      // Fetch fairness report and critique
      const [report, critique] = await Promise.all([
        apiClient.getFairnessReport(jobId),
        apiClient.getLLMCritique(jobId),
      ]);

      setState(prev => ({
        ...prev,
        fairnessReport: report.report,
        critique: critique.critique,
      }));
    } catch (err) {
      setState(prev => ({
        ...prev,
        status: 'error',
        error: err.message,
      }));
    }
  }, []);

  const submitCustomAllocation = useCallback(async (customData) => {
    try {
      // Validate data first
      const validation = await apiClient.validateCustomData(customData);
      if (!validation.isValid) {
        throw new Error('Invalid custom data provided');
      }

      setState(prev => ({
        ...prev,
        status: 'loading',
        logs: [],
        currentStage: 1,
        error: null,
      }));

      const response = await apiClient.submitCustomAllocation(customData);

      if (response.success) {
        setState(prev => ({
          ...prev,
          jobId: response.jobId,
          allocation: response,
          status: 'streaming',
        }));

        await streamLogs(response.jobId);
      } else {
        throw new Error('Failed to submit custom allocation');
      }
    } catch (err) {
      setState(prev => ({
        ...prev,
        status: 'error',
        error: err.message,
      }));
    }
  }, [streamLogs]);

  const reset = useCallback(() => {
    setState({
      status: 'idle',
      currentStage: 0,
      jobId: null,
      logs: [],
      allocation: null,
      fairnessReport: null,
      critique: null,
      error: null,
    });
    logStreamRef.current = [];
  }, []);

  return {
    ...state,
    startDispatch,
    submitCustomAllocation,
    reset,
  };
};

export default useDispatch;
