import { useEffect, useState } from 'react';
import axios from 'axios';
import { Activity, Database, Server, Clock, Factory, Zap, FileText } from 'lucide-react';

const StatCard = ({ title, value, icon: Icon, color }: any) => (
  <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 shadow-lg">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-gray-400 text-sm font-medium uppercase tracking-wider">{title}</p>
        <h3 className="text-3xl font-bold text-white mt-2">{value}</h3>
      </div>
      <div className={`p-3 rounded-full ${color} bg-opacity-20`}>
        <Icon className={`w-8 h-8 ${color.replace('bg-', 'text-')}`} />
      </div>
    </div>
  </div>
);

const Dashboard = () => {
  const [status, setStatus] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusRes, summaryRes] = await Promise.all([
          axios.get('http://localhost:8000/status'),
          axios.get('http://localhost:8000/eia/summary')
        ]);
        setStatus(statusRes.data);
        setSummary(summaryRes.data);
      } catch (err) {
        console.error("Failed to fetch dashboard data", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="text-white">Loading dashboard...</div>;

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white">System Overview</h2>
        <p className="text-gray-400">Real-time status of data ingestion and storage.</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Ingestion Status" 
          value={status?.status === 'running' ? 'Active' : 'Idle'} 
          icon={Activity} 
          color={status?.status === 'running' ? 'bg-green-500' : 'bg-gray-500'} 
        />
        <StatCard 
          title="EIA Series" 
          value={summary?.total_series?.toLocaleString() || '0'} 
          icon={Database} 
          color="bg-blue-500" 
        />
        <StatCard 
          title="Power Plants" 
          value={summary?.total_plants?.toLocaleString() || '0'} 
          icon={Factory} 
          color="bg-purple-500" 
        />
        <StatCard 
          title="Generators" 
          value={summary?.total_generators?.toLocaleString() || '0'} 
          icon={Zap} 
          color="bg-yellow-500" 
        />
        <StatCard 
          title="Gen. Records" 
          value={summary?.generation_records?.toLocaleString() || '0'} 
          icon={FileText} 
          color="bg-teal-500" 
        />
        <StatCard 
          title="Last Update" 
          value={status?.last_updated ? new Date(status.last_updated * 1000).toLocaleTimeString() : 'N/A'} 
          icon={Clock} 
          color="bg-indigo-500" 
        />
      </div>

      {/* Recent Activity or Logs could go here */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Ingestion Details</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="bg-gray-900 p-4 rounded-lg">
            <span className="text-gray-500 block">Current Dataset</span>
            <span className="text-white font-mono">{status?.current_dataset || 'None'}</span>
          </div>
          <div className="bg-gray-900 p-4 rounded-lg">
            <span className="text-gray-500 block">Rows Processed</span>
            <span className="text-white font-mono">{status?.rows_count?.toLocaleString() || 0}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
