import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { LayoutDashboard, Database, Zap, Fuel, TrendingUp, Activity, Factory, Share2, Truck, DollarSign } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import NaturalGasStorage from './pages/NaturalGasStorage';
import NaturalGasPipelines from './pages/NaturalGasPipelines';
import FERCBrowser from './pages/FERCBrowser';
import Form552Browser from './pages/Form552Browser';
import ErrorBoundary from './components/ErrorBoundary';

// Market Pages
import Electricity from './pages/market/Electricity';
import NaturalGas from './pages/market/NaturalGas';
import Petroleum from './pages/market/Petroleum';
import Coal from './pages/market/Coal';
import Transportation from './pages/market/Transportation';
import MarketOverview from './components/MarketOverview';
import GasPrices from './pages/GasPrices';
import Finance from './pages/Finance';
import FinanceOverview from './pages/FinanceOverview';
import FERC1Browser from './pages/FERC1Browser';

// Forecasts
import Forecasts from './pages/forecasts/Forecasts';

import GraphExplorer from './pages/GraphExplorer';

const SidebarItem = ({ to, icon: Icon, label }: { to: string, icon: any, label: string }) => {
  const location = useLocation();
  const isActive = location.pathname === to || (to !== '/' && location.pathname.startsWith(to));
  
  return (
    <Link 
      to={to} 
      className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
        isActive 
          ? 'bg-blue-600 text-white' 
          : 'text-gray-300 hover:bg-gray-800 hover:text-white'
      }`}
    >
      <Icon size={20} />
      <span>{label}</span>
    </Link>
  );
};

const Layout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="flex h-screen bg-gray-900 text-gray-100">
      {/* Sidebar */}
      <div className="w-64 bg-gray-950 border-r border-gray-800 flex flex-col">
        <div className="p-6">
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Database className="text-blue-500" />
            CommodityData
          </h1>
        </div>
        
        <nav className="flex-1 px-4 space-y-6 overflow-y-auto">
          <div className="space-y-1">
            <SidebarItem to="/" icon={LayoutDashboard} label="Dashboard" />
          </div>

          <div>
            <div className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              Market Monitor
            </div>
            <div className="space-y-1">
              <SidebarItem to="/market/electricity" icon={Zap} label="Electricity" />
              <SidebarItem to="/market/natural-gas" icon={Activity} label="Natural Gas" />
              <SidebarItem to="/market/petroleum" icon={Fuel} label="Petroleum" />
              <SidebarItem to="/market/coal" icon={Factory} label="Coal" />
              <SidebarItem to="/market/transportation" icon={Truck} label="Transportation" />
            </div>
          </div>

          <div>
            <div className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              Analysis
            </div>
            <div className="space-y-1">
              <SidebarItem to="/finance" icon={DollarSign} label="Finance" />
              <SidebarItem to="/forecasts" icon={TrendingUp} label="Forecasts (AEO)" />
              <SidebarItem to="/graph" icon={Share2} label="Graph Explorer" />
            </div>
          </div>
        </nav>
        
        <div className="p-4 border-t border-gray-800">
          <div className="text-xs text-gray-500">v0.2.0 Beta</div>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <div className="p-8 max-w-7xl mx-auto h-full">
          {children}
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <Router>
      <Layout>
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            
            {/* Market Monitor Routes */}
            <Route path="/market/electricity" element={<Electricity />} />
            <Route path="/market/petroleum" element={<Petroleum />} />
            <Route path="/market/coal" element={<Coal />} />
            <Route path="/market/transportation" element={<Transportation />} />
            
            <Route path="/market/natural-gas" element={<NaturalGas />}>
              <Route index element={<Navigate to="overview" replace />} />
              <Route path="overview" element={<MarketOverview category="natural-gas" />} />
              <Route path="prices" element={<GasPrices />} />
              <Route path="storage" element={<NaturalGasStorage />} />
              <Route path="pipelines" element={<NaturalGasPipelines />} />
            </Route>

            {/* Finance Section */}
            <Route path="/finance" element={<Finance />}>
              <Route index element={<Navigate to="overview" replace />} />
              <Route path="overview" element={<FinanceOverview />} />
              <Route path="pipelines" element={<FERCBrowser />} />
              <Route path="electric" element={<FERC1Browser />} />
              <Route path="transactions" element={<Form552Browser />} />
            </Route>

            {/* Forecasts */}
            <Route path="/forecasts" element={<Forecasts />} />
            <Route path="/graph" element={<GraphExplorer />} />

            {/* Legacy Redirects */}
            <Route path="/eia" element={<Navigate to="/market/electricity" replace />} />
            <Route path="/natural-gas" element={<Navigate to="/market/natural-gas" replace />} />
            <Route path="/ferc" element={<Navigate to="/market/natural-gas/financials" replace />} />
            <Route path="/electricity" element={<Navigate to="/market/electricity" replace />} />
            <Route path="/petroleum" element={<Navigate to="/market/petroleum" replace />} />
            <Route path="/transportation" element={<Navigate to="/market/transportation" replace />} />
            <Route path="/environment" element={<Navigate to="/forecasts" replace />} />
            <Route path="/economy" element={<Navigate to="/forecasts" replace />} />
          </Routes>
        </ErrorBoundary>
      </Layout>
    </Router>
  );
}

export default App;
