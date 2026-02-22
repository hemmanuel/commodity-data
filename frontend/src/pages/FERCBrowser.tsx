import React, { useEffect, useState, useRef, useCallback } from 'react';
import axios from 'axios';
import { Search, Calendar, ChevronRight, X } from 'lucide-react';

const FERCBrowser = () => {
  const [respondents, setRespondents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [yearFilter, setYearFilter] = useState<string>('all');
  const [years, setYears] = useState<number[]>([]);
  const [selectedRespondent, setSelectedRespondent] = useState<any>(null);
  const [respondentData, setRespondentData] = useState<any>({});
  const [activeTab, setActiveTab] = useState('income_statement');
  const [sortBy, setSortBy] = useState<'name' | 'year'>('name');
  
  // Infinite scroll state
  const [hasMore, setHasMore] = useState(true);
  const [isFetching, setIsFetching] = useState(false);
  const offsetRef = useRef(0);
  
  // Ref to track if component is mounted
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    const fetchYears = async () => {
      try {
        const res = await axios.get('http://localhost:8000/ferc/years');
        if (isMounted.current) setYears(res.data);
      } catch (err) {
        console.error(err);
      }
    };
    fetchYears();
    return () => { isMounted.current = false; };
  }, []);

  const fetchRespondents = useCallback(async (reset = false) => {
    if (isFetching && !reset) return;
    setIsFetching(true);
    
    try {
      const limit = 100;
      const currentOffset = reset ? 0 : offsetRef.current;
      
      const params = new URLSearchParams();
      if (yearFilter !== 'all') params.append('year', yearFilter);
      if (search) params.append('search', search);
      params.append('sort', sortBy);
      params.append('limit', limit.toString());
      params.append('offset', currentOffset.toString());

      const res = await axios.get(`http://localhost:8000/ferc/respondents?${params.toString()}`);
      
      if (!isMounted.current) return;

      const newData = res.data || [];
      
      if (reset) {
        setRespondents(newData);
        offsetRef.current = limit;
      } else {
        setRespondents(prev => [...prev, ...newData]);
        offsetRef.current += limit;
      }
      
      setHasMore(newData.length === limit);
    } catch (err) {
      console.error(err);
    } finally {
      if (isMounted.current) {
        setIsFetching(false);
        setLoading(false);
      }
    }
  }, [yearFilter, search, sortBy, isFetching]);

  // Initial fetch and filter changes
  useEffect(() => {
    setLoading(true);
    const timeoutId = setTimeout(() => {
      offsetRef.current = 0;
      fetchRespondents(true);
    }, 300);
    return () => clearTimeout(timeoutId);
  }, [yearFilter, search, sortBy]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, clientHeight, scrollHeight } = e.currentTarget;
    // Load more when user is 100px from bottom
    if (scrollHeight - scrollTop <= clientHeight + 100 && hasMore && !isFetching) {
      fetchRespondents(false);
    }
  };

  const handleSelectRespondent = async (respondent: any) => {
    setSelectedRespondent(respondent);
    setRespondentData({}); 
    try {
      const yearParam = respondent?.year ?? yearFilter;
      const res = await axios.get(`http://localhost:8000/ferc/data/${respondent.respondent_id}?year=${yearParam}`);
      if (isMounted.current) setRespondentData(res.data);
    } catch (err) {
      console.error(err);
      if (isMounted.current) setRespondentData({});
    }
  };

  const renderDetailTable = (data: any[]) => {
    if (!data || data.length === 0) return <div className="text-center text-gray-500 py-12">No data available for this section.</div>;

    return (
      <div className="overflow-auto h-full">
        <table className="w-full text-left text-sm text-gray-400">
          <thead className="bg-gray-900 text-gray-200 uppercase font-medium sticky top-0 z-10">
            <tr>
              <th className="px-6 py-3 w-16">Row</th>
              <th className="px-6 py-3">Description</th>
              <th className="px-6 py-3 text-right">Current Year</th>
              <th className="px-6 py-3 text-right">Prior Year</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {data.map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-700/50">
                <td className="px-6 py-3 font-mono text-xs text-gray-500">{row.row_number}</td>
                <td className="px-6 py-3 text-white">{row.description || <span className="text-gray-600 italic">Unknown</span>}</td>
                <td className="px-6 py-3 text-right font-mono text-white">
                  {(row.current_year_total || row.current_year_end_balance || row.current_year)?.toLocaleString()}
                </td>
                <td className="px-6 py-3 text-right font-mono">
                  {(row.prev_year_total || row.prev_year_end_balance || row.prev_year)?.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const formatTabName = (name: string) => {
    return name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  return (
    <div className="flex h-[calc(100vh-100px)] gap-6 relative">
      {/* Main List View */}
      <div className={`flex-1 flex flex-col bg-gray-800 rounded-lg border border-gray-700 overflow-hidden transition-all duration-300 ${selectedRespondent ? 'w-1/3' : 'w-full'}`}>
        {/* Header / Filters */}
        <div className="p-4 border-b border-gray-700 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold text-white">FERC Form 2 / 2A Respondents</h2>
            <div className="text-sm text-gray-400">
              {respondents.length} loaded
            </div>
          </div>
          
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 text-gray-500" size={18} />
              <input
                type="text"
                placeholder="Search companies..."
                className="w-full bg-gray-900 text-white border border-gray-600 rounded-lg py-2 px-4 pl-10 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            
            <div className="relative w-32">
              <Calendar className="absolute left-2.5 top-2.5 text-gray-500" size={16} />
              <select
                className="w-full bg-gray-900 text-white border border-gray-600 rounded-lg py-2 pl-9 pr-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none"
                value={yearFilter}
                onChange={(e) => setYearFilter(e.target.value)}
              >
                <option value="all">All Years</option>
                {years.map(y => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>

            <div className="flex rounded-lg overflow-hidden border border-gray-600">
              <button
                className={`px-3 py-2 text-xs font-medium ${sortBy === 'name' ? 'bg-blue-600 text-white' : 'bg-gray-900 text-gray-400 hover:text-white'}`}
                onClick={() => setSortBy('name')}
              >
                Name
              </button>
              <button
                className={`px-3 py-2 text-xs font-medium ${sortBy === 'year' ? 'bg-blue-600 text-white' : 'bg-gray-900 text-gray-400 hover:text-white'}`}
                onClick={() => setSortBy('year')}
              >
                Year
              </button>
            </div>
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto" onScroll={handleScroll}>
          <div className="flex items-center px-6 py-2 bg-gray-900/50 border-b border-gray-700 text-xs font-medium text-gray-400 uppercase sticky top-0 z-10 backdrop-blur-sm">
            <div className="flex-1">Name</div>
            <div className="w-20">Year</div>
            <div className="w-8"></div>
          </div>
          
          <div className="divide-y divide-gray-700">
            {respondents.map((r, idx) => (
              <div 
                key={`${r.respondent_id}-${r.year}-${idx}`}
                onClick={() => handleSelectRespondent(r)}
                className={`flex items-center px-6 py-3 hover:bg-gray-700 cursor-pointer transition-colors ${
                  selectedRespondent?.respondent_id === r.respondent_id && selectedRespondent?.year === r.year 
                    ? 'bg-blue-900/20 border-l-4 border-l-blue-500' 
                    : 'border-l-4 border-l-transparent'
                }`}
              >
                <div className="flex-1 font-medium text-white truncate pr-4">{r.respondent_name}</div>
                <div className="w-20 text-gray-400 text-sm">{r.year}</div>
                <div className="w-8 text-gray-500"><ChevronRight size={16} /></div>
              </div>
            ))}
            
            {isFetching && (
              <div className="p-4 text-center text-gray-500 text-sm">
                Loading more...
              </div>
            )}
            
            {!hasMore && respondents.length > 0 && (
              <div className="p-4 text-center text-gray-600 text-sm">
                End of list
              </div>
            )}
            
            {!loading && respondents.length === 0 && (
              <div className="p-12 text-center text-gray-500">
                No respondents found matching your criteria.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Detail Drawer */}
      {selectedRespondent && (
        <div className="w-2/3 bg-gray-800 rounded-lg border border-gray-700 flex flex-col shadow-xl animate-in slide-in-from-right-4 duration-200">
          <div className="flex items-start justify-between p-6 border-b border-gray-700 bg-gray-900/30">
            <div>
              <h2 className="text-2xl font-bold text-white mb-1">{selectedRespondent.respondent_name}</h2>
              <div className="flex items-center gap-3 text-sm text-gray-400">
                <span className="bg-blue-900/50 text-blue-300 px-2 py-0.5 rounded border border-blue-800">
                  ID: {selectedRespondent.respondent_id}
                </span>
                <span className="bg-gray-700 text-gray-300 px-2 py-0.5 rounded">
                  Year: {selectedRespondent.year}
                </span>
              </div>
              {(selectedRespondent.address || selectedRespondent.city) && (
                <div className="mt-3 text-sm text-gray-500 flex items-center gap-2">
                  <div className="w-1 h-1 rounded-full bg-gray-500"></div>
                  {[selectedRespondent.address, selectedRespondent.city, selectedRespondent.state, selectedRespondent.zip].filter(Boolean).join(', ')}
                </div>
              )}
            </div>
            <button 
              onClick={() => setSelectedRespondent(null)}
              className="text-gray-400 hover:text-white p-1 hover:bg-gray-700 rounded transition-colors"
            >
              <X size={24} />
            </button>
          </div>

          <div className="flex border-b border-gray-700 bg-gray-900/20 px-2 overflow-x-auto">
            {['income_statement', 'balance_sheet_assets', 'balance_sheet_liabilities', 'cash_flow'].map(tab => (
              <button
                key={tab}
                className={`px-6 py-3 text-sm font-medium transition-colors whitespace-nowrap border-b-2 ${
                  activeTab === tab 
                    ? 'text-blue-400 border-blue-400 bg-blue-900/10' 
                    : 'text-gray-400 border-transparent hover:text-gray-200 hover:bg-gray-800/50'
                }`}
                onClick={() => setActiveTab(tab)}
              >
                {formatTabName(tab)}
              </button>
            ))}
          </div>

          <div className="flex-1 min-h-0 bg-gray-900/10">
            {renderDetailTable(respondentData[activeTab])}
          </div>
        </div>
      )}
    </div>
  );
};

export default FERCBrowser;
