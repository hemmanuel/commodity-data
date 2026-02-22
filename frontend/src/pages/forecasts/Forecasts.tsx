import { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, BarChart2, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const Forecasts = () => {
  const [years, setYears] = useState<string[]>([]);
  const [selectedYear, setSelectedYear] = useState<string>('');
  const [scenarios, setScenarios] = useState<string[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>('all');
  const [selectedMetric, setSelectedMetric] = useState<string>('all');
  const [query, setQuery] = useState('');
  
  const [results, setResults] = useState<any[]>([]);
  const [selectedSeries, setSelectedSeries] = useState<any>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  // Zoom state
  const [zoomDomain, setZoomDomain] = useState<[number, number] | null>(null);

  // Initial fetch of years
  useEffect(() => {
    const fetchYears = async () => {
      try {
        const res = await axios.get('http://localhost:8000/aeo/years');
        setYears(res.data);
        if (res.data.length > 0) setSelectedYear(res.data[0]);
      } catch (err) {
        console.error(err);
      }
    };
    fetchYears();
  }, []);

  // Fetch scenarios when year changes
  useEffect(() => {
    if (!selectedYear) return;
    const fetchScenarios = async () => {
      try {
        const res = await axios.get(`http://localhost:8000/aeo/scenarios/${selectedYear}`);
        setScenarios(res.data);
        setSelectedScenario('all');
      } catch (err) {
        console.error(err);
      }
    };
    fetchScenarios();
  }, [selectedYear]);

  // Fetch series
  const fetchSeries = async (isLoadMore = false, isReset = false) => {
    if (!selectedYear) return;
    
    const currentOffset = isLoadMore ? offset : 0;
    const limit = 50;
    
    if (isLoadMore) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }

    try {
      const params = new URLSearchParams();
      params.append('dataset', selectedYear);
      if (selectedScenario !== 'all') params.append('scenario', selectedScenario);
      if (selectedMetric !== 'all') params.append('metric', selectedMetric);
      if (query) params.append('q', query);
      
      params.append('limit', limit.toString());
      params.append('offset', currentOffset.toString());

      const res = await axios.get(`http://localhost:8000/aeo/search?${params.toString()}`);
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

  // Trigger search on filter changes
  useEffect(() => {
    if (selectedYear) {
      setOffset(0);
      fetchSeries(false, true);
    }
  }, [selectedYear, selectedScenario, selectedMetric]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
    fetchSeries(false, true);
  };

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

  const handleZoom = (direction: 'in' | 'out') => {
    if (!zoomDomain || chartData.length === 0) return;
    const [start, end] = zoomDomain;
    const range = end - start;
    const factor = 0.2;
    const delta = Math.max(1, Math.round(range * factor / 2));

    if (direction === 'in') {
      if (range < 10) return;
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

  const visibleData = (chartData.length > 0 && zoomDomain) ? chartData.slice(zoomDomain[0], zoomDomain[1]) : [];

  return (
    <div className="flex h-[calc(100vh-100px)] gap-6">
      {/* Sidebar / Filters */}
      <div className="w-1/3 flex flex-col space-y-4">
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 space-y-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1 uppercase font-bold">Outlook Year</label>
            <select 
              className="w-full bg-gray-900 text-white border border-gray-600 rounded p-2 text-sm"
              value={selectedYear}
              onChange={(e) => setSelectedYear(e.target.value)}
            >
              {years.map(y => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>
          
          <div>
            <label className="block text-xs text-gray-400 mb-1 uppercase font-bold">Scenario</label>
            <select 
              className="w-full bg-gray-900 text-white border border-gray-600 rounded p-2 text-sm"
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
            >
              <option value="all">All Scenarios</option>
              {scenarios.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1 uppercase font-bold">Metric Type</label>
            <select 
              className="w-full bg-gray-900 text-white border border-gray-600 rounded p-2 text-sm"
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
            >
              <option value="all">All Types</option>
              <option value="capacity">Capacity</option>
              <option value="generation">Generation</option>
              <option value="consumption">Consumption</option>
              <option value="price">Price</option>
              <option value="emissions">Emissions</option>
            </select>
          </div>

          <form onSubmit={handleSearch} className="relative">
            <input
              type="text"
              placeholder="Search projections..."
              className="w-full bg-gray-900 text-white border border-gray-600 rounded py-2 px-4 pl-8 text-sm"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <Search className="absolute left-2.5 top-2.5 text-gray-500" size={14} />
          </form>
        </div>

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
                  <div className="font-medium text-white text-sm line-clamp-2">{series.name}</div>
                  <div className="text-xs text-gray-400 mt-1 flex justify-between">
                    <span>{series.unit}</span>
                    <span className="bg-gray-700 px-1.5 py-0.5 rounded text-[10px]">{series.series_id.split('.')[2]}</span>
                  </div>
                </li>
              ))}
              {loadingMore && (
                <li className="p-4 text-center text-gray-400 text-sm">Loading more...</li>
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
            <div className="mb-6">
              <h2 className="text-xl font-bold text-white">{selectedSeries.name}</h2>
              <div className="flex gap-4 mt-2 text-sm text-gray-400">
                <span className="bg-blue-900/50 text-blue-300 px-2 py-0.5 rounded border border-blue-800">
                  {selectedSeries.series_id.split('.')[2]} Scenario
                </span>
                <span>ID: {selectedSeries.series_id}</span>
                <span>Unit: {selectedSeries.unit}</span>
              </div>
            </div>
            
            <div className="flex-1 min-h-0 relative">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={visibleData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis 
                    dataKey="date" 
                    stroke="#9CA3AF" 
                    tick={{fill: '#9CA3AF'}}
                    tickFormatter={(val) => val.split('-')[0]} 
                  />
                  <YAxis stroke="#9CA3AF" tick={{fill: '#9CA3AF'}} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1F2937', borderColor: '#374151', color: '#F3F4F6' }}
                    labelStyle={{ color: '#9CA3AF' }}
                    formatter={(val: any) => [val.toLocaleString(), selectedSeries.unit]}
                    labelFormatter={(label) => `Year: ${label.split('-')[0]}`}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="value" 
                    name="Projection"
                    stroke="#3B82F6" 
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 8 }}
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
            <p>Select a projection series to view</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Forecasts;
