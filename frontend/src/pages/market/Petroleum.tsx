import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, 
  BarChart, Bar, AreaChart, Area, ComposedChart
} from 'recharts';
import { Calendar, DollarSign, Activity, Layers, Droplet, TrendingUp } from 'lucide-react';

const Petroleum = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [prices, setPrices] = useState<any[]>([]);
  const [rigs, setRigs] = useState<any[]>([]);
  const [cot, setCot] = useState<any[]>([]);
  const [stocks, setStocks] = useState<any[]>([]);
  const [curve, setCurve] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Parallel fetch
        const [wtiRes, brentRes, rigRes, cotRes, stockRes, curveRes] = await Promise.all([
          fetch('http://localhost:8000/financials/petroleum/prices?metric=WTI Spot Price&start_date=2020-01-01'),
          fetch('http://localhost:8000/financials/petroleum/prices?metric=Brent Spot Price&start_date=2020-01-01'),
          fetch('http://localhost:8000/financials/rig-count?start_date=2020-01-01'),
          fetch('http://localhost:8000/financials/cot?start_date=2020-01-01'),
          fetch('http://localhost:8000/financials/petroleum/stocks?metric=Crude Stocks Total&start_date=2020-01-01'),
          fetch('http://localhost:8000/financials/petroleum/futures')
        ]);

        const wti = await wtiRes.json();
        const brent = await brentRes.json();
        const rigData = await rigRes.json();
        const cotData = await cotRes.json();
        const stockData = await stockRes.json();
        const curveData = await curveRes.json();

        // Merge Prices
        const priceMap = new Map();
        wti.forEach((d: any) => priceMap.set(d.date, { date: d.date, wti: d.value }));
        brent.forEach((d: any) => {
          if (priceMap.has(d.date)) {
            priceMap.get(d.date).brent = d.value;
          } else {
            priceMap.set(d.date, { date: d.date, brent: d.value });
          }
        });
        setPrices(Array.from(priceMap.values()).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()));

        setRigs(rigData);
        setCot(cotData);
        setStocks(stockData);
        setCurve(curveData.curve || []);

      } catch (err) {
        console.error("Failed to fetch petroleum data", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const TabButton = ({ id, label, icon: Icon }: any) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
        activeTab === id 
          ? 'bg-blue-600 text-white shadow-sm' 
          : 'text-gray-600 hover:bg-gray-100'
      }`}
    >
      <Icon size={18} />
      {label}
    </button>
  );

  if (loading) return <div className="p-8 text-center text-gray-500">Loading Petroleum Data...</div>;

  return (
    <div className="p-6 max-w-[1600px] mx-auto space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Petroleum Market</h1>
          <p className="text-gray-500">Crude Oil Prices, Inventory, and Upstream Activity</p>
        </div>
        
        <div className="flex flex-wrap gap-2 bg-white p-1 rounded-xl border border-gray-200 shadow-sm">
          <TabButton id="overview" label="Overview" icon={Activity} />
          <TabButton id="prices" label="Prices & Futures" icon={DollarSign} />
          <TabButton id="inventory" label="Inventory" icon={Layers} />
          <TabButton id="upstream" label="Upstream" icon={TrendingUp} />
        </div>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Price Chart */}
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <DollarSign size={20} className="text-green-600" />
              Crude Oil Spot Prices (WTI vs Brent)
            </h3>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={prices}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={(val) => new Date(val).toLocaleDateString(undefined, {month: 'short', year: '2-digit'})}
                    minTickGap={30}
                    tick={{fontSize: 12}}
                  />
                  <YAxis domain={['auto', 'auto']} tick={{fontSize: 12}} />
                  <Tooltip 
                    contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)'}}
                    labelFormatter={(val) => new Date(val).toLocaleDateString()}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="wti" name="WTI" stroke="#2563eb" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="brent" name="Brent" stroke="#dc2626" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Rig Count */}
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <TrendingUp size={20} className="text-amber-600" />
              US Rig Count (Total)
            </h3>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={rigs}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={(val) => new Date(val).toLocaleDateString(undefined, {month: 'short', year: '2-digit'})}
                    minTickGap={30}
                    tick={{fontSize: 12}}
                  />
                  <YAxis tick={{fontSize: 12}} />
                  <Tooltip 
                    contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)'}}
                    labelFormatter={(val) => new Date(val).toLocaleDateString()}
                  />
                  <Area type="monotone" dataKey="total" name="Total Rigs" stroke="#d97706" fill="#fcd34d" fillOpacity={0.3} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* COT Positioning */}
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm lg:col-span-2">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Activity size={20} className="text-purple-600" />
              Managed Money Net Positioning (WTI)
            </h3>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={cot}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={(val) => new Date(val).toLocaleDateString(undefined, {month: 'short', year: '2-digit'})}
                    minTickGap={30}
                    tick={{fontSize: 12}}
                  />
                  <YAxis tick={{fontSize: 12}} />
                  <Tooltip 
                    contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)'}}
                    labelFormatter={(val) => new Date(val).toLocaleDateString()}
                  />
                  <Legend />
                  <Bar dataKey="managed_money_net" name="Net Length" fill="#8b5cf6" barSize={20} />
                  <Line type="monotone" dataKey="open_interest" name="Open Interest" stroke="#9ca3af" strokeWidth={1} dot={false} yAxisId={0} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Prices Tab */}
      {activeTab === 'prices' && (
        <div className="grid grid-cols-1 gap-6">
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <h3 className="text-lg font-semibold mb-4">WTI Futures Curve (Latest)</h3>
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={curve}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="contract" label={{ value: 'Contract Month', position: 'insideBottom', offset: -5 }} />
                  <YAxis label={{ value: 'Price ($/bbl)', angle: -90, position: 'insideLeft' }} domain={['auto', 'auto']} />
                  <Tooltip />
                  <Line type="monotone" dataKey="price" stroke="#2563eb" strokeWidth={3} dot={{r: 6}} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="text-sm text-gray-500 mt-4">
              Visualizing the term structure (Contango vs Backwardation) for the first 4 contracts.
            </p>
          </div>
        </div>
      )}
      
      {/* Inventory Tab */}
      {activeTab === 'inventory' && (
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">US Commercial Crude Stocks</h3>
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stocks}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(val) => new Date(val).toLocaleDateString(undefined, {month: 'short', year: '2-digit'})}
                />
                <YAxis domain={['auto', 'auto']} />
                <Tooltip labelFormatter={(val) => new Date(val).toLocaleDateString()} />
                <Area type="monotone" dataKey="value" name="Thousand Barrels" stroke="#059669" fill="#10b981" fillOpacity={0.2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Upstream Tab */}
      {activeTab === 'upstream' && (
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold mb-4">Rig Count by Basin (Permian vs Others)</h3>
          <p className="text-gray-500">
            (Detailed basin breakdown visualization coming soon - currently showing aggregated total)
          </p>
          <div className="h-[400px] mt-4">
             <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={rigs}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={(val) => new Date(val).toLocaleDateString(undefined, {month: 'short', year: '2-digit'})}
                  />
                  <YAxis />
                  <Tooltip labelFormatter={(val) => new Date(val).toLocaleDateString()} />
                  <Legend />
                  <Area type="monotone" dataKey="oil" stackId="1" name="Oil Rigs" stroke="#2563eb" fill="#3b82f6" />
                  <Area type="monotone" dataKey="gas" stackId="1" name="Gas Rigs" stroke="#dc2626" fill="#ef4444" />
                </AreaChart>
              </ResponsiveContainer>
          </div>
        </div>
      )}

    </div>
  );
};

export default Petroleum;
