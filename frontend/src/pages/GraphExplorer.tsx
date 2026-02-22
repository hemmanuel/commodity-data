import { useEffect, useState, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import axios from 'axios';
import { Share2, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

const GraphExplorer = () => {
  const [data, setData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [year, setYear] = useState<number>(2023);
  const fgRef = useRef<any>(null);

  useEffect(() => {
    const fetchGraph = async () => {
      setLoading(true);
      try {
        const res = await axios.get(`http://localhost:8000/graph/snapshot?limit=2000&year=${year}`);
        setData(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchGraph();
  }, [year]);

  const handleZoomIn = () => {
    fgRef.current?.zoom(fgRef.current.zoom() * 1.2, 400);
  };

  const handleZoomOut = () => {
    fgRef.current?.zoom(fgRef.current.zoom() / 1.2, 400);
  };

  const handleResetZoom = () => {
    fgRef.current?.zoomToFit(400);
  };

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white flex items-center gap-3">
          <Share2 className="text-blue-500" />
          Knowledge Graph Explorer
        </h2>
        <div className="text-sm text-gray-400">
          {data.nodes.length} Nodes | {data.links.length} Links
        </div>
      </div>

      <div className="flex-1 bg-gray-900 rounded-lg border border-gray-700 overflow-hidden relative">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center text-gray-500">
            Loading graph data...
          </div>
        ) : (
          <ForceGraph2D
            ref={fgRef}
            graphData={data}
            nodeLabel="name"
            nodeColor={(node: any) => node.group === 'company' ? '#3b82f6' : '#10b981'}
            nodeRelSize={6}
            backgroundColor="#111827"
            linkColor={(link: any) => {
              if (link.type === 'AFFILIATE_552') return '#d946ef'; // Magenta for corporate
              if (link.type === 'SAME_AS_552') return '#f59e0b'; // Amber for name change
              if (link.type === 'EXACT') return '#4b5563'; // Gray for ownership
              return '#9ca3af'; // Lighter gray for fuzzy/other
            }}
            linkWidth={(link: any) => (link.type === 'AFFILIATE_552' || link.type === 'SAME_AS_552') ? 2 : 1}
            linkDirectionalArrowLength={3.5}
            linkDirectionalArrowRelPos={1}
            onNodeClick={(node: any) => {
              fgRef.current?.centerAt(node.x, node.y, 1000);
              fgRef.current?.zoom(8, 2000);
            }}
          />
        )}

        {/* Controls */}
        <div className="absolute bottom-8 right-8 flex gap-2 bg-gray-800/80 p-2 rounded-lg border border-gray-700 backdrop-blur-sm">
          <button 
            onClick={handleZoomIn} 
            className="p-2 bg-gray-700 text-gray-300 hover:text-white hover:bg-gray-600 rounded transition-colors"
            title="Zoom In"
          >
            <ZoomIn size={20} />
          </button>
          <button 
            onClick={handleZoomOut} 
            className="p-2 bg-gray-700 text-gray-300 hover:text-white hover:bg-gray-600 rounded transition-colors"
            title="Zoom Out"
          >
            <ZoomOut size={20} />
          </button>
          <button 
            onClick={handleResetZoom} 
            className="p-2 bg-gray-700 text-gray-300 hover:text-white hover:bg-gray-600 rounded transition-colors"
            title="Reset View"
          >
            <RotateCcw size={20} />
          </button>
        </div>

        {/* Time Slider */}
        <div className="absolute bottom-8 left-8 right-48 bg-gray-800/80 p-4 rounded-lg border border-gray-700 backdrop-blur-sm flex items-center gap-4">
          <span className="text-white font-mono font-bold text-lg">{year}</span>
          <input 
            type="range" 
            min="2000" 
            max="2025" 
            value={year} 
            onChange={(e) => setYear(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
        </div>
      </div>
    </div>
  );
};

export default GraphExplorer;
