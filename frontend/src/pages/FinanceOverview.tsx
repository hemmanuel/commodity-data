import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { DollarSign, TrendingUp, Activity, BarChart2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

const Finance = () => {
  const [pipelineRankings, setPipelineRankings] = useState<any[]>([]);
  const [marketSummary, setMarketSummary] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [year, setYear] = useState<number | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // 1. Market Summary (Volume)
        const summaryRes = await axios.get('http://localhost:8000/financials/gas/market-summary');
        setMarketSummary(summaryRes.data);
        
        // Determine latest year
        const latestYear = year || (summaryRes.data.length > 0 ? Math.max(...summaryRes.data.map((d: any) => d.year)) : 2023);
        if (!year) setYear(latestYear);

        // 2. Pipeline Rankings (Revenue)
        // Note: FERC 2 data might lag behind FERC 552. We'll try the same year, or fallback.
        try {
            const rankRes = await axios.get(`http://localhost:8000/financials/pipelines/rankings?year=${latestYear}&limit=5`);
            setPipelineRankings(rankRes.data.rankings);
        } catch (e) {
            // If current year fails (e.g. 2024 not out yet), try previous
            const rankRes = await axios.get(`http://localhost:8000/financials/pipelines/rankings?year=${latestYear - 1}&limit=5`);
            setPipelineRankings(rankRes.data.rankings);
        }

      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [year]);

  if (loading && marketSummary.length === 0) {
    return <div className="p-8 text-center text-gray-400">Loading Financial Dashboard...</div>;
  }

  return (
    <div className="h-full flex flex-col space-y-6">
      <div className="flex justify-between items-center border-b border-gray-700 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <DollarSign className="text-green-500" />
            Financial Dashboard
          </h2>
          <p className="text-gray-400 text-sm mt-1">Market Liquidity, Infrastructure Revenue & Pricing</p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-gray-400 text-sm">Select Year:</span>
          <select 
            value={year || ''} 
            onChange={(e) => setYear(Number(e.target.value))}
            className="bg-gray-800 text-white border border-gray-700 rounded-lg p-2 focus:ring-2 focus:ring-blue-500"
          >
            {marketSummary.map((d: any) => (
              <option key={d.year} value={d.year}>{d.year}</option>
            ))}
          </select>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-gray-400 text-sm font-medium">Total Physical Volume</h3>
            <Activity className="text-blue-500" size={20} />
          </div>
          <p className="text-3xl font-bold text-white">
            {marketSummary.find((d: any) => d.year === year)?.total_sales?.toLocaleString() || '-'} <span className="text-lg text-gray-500 font-normal">TBtu</span>
          </p>
          <div className="text-xs text-gray-500 mt-2">FERC Form 552 Reported Sales</div>
        </div>

        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-gray-400 text-sm font-medium">Top Pipeline Revenue</h3>
            <DollarSign className="text-green-500" size={20} />
          </div>
          <p className="text-3xl font-bold text-white">
            ${(pipelineRankings[0]?.operating_revenues / 1000000000)?.toFixed(2) || '-'} <span className="text-lg text-gray-500 font-normal">B</span>
          </p>
          <div className="text-xs text-gray-500 mt-2">
            {pipelineRankings[0]?.name || 'Loading...'} (Operating Rev)
          </div>
        </div>

        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-gray-400 text-sm font-medium">Active Traders</h3>
            <TrendingUp className="text-purple-500" size={20} />
          </div>
          <p className="text-3xl font-bold text-white">
            {marketSummary.find((d: any) => d.year === year)?.respondent_count || '-'}
          </p>
          <div className="text-xs text-gray-500 mt-2">Companies Reporting Transactions</div>
        </div>
      </div>

      {/* Main Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 min-h-0">
        
        {/* Market Liquidity Trend */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 flex flex-col">
          <h3 className="text-lg font-bold text-white mb-4">Market Liquidity Trend (Physical Sales)</h3>
          <div className="flex-1 w-full min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={marketSummary}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                <XAxis dataKey="year" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `${val/1000}k`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }}
                  formatter={(val: number) => [`${val.toLocaleString()} TBtu`, 'Volume']}
                />
                <Line type="monotone" dataKey="total_sales" stroke="#3b82f6" strokeWidth={3} dot={false} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Pipelines by Revenue */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 flex flex-col">
          <h3 className="text-lg font-bold text-white mb-4">Top Pipelines by Operating Revenue</h3>
          <div className="flex-1 w-full min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pipelineRankings} layout="vertical" margin={{ top: 5, right: 30, left: 60, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
                <XAxis type="number" stroke="#9ca3af" tickFormatter={(val) => `$${val/1000000000}B`} />
                <YAxis dataKey="name" type="category" width={150} stroke="#9ca3af" style={{ fontSize: '11px' }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }}
                  formatter={(val: number) => [`$${(val/1000000).toLocaleString()} M`, 'Revenue']}
                />
                <Bar dataKey="operating_revenues" fill="#10b981" radius={[0, 4, 4, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Finance;
