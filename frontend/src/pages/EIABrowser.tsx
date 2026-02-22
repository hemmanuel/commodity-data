import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, BarChart2, X, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';

const EIABrowser = ({ category }: { category?: string }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [selectedSeries, setSelectedSeries] = useState<any>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  // Reset state when category changes
  useEffect(() => {
    setQuery('');
    setResults([]);
    setSelectedSeries(null);
    setChartData([]);
    setOffset(0);
    setHasMore(true);
    setLoading(true);
    fetchSeries(false, true);
  }, [category]);

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
    if (!zoomDomain || chartData.length === 0) return;
    const [start, end] = zoomDomain;
    const range = end - start;
    const factor = 0.2; // 20% zoom
    const delta = Math.max(1, Math.round(range * factor / 2));

    if (direction === 'in') {
      if (range < 10) return; // Minimum 10 points
      setZoomDomain([start + delta, end - delta]);
    } else {
      const newStart = Math.max(0, start - delta);
      const newEnd = Math.min(chartData.length, end + delta);
      setZoomDomain([newStart, newEnd]);
    }
  };

  const handleResetZoom = () => {
    setZoomDomain([0, chartData.length]);
  };

  const handleWheel = (e: React.WheelEvent) => {
    if (e.deltaY < 0) {
      handleZoom('in');
    } else {
      handleZoom('out');
    }
  };

  const fetchSeries = async (isLoadMore = false, isReset = false) => {
    const currentOffset = isLoadMore ? offset : 0;
    const limit = 50;
    
    if (isLoadMore) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }

    try {
      const params = new URLSearchParams();
      if (query) params.append('q', query);
      if (category) params.append('category', category);
      params.append('limit', limit.toString());
      params.append('offset', currentOffset.toString());

      const res = await axios.get(`http://localhost:8000/eia/search?${params.toString()}`);
      const newData = res.data;

      if (isLoadMore) {
        setResults(prev => [...prev, ...newData]);
      } else {
        setResults(newData);
      }

      setHasMore(newData.length === limit);
      if (!isReset) setOffset(currentOffset + limit);
      else setOffset(limit);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  useEffect(() => {
    // Initial fetch handled by category change effect
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
    fetchSeries(false, true);
  };

  // Infinite scroll handler
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, clientHeight, scrollHeight } = e.currentTarget;
    if (Math.ceil(scrollTop) + clientHeight >= scrollHeight - 50 && hasMore && !loadingMore && !loading) {
      fetchSeries(true, false);
    }
  };

  const handleSelectSeries = async (series: any) => {
    setSelectedSeries(series);
    try {
      const res = await axios.get(`http://localhost:8000/eia/series/${series.series_id}`);
      if (res.data && Array.isArray(res.data.data)) {
        setChartData(res.data.data);
        setZoomDomain([0, res.data.data.length]);
      } else {
        setChartData([]);
        setZoomDomain(null);
      }
    } catch (err) {
      console.error(err);
      setChartData([]);
      setZoomDomain(null);
    }
  };

  const visibleData = (chartData.length > 0 && zoomDomain) ? chartData.slice(zoomDomain[0], zoomDomain[1]) : [];

  return (
    <div className="flex h-[calc(100vh-100px)] gap-6">
      {/* Sidebar / Search */}
      <div className="w-1/3 flex flex-col space-y-4">
        <form onSubmit={handleSearch} className="relative">
          <input
            type="text"
            placeholder={`Search ${category ? category + ' ' : ''}series...`}
            className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg py-3 px-4 pl-10 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <Search className="absolute left-3 top-3.5 text-gray-500" size={18} />
        </form>

        <div 
          className="flex-1 overflow-y-auto bg-gray-800 rounded-lg border border-gray-700"
          onScroll={handleScroll}
        >
          {results.length === 0 && !loading ? (
            <div className="p-4 text-center text-gray-500">No results found</div>
          ) : (
            <ul className="divide-y divide-gray-700">
              {results.map((series) => (
                <li 
                  key={series.series_id}
                  onClick={() => handleSelectSeries(series)}
                  className={`p-4 cursor-pointer hover:bg-gray-700 transition-colors ${
                    selectedSeries?.series_id === series.series_id ? 'bg-blue-900/30 border-l-4 border-blue-500' : ''
                  }`}
                >
                  <div className="font-medium text-white truncate">{series.name}</div>
                  <div className="text-xs text-gray-400 mt-1 flex justify-between">
                    <span>{series.unit}</span>
                    <span>{series.frequency}</span>
                  </div>
                </li>
              ))}
              {loadingMore && (
                <li className="p-4 text-center text-gray-400">Loading more...</li>
              )}
            </ul>
          )}
          {loading && !loadingMore && (
            <div className="p-4 text-center text-gray-400">Loading...</div>
          )}
        </div>
      </div>

      {/* Main Content / Chart */}
      <div className="flex-1 bg-gray-800 rounded-lg border border-gray-700 p-6 flex flex-col">
        {selectedSeries ? (
          <>
            <div className="mb-6 flex justify-between items-start">
              <div>
                <h2 className="text-xl font-bold text-white">{selectedSeries.name}</h2>
                <div className="flex gap-4 mt-2 text-sm text-gray-400">
                  <span>ID: {selectedSeries.series_id}</span>
                  <span>Unit: {selectedSeries.unit}</span>
                  <span>Freq: {selectedSeries.frequency}</span>
                </div>
              </div>
              
              {measureStart && (
                <div className="flex items-center gap-4 bg-blue-900/30 border border-blue-800 rounded-lg px-4 py-2">
                  <div className="text-sm">
                    <span className="text-blue-300 font-medium">Start:</span> {new Date(measureStart.date).toLocaleDateString()}
                    {measureEnd && (
                      <>
                        <span className="text-blue-300 font-medium ml-3">End:</span> {new Date(measureEnd.date).toLocaleDateString()}
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
            </div>
            
            <div className="flex-1 min-h-0 relative" onWheel={handleWheel}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart 
                  data={visibleData}
                  onClick={handleChartClick}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis 
                    dataKey="date" 
                    stroke="#9CA3AF" 
                    tick={{fill: '#9CA3AF'}}
                    tickFormatter={(val) => {
                      try {
                        return new Date(val).toLocaleDateString();
                      } catch {
                        return val;
                      }
                    }}
                  />
                  <YAxis stroke="#9CA3AF" tick={{fill: '#9CA3AF'}} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#F3F4F6' }}
                    labelStyle={{ color: '#9CA3AF' }}
                  />
                  <Legend />
                  
                  {measureStart && (
                    <ReferenceLine x={measureStart.date} stroke="yellow" strokeDasharray="3 3" label="Start" />
                  )}
                  {measureEnd && (
                    <ReferenceLine x={measureEnd.date} stroke="yellow" strokeDasharray="3 3" label="End" />
                  )}
                  
                  <Line 
                    type="monotone" 
                    dataKey="value" 
                    stroke="#3B82F6" 
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 8, onClick: (_, payload) => handleChartClick({ activePayload: [payload] }) }}
                  />
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
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
            <BarChart2 size={48} className="mb-4 opacity-50" />
            <p>Select a series to view historical data</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EIABrowser;
