import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import { X, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

const SERIES = [
  { id: 'EIA_NG_STORAGE_LOWER_48_STATES', name: 'Lower 48 States' },
  { id: 'EIA_NG_STORAGE_EAST_REGION', name: 'East Region' },
  { id: 'EIA_NG_STORAGE_MIDWEST_REGION', name: 'Midwest Region' },
  { id: 'EIA_NG_STORAGE_MOUNTAIN_REGION', name: 'Mountain Region' },
  { id: 'EIA_NG_STORAGE_PACIFIC_REGION', name: 'Pacific Region' },
  { id: 'EIA_NG_STORAGE_SOUTH_CENTRAL_REGION', name: 'South Central Region' },
  { id: 'EIA_NG_STORAGE_SALT_SOUTH_CENTRAL_REGION', name: 'Salt South Central' },
  { id: 'EIA_NG_STORAGE_NONSALT_SOUTH_CENTRAL_REGION', name: 'Nonsalt South Central' }
];

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#14b8a6'];

const NaturalGasStorage = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'chart' | 'table'>('chart');
  
  // Zoom state
  const [zoomDomain, setZoomDomain] = useState<[number, number] | null>(null);

  // Measurement state
  const [measureStart, setMeasureStart] = useState<any>(null);
  const [measureEnd, setMeasureEnd] = useState<any>(null);

  const handleChartClick = (e: any) => {
    if (!e || !e.activePayload) return;
    const point = e.activePayload[0].payload;
    
    if (!measureStart) {
      setMeasureStart(point);
      setMeasureEnd(null);
    } else if (!measureEnd) {
      setMeasureEnd(point);
    } else {
      setMeasureStart(point);
      setMeasureEnd(null);
    }
  };

  const clearMeasurement = () => {
    setMeasureStart(null);
    setMeasureEnd(null);
  };

  const handleZoom = (direction: 'in' | 'out') => {
    if (!zoomDomain || data.length === 0) return;
    const [start, end] = zoomDomain;
    const range = end - start;
    const factor = 0.2; // 20% zoom
    const delta = Math.max(1, Math.round(range * factor / 2));

    if (direction === 'in') {
      if (range < 10) return; // Minimum 10 points
      setZoomDomain([start + delta, end - delta]);
    } else {
      const newStart = Math.max(0, start - delta);
      const newEnd = Math.min(data.length, end + delta);
      setZoomDomain([newStart, newEnd]);
    }
  };

  const handleResetZoom = () => {
    setZoomDomain([0, data.length]);
  };

  const handleWheel = (e: React.WheelEvent) => {
    if (viewMode !== 'chart') return;
    // Prevent default scroll if needed, but wheel event is passive by default in React 18+
    if (e.deltaY < 0) {
      handleZoom('in');
    } else {
      handleZoom('out');
    }
  };

  useEffect(() => {
    const fetchStorageData = async () => {
      try {
        setLoading(true);
        const promises = SERIES.map(s => 
          axios.get(`http://localhost:8000/eia/series/${s.id}`).catch(() => null)
        );
        const results = await Promise.all(promises);
        
        const dateMap = new Map<string, any>();
        
        results.forEach((res, idx) => {
          if (!res?.data?.data) return;
          const seriesId = SERIES[idx].id;
          
          res.data.data.forEach((point: any) => {
            if (!dateMap.has(point.date)) {
              dateMap.set(point.date, { date: point.date });
            }
            const existing = dateMap.get(point.date);
            existing[seriesId] = point.value;
          });
        });

        const mergedData = Array.from(dateMap.values()).sort((a, b) => 
          new Date(a.date).getTime() - new Date(b.date).getTime()
        );
        
        setData(mergedData);
        setZoomDomain([0, mergedData.length]);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchStorageData();
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-gray-400 text-lg">Loading Natural Gas Storage Data...</div>;
  }

  if (data.length === 0) {
    return <div className="p-8 text-center text-red-400">No storage data found. Ingestion may have failed.</div>;
  }

  const latestPoint = data[data.length - 1]; // because it's sorted ASC now

  const visibleData = data.length > 0 && zoomDomain ? data.slice(zoomDomain[0], zoomDomain[1]) : [];

  return (
    <div className="flex h-[calc(100vh-100px)] flex-col gap-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-white">EIA Weekly Natural Gas Storage</h2>
          <p className="text-sm text-gray-400 mt-1">Sourced from EIA NG_STOR_WKLY_S1_W.xls</p>
        </div>
        
        <div className="flex items-center gap-6">
          {measureStart && (
            <div className="flex items-center gap-4 bg-blue-900/30 border border-blue-800 rounded-lg px-4 py-2">
              <div className="text-sm">
                <span className="text-blue-300 font-medium">Start:</span> {measureStart.date}
                {measureEnd && (
                  <>
                    <span className="text-blue-300 font-medium ml-3">End:</span> {measureEnd.date}
                    <span className="text-blue-300 font-medium ml-3">Diff:</span> {
                      Math.round((new Date(measureEnd.date).getTime() - new Date(measureStart.date).getTime()) / (1000 * 60 * 60 * 24))
                    } days
                  </>
                )}
              </div>
              <button onClick={clearMeasurement} className="text-blue-400 hover:text-white">
                <X size={16} />
              </button>
            </div>
          )}
          
          <div className="flex bg-gray-800 rounded-lg p-1 border border-gray-700">
            <button 
              className={`px-4 py-2 rounded text-sm font-medium transition-colors ${viewMode === 'chart' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
              onClick={() => setViewMode('chart')}
            >
              Chart View
            </button>
            <button 
              className={`px-4 py-2 rounded text-sm font-medium transition-colors ${viewMode === 'table' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
              onClick={() => setViewMode('table')}
            >
              Table View
            </button>
          </div>
          
          <div className="bg-gray-800 border border-gray-700 rounded-lg px-6 py-2 text-right">
            <div className="text-xs text-gray-400">Latest (Lower 48) - {latestPoint?.date}</div>
            <div className="text-xl font-bold text-blue-400">
              {latestPoint?.EIA_NG_STORAGE_LOWER_48_STATES?.toLocaleString() || 'N/A'} Bcf
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 bg-gray-800 rounded-lg border border-gray-700 p-6 min-h-0 overflow-hidden flex flex-col relative" onWheel={handleWheel}>
        {viewMode === 'chart' ? (
          <>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart 
                data={visibleData}
                onClick={handleChartClick}
              >
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="date" 
                stroke="#9ca3af" 
                tick={{fill: '#9ca3af'}} 
                tickFormatter={(val) => {
                  if (!val) return '';
                  const d = new Date(val);
                  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2, '0')}`;
                }}
                minTickGap={50}
              />
              <YAxis 
                stroke="#9ca3af" 
                tick={{fill: '#9ca3af'}}
                domain={['auto', 'auto']}
                tickFormatter={(val) => val.toLocaleString()}
              />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '0.5rem', color: '#f3f4f6' }}
                itemStyle={{ color: '#e5e7eb' }}
                labelStyle={{ color: '#9ca3af', marginBottom: '0.5rem' }}
                formatter={(value: any, name: any) => {
                  const s = SERIES.find(s => s.id === name);
                  return [value?.toLocaleString() + ' Bcf', s?.name || name];
                }}
              />
              <Legend 
                formatter={(value) => {
                  const s = SERIES.find(s => s.id === value);
                  return <span className="text-gray-300">{s?.name || value}</span>;
                }}
              />
              
              {measureStart && (
                <ReferenceLine x={measureStart.date} stroke="yellow" strokeDasharray="3 3" label="Start" />
              )}
              {measureEnd && (
                <ReferenceLine x={measureEnd.date} stroke="yellow" strokeDasharray="3 3" label="End" />
              )}
              
              {SERIES.map((s, idx) => (
                <Line 
                  key={s.id}
                  type="monotone" 
                  dataKey={s.id} 
                  stroke={COLORS[idx % COLORS.length]} 
                  dot={false}
                  strokeWidth={s.id === 'EIA_NG_STORAGE_LOWER_48_STATES' ? 3 : 1.5}
                  opacity={s.id === 'EIA_NG_STORAGE_LOWER_48_STATES' ? 1 : 0.7}
                  activeDot={{ r: 6, onClick: (_, payload) => handleChartClick({ activePayload: [payload] }) }}
                />
              ))}
              </LineChart>
            </ResponsiveContainer>
            
            {/* Zoom Controls Overlay */}
            <div className="absolute bottom-8 right-8 flex gap-2 bg-gray-900/80 p-2 rounded-lg border border-gray-700 backdrop-blur-sm">
              <button 
                onClick={() => handleZoom('in')} 
                className="p-2 bg-gray-800 text-gray-300 hover:text-white hover:bg-gray-700 rounded transition-colors"
                title="Zoom In"
              >
                <ZoomIn size={20} />
              </button>
              <button 
                onClick={() => handleZoom('out')} 
                className="p-2 bg-gray-800 text-gray-300 hover:text-white hover:bg-gray-700 rounded transition-colors"
                title="Zoom Out"
              >
                <ZoomOut size={20} />
              </button>
              <button 
                onClick={handleResetZoom} 
                className="p-2 bg-gray-800 text-gray-300 hover:text-white hover:bg-gray-700 rounded transition-colors"
                title="Reset Zoom"
              >
                <RotateCcw size={20} />
              </button>
            </div>
          </>
        ) : (
          <div className="overflow-auto flex-1">
            <table className="w-full text-left text-sm text-gray-400 whitespace-nowrap">
              <thead className="bg-gray-900 text-gray-200 uppercase font-medium sticky top-0 z-10">
                <tr>
                  <th className="px-4 py-3">Date</th>
                  {SERIES.map(s => (
                    <th key={s.id} className="px-4 py-3 text-right">{s.name}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {data.slice().reverse().map((row) => (
                  <tr key={row.date} className="hover:bg-gray-700 transition-colors">
                    <td className="px-4 py-3 font-mono text-white">{row.date}</td>
                    {SERIES.map(s => (
                      <td key={s.id} className="px-4 py-3 text-right font-mono">
                        {row[s.id]?.toLocaleString() || '—'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default NaturalGasStorage;
