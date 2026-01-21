import React, { useState } from 'react';
import Dashboard from './components/Dashboard';
import useData from './hooks/useData';
import clsx from 'clsx';

function App() {
  const [datasetType, setDatasetType] = useState('extreme');
  const { data, detailedData, loading, detailedLoading, error, fetchDetailed } = useData(datasetType);

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 font-sans selection:bg-pink-500 selection:text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 sticky top-0 z-50 backdrop-blur-md bg-opacity-80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg shadow-lg flex items-center justify-center">
              <span className="font-bold text-white text-lg">V</span>
            </div>
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
              Sensor Analysis Visualizer
            </h1>
          </div>

          <div className="flex space-x-2 bg-gray-900 p-1 rounded-lg border border-gray-700">
            <TabButton
              active={datasetType === 'extreme'}
              onClick={() => setDatasetType('extreme')}
            >
              Extreme Test
            </TabButton>
            <TabButton
              active={datasetType === 'hard'}
              onClick={() => setDatasetType('hard')}
            >
              Hard Test
            </TabButton>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading && (
          <div className="flex flex-col items-center justify-center h-64 space-y-4">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-gray-400 animate-pulse">Loading data...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-900/50 border border-red-500 text-red-200 p-4 rounded-lg flex items-center space-x-3">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            <span>Error loading data: {error}</span>
          </div>
        )}

        {!loading && !error && (
          <Dashboard
            data={data}
            detailedData={detailedData}
            fetchDetailed={fetchDetailed}
            detailedLoading={detailedLoading}
          />
        )}
      </main>
    </div>
  );
}

const TabButton = ({ active, onClick, children }) => (
  <button
    onClick={onClick}
    className={clsx(
      "px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500",
      active
        ? "bg-gray-800 text-white shadow-sm border border-gray-600"
        : "text-gray-400 hover:text-white hover:bg-gray-800"
    )}
  >
    {children}
  </button>
);

export default App;
