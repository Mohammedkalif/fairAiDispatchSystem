import React, { useState } from 'react';
import './styles/globals.css';
import Navbar from './components/shared/Navbar';
import Hero from './components/Hero/Hero';
import DatasetSelector from './components/DatasetSelector/DatasetSelector';
import ProcessView from './components/ProcessView/ProcessView';
import CustomInput from './components/CustomInput/CustomInput';
import useDispatch from './hooks/useDispatch';

function App() {
  const [view, setView] = useState('home'); // home, datasets, process, custom
  const [selectedDatasetId, setSelectedDatasetId] = useState(null);
  const [isCustom, setIsCustom] = useState(false);
  const dispatch = useDispatch();

  const handleProceedFromHero = () => {
    setView('datasets');
  };

  const handleSelectDataset = (id) => {
    setSelectedDatasetId(id);
    if (id === 6) {
      setView('custom');
      setIsCustom(true);
    }
  };

  const handleProceedFromDataset = (id) => {
    setSelectedDatasetId(id);
    setIsCustom(false);
    dispatch.startDispatch(id, false);
    setView('process');
  };

  const handleCustomSubmit = async (data) => {
    setIsCustom(true);
    await dispatch.submitCustomAllocation(data);
    setView('process');
  };

  const handleReset = () => {
    dispatch.reset();
    setSelectedDatasetId(null);
    setIsCustom(false);
    setView('home');
  };

  return (
    <div className="app">
      <Navbar currentView={view} />

      {view === 'home' && (
        <Hero onProceed={handleProceedFromHero} />
      )}

      {view === 'datasets' && (
        <DatasetSelector
          onSelectDataset={handleSelectDataset}
          onProceed={handleProceedFromDataset}
          isLoading={dispatch.status === 'loading'}
        />
      )}

      {view === 'process' && (
        <ProcessView
          status={dispatch.status}
          currentStage={dispatch.currentStage}
          logs={dispatch.logs}
          allocation={dispatch.allocation}
          fairnessReport={dispatch.fairnessReport}
          critique={dispatch.critique}
          onReset={handleReset}
        />
      )}

      {view === 'custom' && (
        <CustomInput
          onSubmit={handleCustomSubmit}
          isLoading={dispatch.status === 'loading' || dispatch.status === 'streaming'}
        />
      )}
    </div>
  );
}

export default App;
