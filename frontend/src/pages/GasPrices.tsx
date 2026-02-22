import React, { useState, useEffect, useMemo } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';
import { TrendingUp, Map as MapIcon, DollarSign, Calendar } from 'lucide-react';
import axios from 'axios';

// State coordinates for map (reused from Pipelines)
const STATE_COORDINATES: Record<string, { x: number, y: number }> = {
  'AL': { x: 670, y: 480 }, 'AK': { x: 100, y: 550 }, 'AZ': { x: 200, y: 430 },
  'AR': { x: 550, y: 430 }, 'CA': { x: 50, y: 350 }, 'CO': { x: 300, y: 350 },
  'CT': { x: 920, y: 230 }, 'DE': { x: 880, y: 300 }, 'FL': { x: 800, y: 550 },
  'GA': { x: 750, y: 480 }, 'HI': { x: 300, y: 600 }, 'ID': { x: 200, y: 200 },
  'IL': { x: 600, y: 300 }, 'IN': { x: 650, y: 300 }, 'IA': { x: 500, y: 280 },
  'KS': { x: 450, y: 380 }, 'KY': { x: 700, y: 360 }, 'LA': { x: 550, y: 520 },
  'ME': { x: 950, y: 100 }, 'MD': { x: 850, y: 310 }, 'MA': { x: 920, y: 210 },
  'MI': { x: 680, y: 220 }, 'MN': { x: 500, y: 180 }, 'MS': { x: 600, y: 480 },
  'MO': { x: 550, y: 360 }, 'MT': { x: 300, y: 150 }, 'NE': { x: 400, y: 300 },
  'NV': { x: 150, y: 300 }, 'NH': { x: 920, y: 180 }, 'NJ': { x: 900, y: 270 },
  'NM': { x: 300, y: 450 }, 'NY': { x: 850, y: 200 }, 'NC': { x: 820, y: 400 },
  'ND': { x: 400, y: 150 }, 'OH': { x: 720, y: 300 }, 'OK': { x: 450, y: 430 },
  'OR': { x: 100, y: 200 }, 'PA': { x: 820, y: 270 }, 'RI': { x: 930, y: 230 },
  'SC': { x: 800, y: 440 }, 'SD': { x: 400, y: 220 }, 'TN': { x: 680, y: 400 },
  'TX': { x: 450, y: 500 }, 'UT': { x: 250, y: 350 }, 'VT': { x: 900, y: 170 },
  'VA': { x: 820, y: 350 }, 'WA': { x: 100, y: 100 }, 'WV': { x: 780, y: 330 },
  'WI': { x: 580, y: 220 }, 'WY': { x: 300, y: 250 }, 'DC': { x: 850, y: 320 }
};

const GasPrices = () => {
  const [henryHubData, setHenryHubData] = useState<any[]>([]);
  const [selectedState, setSelectedState] = useState<string>('CA');
  const [statePriceData, setStatePriceData] = useState<any[]>([]);
  const [basisMapData, setBasisMapData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'chart' | 'map'>('chart');
  const [year, setYear] = useState(2023);
  const [month, setMonth] = useState(1);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch Henry Hub History
        const hhRes = await axios.get('http://localhost:8000/financials/gas/prices/history?location=Henry Hub');
        setHenryHubData(hhRes.data);

        // Fetch State History
        const stateRes = await axios.get(`http://localhost:8000/financials/gas/prices/history?location=${selectedState}`);
        setStatePriceData(stateRes.data);

        // Fetch Basis Map for selected period
        const mapRes = await axios.get(`http://localhost:8000/financials/gas/prices/basis?year=${year}&month=${month}`);
        setBasisMapData(mapRes.data);

      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [selectedState, year, month]);

  // Combine data for chart
  const chartData = useMemo(() => {
    if (!henryHubData.length || !statePriceData.length) return [];
    
    // Create a map of date -> values
    const dataMap = new Map();
    
    henryHubData.forEach(d => {
      dataMap.set(d.date, { date: d.date, henry_hub: d.value });
    });
    
    statePriceData.forEach(d => {
      if (dataMap.has(d.date)) {
        const entry = dataMap.get(d.date);
        entry.state_price = d.value;
        entry.basis = d.value - entry.henry_hub;
      } else {
        dataMap.set(d.date, { date: d.date, state_price: d.value });
      }
    });
    
    return Array.from(dataMap.values())
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .filter(d => d.henry_hub !== undefined && d.state_price !== undefined); // Only show overlapping periods
  }, [henryHubData, statePriceData]);

  const renderMap = () => {
    if (!basisMapData) return null;

    return (
      <div className="relative w-full h-full bg-gray-900 rounded-xl overflow-hidden border border-gray-700">
        <svg viewBox="0 0 1000 650" className="w-full h-full">
          {Object.entries(STATE_COORDINATES).map(([code, coords]) => {
            const stateData = basisMapData.states.find((s: any) => s.state === code);
            const basis = stateData ? stateData.basis : 0;
            
            // Color scale: Blue (Negative Basis) -> Gray (Zero) -> Red (Positive Basis)
            let fill = '#6b7280';
            if (basis > 0) {
              // Premium market (Red)
              const intensity = Math.min(1, basis / 5); // Max red at +$5
              fill = `rgba(239, 68, 68, ${0.3 + intensity * 0.7})`;
            } else if (basis < 0) {
              // Discount market (Blue)
              const intensity = Math.min(1, Math.abs(basis) / 2); // Max blue at -$2
              fill = `rgba(59, 130, 246, ${0.3 + intensity * 0.7})`;
            }

            return (
              <g 
                key={code} 
                onClick={() => setSelectedState(code)}
                className="cursor-pointer hover:opacity-80 transition-opacity"
              >
                <circle cx={coords.x} cy={coords.y} r={20} fill={fill} stroke="#1f2937" strokeWidth="2" />
                <text x={coords.x} y={coords.y} textAnchor="middle" dy=".3em" fill="white" fontSize="10" fontWeight="bold">
                  {code}
                </text>
                <text x={coords.x} y={coords.y + 28} textAnchor="middle" fill={basis > 0 ? '#fca5a5' : '#93c5fd'} fontSize="9">
                  {basis > 0 ? '+' : ''}{basis.toFixed(2)}
                </text>
              </g>
            );
          })}
        </svg>
        
        {/* Legend */}
        <div className="absolute bottom-4 right-4 bg-gray-800/90 p-3 rounded-lg border border-gray-700 text-xs">
          <div className="font-bold text-white mb-2">Basis Differential ($/MMBtu)</div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span>Premium (&gt; Henry Hub)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500"></div>
            <span>Discount (&lt; Henry Hub)</span>
          </div>
        </div>

        {/* Controls */}
        <div className="absolute top-4 left-4 bg-gray-800/90 p-3 rounded-lg border border-gray-700 flex gap-4">
           <div>
             <label className="block text-xs text-gray-400 mb-1">Year</label>
             <select 
               value={year} 
               onChange={(e) => setYear(Number(e.target.value))}
               className="bg-gray-700 text-white text-sm rounded p-1 border-none"
             >
               {[...Array(10)].map((_, i) => (
                 <option key={i} value={2024 - i}>{2024 - i}</option>
               ))}
             </select>
           </div>
           <div>
             <label className="block text-xs text-gray-400 mb-1">Month</label>
             <select 
               value={month} 
               onChange={(e) => setMonth(Number(e.target.value))}
               className="bg-gray-700 text-white text-sm rounded p-1 border-none"
             >
               {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'].map((m, i) => (
                 <option key={i} value={i + 1}>{m}</option>
               ))}
             </select>
           </div>
        </div>
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <DollarSign className="text-green-500" />
            Regional Gas Prices & Basis
          </h2>
          <p className="text-gray-400 text-sm mt-1">Citygate Price vs. Henry Hub Benchmark</p>
        </div>
        
        <div className="flex bg-gray-800 rounded-lg p-1 border border-gray-700">
          <button
            onClick={() => setViewMode('chart')}
            className={`px-3 py-1.5 rounded-md flex items-center space-x-2 text-sm font-medium transition-colors ${
              viewMode === 'chart' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
            }`}
          >
            <TrendingUp size={16} />
            <span>Charts</span>
          </button>
          <button
            onClick={() => setViewMode('map')}
            className={`px-3 py-1.5 rounded-md flex items-center space-x-2 text-sm font-medium transition-colors ${
              viewMode === 'map' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
            }`}
          >
            <MapIcon size={16} />
            <span>Basis Map</span>
          </button>
        </div>
      </div>

      {viewMode === 'chart' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
          {/* Main Chart Area */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            {/* Price History */}
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 flex-1 min-h-0 flex flex-col">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-white">Price History: {selectedState} vs. Henry Hub</h3>
                <select 
                  value={selectedState} 
                  onChange={(e) => setSelectedState(e.target.value)}
                  className="bg-gray-700 text-white text-sm rounded-lg p-2 border-none"
                >
                  {Object.keys(STATE_COORDINATES).sort().map(code => (
                    <option key={code} value={code}>{code}</option>
                  ))}
                </select>
              </div>
              <div className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                    <XAxis 
                      dataKey="date" 
                      stroke="#9ca3af" 
                      fontSize={12} 
                      tickLine={false} 
                      axisLine={false}
                      tickFormatter={(val) => new Date(val).getFullYear().toString()}
                      minTickGap={30}
                    />
                    <YAxis 
                      stroke="#9ca3af" 
                      fontSize={12} 
                      tickLine={false} 
                      axisLine={false} 
                      tickFormatter={(val) => `$${val}`}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }}
                      labelFormatter={(label) => new Date(label).toLocaleDateString()}
                      formatter={(val: number) => [`$${val.toFixed(2)}`, '']}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="henry_hub" name="Henry Hub" stroke="#f59e0b" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="state_price" name={`${selectedState} Citygate`} stroke="#3b82f6" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Basis Differential */}
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 h-64 flex flex-col">
              <h3 className="text-lg font-bold text-white mb-4">Basis Differential ({selectedState} - Henry Hub)</h3>
              <div className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                    <XAxis dataKey="date" hide />
                    <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val}`} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }}
                      labelFormatter={(label) => new Date(label).toLocaleDateString()}
                      formatter={(val: number) => [`$${val.toFixed(2)}`, 'Basis']}
                    />
                    <ReferenceLine y={0} stroke="#9ca3af" />
                    <Bar dataKey="basis" fill="#10b981">
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.basis > 0 ? '#ef4444' : '#3b82f6'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Sidebar Stats */}
          <div className="space-y-6">
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
              <h3 className="text-gray-400 text-sm font-medium mb-4">Current Spread (Latest)</h3>
              <div className="flex items-end gap-2 mb-2">
                <span className="text-4xl font-bold text-white">
                  ${chartData[chartData.length - 1]?.basis.toFixed(2) || '-'}
                </span>
                <span className="text-gray-500 text-sm mb-1">/ MMBtu</span>
              </div>
              <p className="text-sm text-gray-400">
                {selectedState} is trading at a 
                <span className={chartData[chartData.length - 1]?.basis > 0 ? "text-red-400 font-bold mx-1" : "text-blue-400 font-bold mx-1"}>
                  {chartData[chartData.length - 1]?.basis > 0 ? 'PREMIUM' : 'DISCOUNT'}
                </span>
                to Henry Hub.
              </p>
            </div>

            <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
              <h3 className="text-gray-400 text-sm font-medium mb-4">Volatility (12 Month)</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-400">Max Basis</span>
                    <span className="text-red-400 font-mono">
                      ${Math.max(...chartData.slice(-12).map(d => d.basis)).toFixed(2)}
                    </span>
                  </div>
                  <div className="w-full h-1.5 bg-gray-700 rounded-full">
                    <div className="h-full bg-red-500 rounded-full" style={{ width: '80%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-400">Min Basis</span>
                    <span className="text-blue-400 font-mono">
                      ${Math.min(...chartData.slice(-12).map(d => d.basis)).toFixed(2)}
                    </span>
                  </div>
                  <div className="w-full h-1.5 bg-gray-700 rounded-full">
                    <div className="h-full bg-blue-500 rounded-full" style={{ width: '40%' }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 min-h-0">
          {renderMap()}
        </div>
      )}
    </div>
  );
};

export default GasPrices;
