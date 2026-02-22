import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Search, TrendingUp, BarChart2, PieChart, Activity } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, PieChart as RePie, Pie, Cell } from 'recharts';

const Form552Browser = () => {
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [marketSummary, setMarketSummary] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [year, setYear] = useState<number | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      try {
        // Fetch Market Summary (History)
        const summaryRes = await axios.get('http://localhost:8000/financials/gas/market-summary');
        setMarketSummary(summaryRes.data);

        // Determine latest year if not set
        const latestYear = year || (summaryRes.data.length > 0 ? Math.max(...summaryRes.data.map((d: any) => d.year)) : 2023);
        if (!year) setYear(latestYear);

        // Fetch Leaderboard for specific year
        const leaderboardRes = await axios.get(`http://localhost:8000/financials/gas/top-traders?year=${latestYear}&limit=15`);
        setLeaderboard(leaderboardRes.data.traders);

      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [year]);

  // Colors for charts
  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  if (loading && marketSummary.length === 0) {
    return <div className="p-8 text-center text-gray-400">Loading Financial Data...</div>;
  }

  return (
    <div className="space-y-6 h-full flex flex-col overflow-y-auto pr-2">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Activity className="text-green-500" />
            Physical Gas Transactions (FERC 552)
          </h2>
          <p className="text-gray-400 text-sm mt-1">Annual Report of Natural Gas Transactions</p>
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

      {/* Top Level Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-gray-400 text-sm font-medium mb-2">Total Market Volume ({year})</h3>
          <p className="text-3xl font-bold text-white">
            {marketSummary.find((d: any) => d.year === year)?.total_sales?.toLocaleString() || '-'} <span className="text-lg text-gray-500 font-normal">TBtu</span>
          </p>
          <div className="text-xs text-gray-500 mt-2">Physical Sales Reported</div>
        </div>
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-gray-400 text-sm font-medium mb-2">Active Traders</h3>
          <p className="text-3xl font-bold text-blue-400">
            {marketSummary.find((d: any) => d.year === year)?.respondent_count || '-'}
          </p>
          <div className="text-xs text-gray-500 mt-2">Reporting Companies</div>
        </div>
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-gray-400 text-sm font-medium mb-2">Market Liquidity Trend</h3>
          <div className="h-12 w-full">
             <ResponsiveContainer width="100%" height="100%">
                <LineChart data={marketSummary}>
                   <Line type="monotone" dataKey="total_sales" stroke="#10b981" strokeWidth={2} dot={false} />
                </LineChart>
             </ResponsiveContainer>
          </div>
          <div className="text-xs text-green-500 mt-2 flex items-center gap-1">
             <TrendingUp size={12} /> Volume Trend
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 min-h-0">
        {/* Leaderboard */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 flex flex-col overflow-hidden">
          <div className="p-6 border-b border-gray-700">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <BarChart2 size={20} className="text-blue-500" />
              Top Traders by Volume ({year})
            </h3>
          </div>
          <div className="flex-1 overflow-y-auto p-0">
            <table className="w-full text-left text-sm text-gray-300">
              <thead className="bg-gray-900/50 text-xs uppercase text-gray-500 sticky top-0">
                <tr>
                  <th className="px-6 py-3 font-medium">Rank</th>
                  <th className="px-6 py-3 font-medium">Company</th>
                  <th className="px-6 py-3 text-right font-medium">Sales (TBtu)</th>
                  <th className="px-6 py-3 text-right font-medium">Purchases (TBtu)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700/50">
                {leaderboard.map((trader, idx) => (
                  <tr key={idx} className="hover:bg-gray-700/30 transition-colors">
                    <td className="px-6 py-4 font-mono text-gray-500">#{idx + 1}</td>
                    <td className="px-6 py-4 font-medium text-white">{trader.name}</td>
                    <td className="px-6 py-4 text-right font-mono text-green-400">{trader.sales.toLocaleString()}</td>
                    <td className="px-6 py-4 text-right font-mono text-blue-400">{trader.purchases.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Charts */}
        <div className="flex flex-col gap-6">
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 flex-1">
            <h3 className="text-lg font-bold text-white mb-4">Market Volume History</h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={marketSummary}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                  <XAxis dataKey="year" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `${val/1000}k`} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }}
                    cursor={{ fill: '#374151', opacity: 0.4 }}
                  />
                  <Legend />
                  <Bar dataKey="total_sales" name="Total Sales" fill="#10b981" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="total_purchases" name="Total Purchases" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 flex-1">
             <h3 className="text-lg font-bold text-white mb-4">Top 5 Market Share ({year})</h3>
             <div className="h-64 w-full flex">
                <ResponsiveContainer width="100%" height="100%">
                   <RePie data={leaderboard.slice(0, 5)} dataKey="total" nameKey="name" cx="50%" cy="50%" outerRadius={80}>
                      {leaderboard.slice(0, 5).map((entry, index) => (
                         <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                      <Tooltip contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }} />
                   </RePie>
                </ResponsiveContainer>
                <div className="flex flex-col justify-center gap-2 text-xs text-gray-300 w-1/2">
                   {leaderboard.slice(0, 5).map((entry, index) => (
                      <div key={index} className="flex items-center gap-2">
                         <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></div>
                         <span className="truncate" title={entry.name}>{entry.name}</span>
                      </div>
                   ))}
                </div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Form552Browser;
