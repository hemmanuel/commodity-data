import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Search, Factory, Zap, Flame, X, Activity } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const PlantBrowser = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [selectedPlant, setSelectedPlant] = useState<any>(null);
  const [plantDetails, setPlantDetails] = useState<any>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  const fetchPlants = async (isLoadMore = false, isReset = false) => {
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
      params.append('limit', limit.toString());
      params.append('offset', currentOffset.toString());

      const res = await axios.get(`http://localhost:8000/plants/search?${params.toString()}`);
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
    fetchPlants();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
    fetchPlants(false, true);
  };

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, clientHeight, scrollHeight } = e.currentTarget;
    if (Math.ceil(scrollTop) + clientHeight >= scrollHeight - 50 && hasMore && !loadingMore && !loading) {
      fetchPlants(true, false);
    }
  };

  const handleSelectPlant = async (plant: any) => {
    setSelectedPlant(plant);
    setLoadingDetails(true);
    setPlantDetails(null);
    try {
      const res = await axios.get(`http://localhost:8000/plants/${plant.plant_id}`);
      setPlantDetails(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDetails(false);
    }
  };

  // Helper to format large numbers
  const formatNumber = (num: number) => {
    if (!num) return '-';
    return num.toLocaleString(undefined, { maximumFractionDigits: 0 });
  };

  return (
    <div className="h-[calc(100vh-100px)] flex gap-6">
      {/* List Pane */}
      <div className={`flex flex-col space-y-6 transition-all duration-300 ${selectedPlant ? 'w-1/3' : 'w-full'}`}>
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <Factory className="text-blue-500" />
            Plant Browser
          </h2>
          <form onSubmit={handleSearch} className="relative flex-1 ml-4">
            <input
              type="text"
              placeholder="Search plants..."
              className="w-full bg-gray-800 text-white border border-gray-700 rounded-lg py-2 px-4 pl-10 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <Search className="absolute left-3 top-2.5 text-gray-500" size={18} />
          </form>
        </div>

        <div className="flex-1 bg-gray-800 rounded-lg border border-gray-700 overflow-hidden flex flex-col">
          <div className="overflow-auto flex-1" onScroll={handleScroll}>
            <div className="divide-y divide-gray-700">
              {results.map((plant) => (
                <div 
                  key={plant.plant_id} 
                  onClick={() => handleSelectPlant(plant)}
                  className={`p-4 hover:bg-gray-700 transition-colors cursor-pointer ${selectedPlant?.plant_id === plant.plant_id ? 'bg-blue-900/20 border-l-4 border-blue-500' : 'border-l-4 border-transparent'}`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-medium text-white text-lg">{plant.name}</div>
                      <div className="text-sm text-gray-400 mt-1 flex items-center gap-2">
                        <span className="bg-gray-700 px-2 py-0.5 rounded text-xs">ID: {plant.plant_id}</span>
                        <span>{plant.state}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-blue-400">{plant.primary_fuel}</div>
                      <div className="text-xs text-gray-500">{plant.technology}</div>
                    </div>
                  </div>
                </div>
              ))}
              {loadingMore && (
                <div className="p-4 text-center text-gray-500">Loading more...</div>
              )}
            </div>
            
            {loading && !loadingMore && (
              <div className="p-12 text-center text-gray-500">Loading plants...</div>
            )}
            
            {!loading && results.length === 0 && (
              <div className="p-12 text-center text-gray-500">No plants found matching your search.</div>
            )}
          </div>
        </div>
      </div>

      {/* Detail Pane */}
      {selectedPlant && (
        <div className="flex-1 bg-gray-800 rounded-lg border border-gray-700 flex flex-col overflow-hidden animate-in slide-in-from-right-4 duration-300">
          <div className="p-6 border-b border-gray-700 flex justify-between items-start bg-gray-900/50">
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">{selectedPlant.name}</h2>
              <div className="flex gap-4 text-sm text-gray-400">
                <div className="flex items-center gap-1"><Factory size={16} /> {selectedPlant.state}</div>
                <div className="flex items-center gap-1"><Flame size={16} /> {selectedPlant.primary_fuel}</div>
                <div className="flex items-center gap-1"><Zap size={16} /> {selectedPlant.technology}</div>
              </div>
            </div>
            <button 
              onClick={() => setSelectedPlant(null)}
              className="text-gray-400 hover:text-white p-1 hover:bg-gray-700 rounded"
            >
              <X size={24} />
            </button>
          </div>

          {loadingDetails ? (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              Loading details...
            </div>
          ) : plantDetails ? (
            <div className="flex-1 overflow-y-auto p-6 space-y-8">
              
              {/* Generation History Chart */}
              {plantDetails.generation_history && plantDetails.generation_history.length > 0 && (
                <div className="bg-gray-900/30 p-4 rounded-xl border border-gray-700">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Activity className="text-green-500" />
                    Annual Generation (MWh)
                  </h3>
                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={plantDetails.generation_history}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis dataKey="year" stroke="#9ca3af" />
                        <YAxis stroke="#9ca3af" />
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }}
                          formatter={(value: number) => [formatNumber(value), 'MWh']}
                        />
                        <Legend />
                        <Line type="monotone" dataKey="net_generation_mwh" name="Net Gen (MWh)" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* Generators Table */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Zap className="text-yellow-500" />
                  Generators ({plantDetails.generators?.length || 0})
                </h3>
                <div className="overflow-x-auto rounded-lg border border-gray-700">
                  <table className="w-full text-left text-sm text-gray-400">
                    <thead className="bg-gray-900 text-gray-200 uppercase font-medium">
                      <tr>
                        <th className="px-4 py-3">ID</th>
                        <th className="px-4 py-3">Tech</th>
                        <th className="px-4 py-3">Prime Mover</th>
                        <th className="px-4 py-3">Fuel</th>
                        <th className="px-4 py-3 text-right">Capacity (MW)</th>
                        <th className="px-4 py-3 text-center">Status</th>
                        <th className="px-4 py-3 text-right">Operating Year</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700 bg-gray-800/50">
                      {plantDetails.generators?.map((gen: any, idx: number) => (
                        <tr key={idx} className="hover:bg-gray-700/50">
                          <td className="px-4 py-3 font-mono text-white">{gen.generator_id}</td>
                          <td className="px-4 py-3">{gen.technology}</td>
                          <td className="px-4 py-3">{gen.prime_mover}</td>
                          <td className="px-4 py-3">{gen.primary_fuel}</td>
                          <td className="px-4 py-3 text-right font-mono text-white">{gen.nameplate_capacity_mw}</td>
                          <td className="px-4 py-3 text-center">
                            <span className={`px-2 py-0.5 rounded text-xs ${gen.status === 'OP' ? 'bg-green-900/50 text-green-400 border border-green-800' : 'bg-gray-700 text-gray-400'}`}>
                              {gen.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right font-mono">{gen.operating_year}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              Select a plant to view details
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PlantBrowser;
