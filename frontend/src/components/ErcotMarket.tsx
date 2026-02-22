import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const ErcotMarket = () => {
  const [points, setPoints] = useState<any[]>([]);
  const [selectedPoint, setSelectedPoint] = useState<string>('');
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Fetch available points
    fetch('http://localhost:8000/financials/ercot/points')
      .then(res => res.json())
      .then(data => {
        setPoints(data);
        if (data.length > 0) {
          // Default to a Hub if possible, usually 'HB_NORTH' or similiar
          const hub = data.find((p: any) => p.name.includes('HB_'));
          setSelectedPoint(hub ? hub.name : data[0].name);
        }
      })
      .catch(err => console.error(err));
  }, []);

  useEffect(() => {
    if (!selectedPoint) return;

    setLoading(true);
    fetch(`http://localhost:8000/financials/ercot/lmp?settlement_point=${selectedPoint}&limit=200`)
      .then(res => res.json())
      .then(data => {
        // Sort by timestamp asc for chart
        const sorted = data.sort((a: any, b: any) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
        setData(sorted);
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, [selectedPoint]);

  return (
    <div className="h-full flex flex-col space-y-4">
      <div className="flex justify-between items-center bg-gray-800 p-4 rounded-lg">
        <h3 className="text-lg font-semibold text-white">ERCOT Real-Time Market (LMP)</h3>
        <div className="flex items-center gap-4">
          <label className="text-sm text-gray-300">Settlement Point:</label>
          <select 
            value={selectedPoint} 
            onChange={(e) => setSelectedPoint(e.target.value)}
            className="bg-gray-700 text-white rounded px-2 py-1 border border-gray-600 max-w-xs"
          >
            {points.map(p => (
              <option key={p.name} value={p.name}>{p.name} ({p.type})</option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex-1 bg-gray-900 rounded-lg border border-gray-700 p-4">
        {loading ? (
          <div className="h-full flex items-center justify-center text-gray-400">Loading Market Data...</div>
        ) : data.length > 0 ? (
          <div className="h-full flex flex-col">
            <div className="flex-1 min-h-0">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis 
                    dataKey="timestamp" 
                    stroke="#9ca3af" 
                    tickFormatter={(ts) => new Date(ts).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  />
                  <YAxis stroke="#9ca3af" label={{ value: '$/MWh', angle: -90, position: 'insideLeft', fill: '#9ca3af' }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }}
                    labelFormatter={(ts) => new Date(ts).toLocaleString()}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="price" stroke="#3b82f6" dot={false} name="LMP" />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 h-48 overflow-auto border-t border-gray-700 pt-4">
               <table className="min-w-full text-sm text-left text-gray-300">
                 <thead className="text-xs text-gray-400 uppercase bg-gray-800">
                   <tr>
                     <th className="px-4 py-2">Time</th>
                     <th className="px-4 py-2">Price ($/MWh)</th>
                   </tr>
                 </thead>
                 <tbody>
                   {[...data].reverse().map((row, i) => (
                     <tr key={i} className="border-b border-gray-800 hover:bg-gray-800/50">
                       <td className="px-4 py-2">{new Date(row.timestamp).toLocaleString()}</td>
                       <td className={`px-4 py-2 font-mono ${row.price < 0 ? 'text-red-400' : 'text-green-400'}`}>
                         ${row.price.toFixed(2)}
                       </td>
                     </tr>
                   ))}
                 </tbody>
               </table>
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-400">
            No data available for this settlement point.
          </div>
        )}
      </div>
    </div>
  );
};

export default ErcotMarket;
