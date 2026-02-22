import { useState } from 'react';
import MarketOverview from '../../components/MarketOverview';
import PlantBrowser from '../PlantBrowser';
import FERC1Browser from '../FERC1Browser';
import TransmissionMap from '../../components/TransmissionMap';
import ErcotMarket from '../../components/ErcotMarket';

const Electricity = () => {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="h-full flex flex-col space-y-6">
      <div className="flex items-center justify-between border-b border-gray-700 pb-4">
        <h2 className="text-2xl font-bold text-white">Electricity Market</h2>
        <div className="flex bg-gray-800 rounded-lg p-1 border border-gray-700">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors ${activeTab === 'overview' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
          >
            Market Overview
          </button>
          <button
            onClick={() => setActiveTab('grid')}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors ${activeTab === 'grid' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
          >
            Grid Topology
          </button>
          <button
            onClick={() => setActiveTab('ercot')}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors ${activeTab === 'ercot' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
          >
            ERCOT Pricing
          </button>
          <button
            onClick={() => setActiveTab('plants')}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors ${activeTab === 'plants' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
          >
            Plant Browser
          </button>
          <button
            onClick={() => setActiveTab('financials')}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors ${activeTab === 'financials' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
          >
            Financials (FERC)
          </button>
        </div>
      </div>
      
      <div className="flex-1 min-h-0">
        {activeTab === 'overview' ? (
          <MarketOverview category="electricity" />
        ) : activeTab === 'grid' ? (
          <TransmissionMap />
        ) : activeTab === 'ercot' ? (
          <ErcotMarket />
        ) : activeTab === 'plants' ? (
          <PlantBrowser />
        ) : (
          <FERC1Browser />
        )}
      </div>
    </div>
  );
};

export default Electricity;
