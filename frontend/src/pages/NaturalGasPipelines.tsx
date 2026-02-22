import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, Cell } from 'recharts';
import { Search, Filter, Map as MapIcon, Table as TableIcon, Download, ZoomIn, ZoomOut, RotateCcw, X, Info, Maximize2, Minimize2, DollarSign, ArrowRight } from 'lucide-react';
// Remove problematic imports
// import * as ReactWindow from 'react-window';
// import * as ReactVirtualizedAutoSizer from 'react-virtualized-auto-sizer';

// Simple AutoSizer implementation to avoid import issues
const AutoSizer = ({ children }: { children: (size: { width: number, height: number }) => React.ReactNode }) => {
  const ref = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (!ref.current) return;
    
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        // Use contentRect for accurate inner dimensions
        setSize({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });

    resizeObserver.observe(ref.current);
    return () => resizeObserver.disconnect();
  }, []);

  return (
    <div ref={ref} style={{ width: '100%', height: '100%', overflow: 'hidden' }}>
      {size.width > 0 && size.height > 0 && children(size)}
    </div>
  );
};

// Simple Virtual List implementation to avoid import issues
const VirtualList = ({ height, width, itemCount, itemSize, children: Row }: any) => {
  const [scrollTop, setScrollTop] = useState(0);
  
  const startIndex = Math.floor(scrollTop / itemSize);
  const endIndex = Math.min(
    itemCount - 1,
    Math.floor((scrollTop + height) / itemSize)
  );
  
  const items = [];
  // Buffer a few items
  const buffer = 5;
  const start = Math.max(0, startIndex - buffer);
  const end = Math.min(itemCount - 1, endIndex + buffer);
  
  for (let i = start; i <= end; i++) {
    items.push(
      <Row
        key={i}
        index={i}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: itemSize,
          transform: `translateY(${i * itemSize}px)`,
        }}
      />
    );
  }

  return (
    <div
      style={{ height, width, overflow: 'auto', position: 'relative' }}
      onScroll={(e) => setScrollTop(e.currentTarget.scrollTop)}
    >
      <div style={{ height: itemCount * itemSize, width: '100%' }}>
        {items}
      </div>
    </div>
  );
};

// Use our custom components
const List = VirtualList;

// Dynamically import ForceGraph2D to prevent SSR/Build issues
const ForceGraph2D = React.lazy(() => import('react-force-graph-2d'));

// State coordinates for map-like visualization
const STATE_COORDINATES: Record<string, { x: number, y: number }> = {
  'AL': { x: 670, y: 480 }, 'AK': { x: 100, y: 550 }, 'AZ': { x: 200, y: 430 },
  'AR': { x: 550, y: 430 }, 'CA': { x: 50, y: 350 }, 'CO': { x: 300, y: 350 },
  'CT': { x: 920, y: 230 }, 'DE': { x: 880, y: 300 }, 'FL': { x: 800, y: 550 },
  'GA': { x: 750, y: 480 }, 'HI': { x: 300, y: 600 }, 'ID': { x: 200, y: 200 },
  'IL': { x: 600, y: 300 }, 'IN': { x: 650, y: 300 }, 'IA': { x: 500, y: 280 },
  'KS': { x: 450, y: 380 }, 'KY': { x: 700, y: 360 }, 'LA': { x: 550, y: 520 },
  'ME': { x: 950, y: 100 }, 'MD': { x: 850, y: 310 }, 'MA': { x: 920, y: 210 },
  'MI': { x: 680, y: 220 }, 'MN': { x: 500, y: 180 }, 'MS': { x: 600, y: 480 },
  'MO': { x: 550, y: 360 }, 'MT': { x: 300, y: 150 }, 'NE': { x: 400, y: 300 },
  'NV': { x: 150, y: 300 }, 'NH': { x: 920, y: 180 }, 'NJ': { x: 900, y: 270 },
  'NM': { x: 300, y: 450 }, 'NY': { x: 850, y: 200 }, 'NC': { x: 820, y: 400 },
  'ND': { x: 400, y: 150 }, 'OH': { x: 720, y: 300 }, 'OK': { x: 450, y: 430 },
  'OR': { x: 100, y: 200 }, 'PA': { x: 820, y: 270 }, 'RI': { x: 930, y: 230 },
  'SC': { x: 800, y: 440 }, 'SD': { x: 400, y: 220 }, 'TN': { x: 680, y: 400 },
  'TX': { x: 450, y: 500 }, 'UT': { x: 250, y: 350 }, 'VT': { x: 900, y: 170 },
  'VA': { x: 820, y: 350 }, 'WA': { x: 100, y: 100 }, 'WV': { x: 780, y: 330 },
  'WI': { x: 580, y: 220 }, 'WY': { x: 300, y: 250 }, 'DC': { x: 850, y: 320 }
};

const STATE_NAMES: Record<string, string> = {
  'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
  'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
  'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
  'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
  'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
  'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
  'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
  'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
  'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
  'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
  'DC': 'District of Columbia'
};

  // Helper for color interpolation (Blue -> Gray -> Red)
  const interpolateColor = (value: number, min: number, max: number) => {
    // Separate scaling for negative (Consumer) and positive (Producer) values
    // This ensures the most extreme consumer (e.g. CA) gets the max Blue,
    // and the most extreme producer (e.g. TX) gets the max Red,
    // even if their absolute volumes differ.

    if (value < 0) {
      // Consumer: Interpolate Gray -> Vibrant Blue
      // t goes from 0 (at 0) to 1 (at min)
      const t = min === 0 ? 0 : Math.min(1, Math.abs(value / min));
      
      // Gray: rgb(107, 114, 128) -> Blue: rgb(0, 80, 255)
      return `rgb(${Math.round(107 + t * (0 - 107))}, ${Math.round(114 + t * (80 - 114))}, ${Math.round(128 + t * (255 - 128))})`;
    } else {
      // Producer: Interpolate Gray -> Red
      // t goes from 0 (at 0) to 1 (at max)
      const t = max === 0 ? 0 : Math.min(1, Math.abs(value / max));
      
      // Gray: rgb(107, 114, 128) -> Red: rgb(239, 68, 68)
      return `rgb(${Math.round(107 + t * (239 - 107))}, ${Math.round(114 + t * (68 - 114))}, ${Math.round(128 + t * (68 - 128))})`;
    }
  };

// Helper for utilization color (Green -> Yellow -> Red)
const getUtilizationColor = (utilization: number) => {
  if (utilization < 0.5) return '#10b981'; // Green
  if (utilization < 0.8) return '#f59e0b'; // Amber
  return '#ef4444'; // Red
};

const IntrastateTab = ({ stateCode }: { stateCode: string }) => {
  const [mapData, setMapData] = useState<any>(null);
  const [pipelines, setPipelines] = useState<any[]>([]);
  const [usStates, setUsStates] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isMaximized, setIsMaximized] = useState(false);
  const [selectedPipeInfo, setSelectedPipeInfo] = useState<any>(null); // For local modal
  const [selectedCompressor, setSelectedCompressor] = useState<any>(null); // For compressor modal

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch GeoJSON Map Data (Pipelines)
        const mapRes = await fetch(`http://localhost:8000/pipelines/state/${stateCode}/intrastate/map`);
        if (mapRes.ok) {
          const data = await mapRes.json();
          setMapData(data);
        }
        
        // Fetch Pipeline List
        const listRes = await fetch(`http://localhost:8000/pipelines/state/${stateCode}/intrastate`);
        if (listRes.ok) {
          const listData = await listRes.json();
          setPipelines(listData);
        }

        // Fetch US States Reference
        const statesRes = await fetch(`http://localhost:8000/reference/us_states`);
        if (statesRes.ok) {
          const statesData = await statesRes.json();
          setUsStates(statesData);
        }

      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [stateCode]);

  const InteractiveMap = ({ pipelineData, stateData, width, height }: { pipelineData: any, stateData: any, width: number, height: number }) => {
    const [transform, setTransform] = useState({ k: 1, x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const [startPoint, setStartPoint] = useState({ x: 0, y: 0 });
    const [compressors, setCompressors] = useState<any>(null);
    const [storage, setStorage] = useState<any>(null);
    const [showCompressors, setShowCompressors] = useState(false);
    const [showStorage, setShowStorage] = useState(true);
    const svgRef = useRef<SVGSVGElement>(null);

    useEffect(() => {
      // Fetch physical nodes
      const fetchNodes = async () => {
        try {
          const compRes = await fetch('http://localhost:8000/spatial/compressors');
          if (compRes.ok) setCompressors(await compRes.json());
          
          const storRes = await fetch('http://localhost:8000/spatial/storage');
          if (storRes.ok) setStorage(await storRes.json());
        } catch (e) {
          console.error("Error fetching physical nodes", e);
        }
      };
      fetchNodes();
    }, []);

    // Find the specific state feature
    const stateFeature = useMemo(() => {
      if (!stateData) return null;
      const stateName = STATE_NAMES[stateCode];
      return stateData.features.find((f: any) => f.properties.name === stateName);
    }, [stateData, stateCode]);

    // Calculate bounds for the State (or pipelines if state missing)
    const bounds = useMemo(() => {
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      
      const processCoords = (coords: any[]) => {
        coords.forEach((coord: any) => {
          if (Array.isArray(coord[0])) {
            processCoords(coord);
          } else {
            const [x, y] = coord;
            if (x < minX) minX = x;
            if (x > maxX) maxX = x;
            if (y < minY) minY = y;
            if (y > maxY) maxY = y;
          }
        });
      };

      // Prioritize State Feature for bounds
      if (stateFeature) {
        processCoords(stateFeature.geometry.coordinates);
      } else if (pipelineData && pipelineData.features) {
        pipelineData.features.forEach((f: any) => {
          if (f.geometry) processCoords(f.geometry.coordinates);
        });
      }

      if (minX === Infinity) return null;

      // Add padding
      const paddingX = (maxX - minX) * 0.05;
      const paddingY = (maxY - minY) * 0.05;
      
      return { 
        minX: minX - paddingX, 
        minY: minY - paddingY, 
        maxX: maxX + paddingX, 
        maxY: maxY + paddingY 
      };
    }, [stateFeature, pipelineData]);

    // Projection function
    const project = (coords: any[]) => {
      if (!coords || coords.length === 0 || !bounds) return '';
      
      const { minX, minY, maxX, maxY } = bounds;
      const mapWidth = maxX - minX;
      const mapHeight = maxY - minY;
      
      // Scale to fit SVG
      const scaleX = width / mapWidth;
      const scaleY = height / mapHeight;
      const baseScale = Math.min(scaleX, scaleY);
      
      // Center in SVG
      const offsetX = (width - mapWidth * baseScale) / 2;
      const offsetY = (height - mapHeight * baseScale) / 2;

      const points = coords.map((pt: any) => {
        const x = (pt[0] - minX) * baseScale + offsetX;
        const y = height - ((pt[1] - minY) * baseScale + offsetY); // Flip Y
        return `${x},${y}`;
      });
      
      return `M ${points.join(' L ')}`;
    };

    const projectPoint = (coord: number[]) => {
      if (!coord || coord.length < 2 || !bounds) return null;
      const { minX, minY, maxX, maxY } = bounds;
      const mapWidth = maxX - minX;
      const mapHeight = maxY - minY;
      const scaleX = width / mapWidth;
      const scaleY = height / mapHeight;
      const baseScale = Math.min(scaleX, scaleY);
      const offsetX = (width - mapWidth * baseScale) / 2;
      const offsetY = (height - mapHeight * baseScale) / 2;
      
      const x = (coord[0] - minX) * baseScale + offsetX;
      const y = height - ((coord[1] - minY) * baseScale + offsetY);
      return { x, y };
    };

    const handleWheel = (e: React.WheelEvent) => {
      e.preventDefault();
      const scaleFactor = 1.1;
      const newK = e.deltaY < 0 ? transform.k * scaleFactor : transform.k / scaleFactor;
      // Clamp zoom
      const clampedK = Math.max(0.5, Math.min(newK, 10));
      setTransform(prev => ({ ...prev, k: clampedK }));
    };

    const handleMouseDown = (e: React.MouseEvent) => {
      setIsDragging(true);
      setStartPoint({ x: e.clientX - transform.x, y: e.clientY - transform.y });
    };

    const handleMouseMove = (e: React.MouseEvent) => {
      if (!isDragging) return;
      setTransform(prev => ({
        ...prev,
        x: e.clientX - startPoint.x,
        y: e.clientY - startPoint.y
      }));
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    const renderFeature = (feature: any, idx: number, type: 'state' | 'pipeline') => {
      const geometry = feature.geometry;
      if (!geometry) return null;

      let d = '';
      if (geometry.type === 'LineString') {
        d = project(geometry.coordinates);
      } else if (geometry.type === 'MultiLineString') {
        d = geometry.coordinates.map((line: any) => project(line).replace('M', '')).join(' M ');
        if (d) d = 'M ' + d;
      } else if (geometry.type === 'Polygon') {
        d = geometry.coordinates.map((ring: any) => project(ring).replace('M', '')).join(' Z M ');
        if (d) d = 'M ' + d + ' Z';
      } else if (geometry.type === 'MultiPolygon') {
         d = geometry.coordinates.map((poly: any) => 
           poly.map((ring: any) => project(ring).replace('M', '')).join(' Z M ')
         ).join(' Z M ');
         if (d) d = 'M ' + d + ' Z';
      }

      if (!d) return null;

      if (type === 'state') {
        return <path key={`state-${idx}`} d={d} fill="#1f2937" stroke="#374151" strokeWidth="2" />;
      } else {
        return (
          <path 
            key={`pipe-${idx}`} 
            d={d} 
            stroke={feature.properties.type === 'Interstate' ? '#ef4444' : '#3b82f6'} 
            strokeWidth={2 / transform.k} // Keep stroke width constant relative to screen
            fill="none" 
            className="cursor-pointer hover:stroke-yellow-400 transition-colors"
            onClick={(e) => {
              e.stopPropagation();
              // Find matching pipeline info from the list if possible
              const pipeName = feature.properties.operator;
              const info = pipelines.find(p => p.pipeline === pipeName) || { 
                pipeline: pipeName, 
                parent_company: 'Unknown',
                type: feature.properties.typepipe,
                status: feature.properties.status
              };
              setSelectedPipeInfo(info);
            }}
          />
        );
      }
    };

    const renderPoint = (feature: any, idx: number, type: 'compressor' | 'storage') => {
      const pt = projectPoint(feature.geometry.coordinates);
      if (!pt) return null;
      
      // Filter points outside bounds (simple check)
      if (pt.x < 0 || pt.x > width || pt.y < 0 || pt.y > height) return null;

      const color = type === 'compressor' ? '#f59e0b' : '#10b981'; // Amber for compressor, Emerald for storage
      
      // Scale size by Horsepower for compressors
      let size = (type === 'compressor' ? 3 : 4) / transform.k;
      if (type === 'compressor' && feature.properties.CERT_HP) {
        // Max HP is ~130k. Scale from 3 to 10 based on HP.
        // Log scale is better for wide ranges
        const hp = feature.properties.CERT_HP;
        const scale = Math.log10(hp + 1) / Math.log10(130000); // 0 to 1
        size = (3 + scale * 8) / transform.k;
      }

      return (
        <circle 
          key={`${type}-${idx}`}
          cx={pt.x}
          cy={pt.y}
          r={size}
          fill={color}
          stroke="#000"
          strokeWidth={0.5 / transform.k}
          opacity={0.8}
          className="cursor-pointer hover:stroke-white transition-colors"
          onClick={(e) => {
            e.stopPropagation();
            if (type === 'compressor') {
              setSelectedCompressor(feature.properties);
            }
          }}
        >
          <title>{feature.properties.NAME || feature.properties.name || type}</title>
        </circle>
      );
    };

    if (!bounds) return <div className="flex items-center justify-center h-full text-gray-500">Loading map data...</div>;

    return (
      <div className="w-full h-full overflow-hidden bg-gray-900 relative">
        <svg 
          ref={svgRef}
          width={width} 
          height={height} 
          className="w-full h-full cursor-move"
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          <g transform={`translate(${transform.x}, ${transform.y}) scale(${transform.k})`}>
            {/* Render State Shape */}
            {stateFeature && renderFeature(stateFeature, 0, 'state')}
            
            {/* Render Pipelines */}
            {pipelineData?.features.map((f: any, idx: number) => renderFeature(f, idx, 'pipeline'))}

            {/* Render Physical Nodes */}
            {showCompressors && compressors?.features.map((f: any, idx: number) => renderPoint(f, idx, 'compressor'))}
            {showStorage && storage?.features.map((f: any, idx: number) => renderPoint(f, idx, 'storage'))}
          </g>
        </svg>
        
        {/* Legend & Controls */}
        <div className="absolute top-4 left-4 flex flex-col gap-2">
          {/* Legend */}
          <div className="bg-gray-900/80 p-2 rounded border border-gray-700 backdrop-blur-sm text-xs text-gray-300">
            <div className="flex items-center gap-2 mb-1"><div className="w-3 h-3 rounded-full bg-amber-500"></div>Compressor Station</div>
            <div className="flex items-center gap-2 mb-1"><div className="w-3 h-3 rounded-full bg-emerald-500"></div>Storage Field</div>
            <div className="flex items-center gap-2 mb-1"><div className="w-4 h-0.5 bg-blue-500"></div>Intrastate Pipe</div>
            <div className="flex items-center gap-2"><div className="w-4 h-0.5 bg-red-500"></div>Interstate Pipe</div>
          </div>

          {/* Toggles */}
          <div className="bg-gray-900/80 p-2 rounded border border-gray-700 backdrop-blur-sm text-xs text-gray-300 flex flex-col gap-2">
            <label className="flex items-center gap-2 cursor-pointer hover:text-white">
              <input 
                type="checkbox" 
                checked={showCompressors} 
                onChange={(e) => setShowCompressors(e.target.checked)}
                className="rounded bg-gray-700 border-gray-600 text-amber-500 focus:ring-amber-500 focus:ring-offset-gray-900"
              />
              Show Compressors
            </label>
            <label className="flex items-center gap-2 cursor-pointer hover:text-white">
              <input 
                type="checkbox" 
                checked={showStorage} 
                onChange={(e) => setShowStorage(e.target.checked)}
                className="rounded bg-gray-700 border-gray-600 text-emerald-500 focus:ring-emerald-500 focus:ring-offset-gray-900"
              />
              Show Storage
            </label>
          </div>
        </div>

        {/* Zoom Controls Overlay */}
        <div className="absolute bottom-4 right-4 flex flex-col gap-2">
           <button onClick={() => setTransform(t => ({...t, k: Math.min(t.k * 1.2, 10)}))} className="p-2 bg-gray-800 text-white rounded shadow hover:bg-gray-700"><ZoomIn size={20}/></button>
           <button onClick={() => setTransform(t => ({...t, k: Math.max(t.k / 1.2, 0.5)}))} className="p-2 bg-gray-800 text-white rounded shadow hover:bg-gray-700"><ZoomOut size={20}/></button>
           <button onClick={() => setTransform({k: 1, x: 0, y: 0})} className="p-2 bg-gray-800 text-white rounded shadow hover:bg-gray-700"><RotateCcw size={20}/></button>
        </div>
      </div>
    );
  };

  const renderMapContainer = (maximized: boolean) => (
    <div className={`relative bg-gray-900 overflow-hidden flex flex-col ${maximized ? 'fixed inset-4 z-[250] rounded-xl shadow-2xl border border-gray-700' : 'h-[500px] rounded-lg border border-gray-700'}`}>
      <div className="absolute top-4 right-4 z-10 flex gap-2">
        <button 
          onClick={() => setIsMaximized(!isMaximized)}
          className="p-2 bg-gray-800/80 text-gray-300 hover:text-white rounded-lg backdrop-blur-sm border border-gray-700 transition-colors"
        >
          {isMaximized ? <Minimize2 size={20} /> : <Maximize2 size={20} />}
        </button>
      </div>
      
      {loading ? (
        <div className="absolute inset-0 flex items-center justify-center text-gray-400">Loading map...</div>
      ) : (
        <div className="flex-1 w-full h-full">
          <AutoSizer>
            {({ width, height }) => (
              <InteractiveMap pipelineData={mapData} stateData={usStates} width={width} height={height} />
            )}
          </AutoSizer>
        </div>
      )}
    </div>
  );

  return (
    <div>
      <h3 className="text-lg font-semibold text-white mb-4">Intrastate Pipeline Network Map</h3>
      {renderMapContainer(false)}
      {isMaximized && renderMapContainer(true)}
      
      {/* Pipeline Details Modal (Local) */}
      {selectedPipeInfo && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[300] backdrop-blur-sm">
           <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-md p-6">
              <div className="flex justify-between items-start mb-4">
                 <h3 className="text-xl font-bold text-white">{selectedPipeInfo.pipeline}</h3>
                 <button onClick={() => setSelectedPipeInfo(null)} className="text-gray-400 hover:text-white"><X size={24}/></button>
              </div>
              <div className="space-y-3 text-gray-300">
                 <p><span className="text-gray-500">Operator/Parent:</span> {selectedPipeInfo.parent_company || selectedPipeInfo.pipeline}</p>
                 <p><span className="text-gray-500">Type:</span> {selectedPipeInfo.type || 'Intrastate'}</p>
                 <p><span className="text-gray-500">Capacity:</span> <span className="text-blue-400 font-mono">{selectedPipeInfo.capacity_mmcfd ? selectedPipeInfo.capacity_mmcfd.toLocaleString() : 'N/A'} MMcf/d</span></p>
                 <p><span className="text-gray-500">Length:</span> {selectedPipeInfo.miles ? selectedPipeInfo.miles.toLocaleString() : 'N/A'} miles</p>
                 <p><span className="text-gray-500">Region:</span> {selectedPipeInfo.region || 'N/A'}</p>
                 {selectedPipeInfo.status && <p><span className="text-gray-500">Status:</span> {selectedPipeInfo.status}</p>}
              </div>
           </div>
        </div>
      )}

      {/* Compressor Details Modal */}
      {selectedCompressor && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[300] backdrop-blur-sm">
           <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-md p-6">
              <div className="flex justify-between items-start mb-4">
                 <h3 className="text-xl font-bold text-white">{selectedCompressor.NAME}</h3>
                 <button onClick={() => setSelectedCompressor(null)} className="text-gray-400 hover:text-white"><X size={24}/></button>
              </div>
              <div className="space-y-3 text-gray-300">
                 <p><span className="text-gray-500">Operator:</span> {selectedCompressor.OPERATOR || 'Unknown'}</p>
                 <p><span className="text-gray-500">Status:</span> {selectedCompressor.STATUS || 'Active'}</p>
                 <p><span className="text-gray-500">Horsepower:</span> <span className="text-amber-400 font-mono">{selectedCompressor.CERT_HP ? selectedCompressor.CERT_HP.toLocaleString() : 'N/A'} HP</span></p>
                 <p><span className="text-gray-500">Units:</span> {selectedCompressor.NUM_UNITS || 'N/A'}</p>
                 {selectedCompressor.PLANT_COST > 0 && (
                   <p><span className="text-gray-500">Plant Cost:</span> ${selectedCompressor.PLANT_COST.toLocaleString()}</p>
                 )}
                 <p><span className="text-gray-500">Location:</span> {selectedCompressor.COUNTY}, {selectedCompressor.STATE}</p>
              </div>
           </div>
        </div>
      )}

      <div className="mt-6">
        <h4 className="text-md font-medium text-gray-300 mb-3">Pipeline Details</h4>
        <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
          <table className="w-full text-sm text-left text-gray-300">
            <thead className="text-xs text-gray-400 uppercase bg-gray-900/50">
              <tr>
                <th className="px-6 py-3">Pipeline</th>
                <th className="px-6 py-3">Parent Company</th>
                <th className="px-6 py-3 text-right">Miles</th>
                <th className="px-6 py-3 text-right">Capacity (MMcf/d)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {pipelines.map((p, idx) => (
                <tr key={idx} className="hover:bg-gray-700/50 cursor-pointer" onClick={() => setSelectedPipeInfo(p)}>
                  <td className="px-6 py-4 font-medium text-white">{p.pipeline}</td>
                  <td className="px-6 py-4">{p.parent_company}</td>
                  <td className="px-6 py-4 text-right">{p.miles?.toLocaleString() || '-'}</td>
                  <td className="px-6 py-4 text-right font-mono text-blue-400">{p.capacity_mmcfd?.toLocaleString() || '-'}</td>
                </tr>
              ))}
              {pipelines.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-gray-500 italic">
                    No intrastate pipelines found for this state.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const ProductionFlowTab = ({ stateCode }: { stateCode: string }) => {
  const [production, setProduction] = useState<any[]>([]);
  const [flow, setFlow] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch Production History
        const prodRes = await fetch(`http://localhost:8000/production/history?state_code=${stateCode}`);
        if (prodRes.ok) {
          const data = await prodRes.json();
          setProduction(data);
        }

        // Fetch Interstate Flow
        const flowRes = await fetch(`http://localhost:8000/flow/interstate?state_code=${stateCode}`);
        if (flowRes.ok) {
          const data = await flowRes.json();
          setFlow(data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [stateCode]);

  // Process Flow Data for Chart
  const flowChartData = useMemo(() => {
    if (!flow.length) return [];
    
    // Group by Year
    const byYear: Record<number, { year: number, receipts: number, deliveries: number }> = {};
    
    flow.forEach((r: any) => {
      if (!byYear[r.year]) byYear[r.year] = { year: r.year, receipts: 0, deliveries: 0 };
      
      // If 'to_state' is this state, it's a Receipt (Inflow)
      if (r.to_state === stateCode) {
        byYear[r.year].receipts += r.value;
      } 
      // If 'from_state' is this state, it's a Delivery (Outflow)
      else if (r.from_state === stateCode) {
        byYear[r.year].deliveries += r.value;
      }
    });
    
    return Object.values(byYear).sort((a, b) => a.year - b.year);
  }, [flow, stateCode]);

  if (loading) return <div className="p-8 text-center text-gray-400">Loading data...</div>;

  return (
    <div className="space-y-8">
      {/* Production Chart */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Natural Gas Marketed Production</h3>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={production}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
              <XAxis 
                dataKey="date" 
                stroke="#9ca3af" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false}
                tickFormatter={(val) => new Date(val).getFullYear().toString()}
                minTickGap={30}
              />
              <YAxis 
                stroke="#9ca3af" 
                fontSize={12} 
                tickLine={false} 
                axisLine={false} 
                tickFormatter={(val) => `${val/1000}k`} 
              />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }}
                formatter={(val: number) => [`${val.toLocaleString()} MMcf`, 'Production']}
                labelFormatter={(label) => new Date(label).toLocaleDateString()}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="value" 
                name="Marketed Production" 
                stroke="#f59e0b" 
                strokeWidth={2} 
                dot={false} 
                activeDot={{ r: 6, fill: '#fbbf24' }} 
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <p className="text-xs text-gray-500 mt-2 text-center">Source: EIA-914 / Natural Gas Monthly</p>
      </div>

      {/* Flow Chart */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Interstate Flow History (Annual)</h3>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={flowChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
              <XAxis dataKey="year" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `${val/1000}k`} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }}
                formatter={(val: number) => [`${val.toLocaleString()} MMcf`, 'Volume']}
              />
              <Legend />
              <Bar dataKey="receipts" name="Receipts (Inflow)" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="deliveries" name="Deliveries (Outflow)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <p className="text-xs text-gray-500 mt-2 text-center">Source: EIA Interstate Movements</p>
      </div>
    </div>
  );
};

const NaturalGasPipelines = () => {
  const [viewMode, setViewMode] = useState<'map' | 'table'>('map');
  const [year, setYear] = useState<number | 'all'>(2023);
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [tableData, setTableData] = useState<any[]>([]);
  const [topPipelines, setTopPipelines] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLink, setSelectedLink] = useState<any>(null);
  const [selectedState, setSelectedState] = useState<any>(null);
  const [selectedPipeline, setSelectedPipeline] = useState<any>(null);
  const [financialLinks, setFinancialLinks] = useState<Record<string, any>>({});
  const [isMaximized, setIsMaximized] = useState(false);
  const fgRef = useRef<any>(null);

  useEffect(() => {
    fetchData();
    fetchFinancialLinks();
  }, [year]);

  const fetchFinancialLinks = async () => {
    try {
      const res = await fetch('http://localhost:8000/pipelines/financial-links');
      if (res.ok) {
        const data = await res.json();
        setFinancialLinks(data);
      }
    } catch (error) {
      console.error("Error fetching financial links:", error);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch Graph Data
      const graphYear = year === 'all' ? 2023 : year;
      const graphRes = await fetch(`http://localhost:8000/pipelines/graph?year=${graphYear}`);
      if (graphRes.ok) {
        const graphJson = await graphRes.json();
        
        // Calculate ranges for normalization
        let minNetFlow = 0;
        let maxNetFlow = 0;
        let maxVolume = 0;
        
        graphJson.nodes.forEach((n: any) => {
          if (n.metrics) {
            minNetFlow = Math.min(minNetFlow, n.metrics.net_flow);
            maxNetFlow = Math.max(maxNetFlow, n.metrics.net_flow);
            maxVolume = Math.max(maxVolume, n.metrics.total_volume);
          }
        });
        
        // Fallback if no metrics
        if (maxVolume === 0) maxVolume = 1;

        // Process links to detect bidirectional flows and add curvature
        const links = graphJson.links;
        const processedLinks = links.map((link: any) => {
          // Check if reverse link exists
          const reverseLink = links.find((l: any) => l.source === link.target && l.target === link.source);
          
          return { 
            ...link, 
            curvature: reverseLink ? 0.2 : 0,
            color: getUtilizationColor(link.utilization || 0)
          };
        });

        // Add coordinates to nodes
        const nodesWithCoords = graphJson.nodes.map((node: any) => {
          // Scale size by volume (min 3, max 15)
          const size = node.metrics ? 3 + (node.metrics.total_volume / maxVolume) * 12 : 5;
          const color = node.metrics ? interpolateColor(node.metrics.net_flow, minNetFlow, maxNetFlow) : '#3b82f6';
          
          return {
            ...node,
            fx: STATE_COORDINATES[node.id]?.x ? STATE_COORDINATES[node.id].x - 500 : undefined,
            fy: STATE_COORDINATES[node.id]?.y ? STATE_COORDINATES[node.id].y - 300 : undefined,
            val: size,
            color: color
          };
        });

        setGraphData({ nodes: nodesWithCoords, links: processedLinks });
      }

      // Fetch Top Pipelines
      const topRes = await fetch(`http://localhost:8000/pipelines/top?year=${graphYear}&limit=10`);
      if (topRes.ok) {
        const topJson = await topRes.json();
        setTopPipelines(topJson);
      }

      // Fetch Table Data
      const yearParam = year === 'all' ? '' : `&year=${year}`;
      const tableRes = await fetch(`http://localhost:8000/pipelines/capacity?limit=50000${yearParam}`);
      if (tableRes.ok) {
        const tableJson = await tableRes.json();
        setTableData(tableJson.data || []);
      } else {
        setTableData([]);
      }

    } catch (error) {
      console.error("Error fetching pipeline data:", error);
      setTableData([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchPipelineEdgeDetails = async (link: any) => {
    try {
      // link.source and link.target are objects in the graph data, we need their IDs
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' ? link.target.id : link.target;
      const graphYear = year === 'all' ? 2023 : year;
      
      const res = await fetch(`http://localhost:8000/pipelines/edge/${sourceId}/${targetId}?year=${graphYear}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedLink(data);
      }
    } catch (error) {
      console.error("Error fetching edge details:", error);
    }
  };

  const fetchStateDetails = async (stateId: string) => {
    try {
      const graphYear = year === 'all' ? 2023 : year;
      const res = await fetch(`http://localhost:8000/pipelines/state/${stateId}?year=${graphYear}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedState(data);
      }
    } catch (error) {
      console.error("Error fetching state details:", error);
    }
  };

  const fetchPipelineDetails = async (pipelineId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/pipelines/details/${pipelineId}`);
      if (res.ok) {
        const data = await res.json();
        
        // Fetch Financials if linked
        // Note: pipelineId here is the cleaned ID (e.g. 'elpaso'), but our link map uses the full name
        // We need to find the full name first. data.name has it.
        let financialData = null;
        const operatorName = data.name;
        
        // Check if we have a link for this operator
        // We need to check both exact and fuzzy matches from our map, but the map keys are operator names
        // The map is: { "Operator Name": { company_id: "...", score: ... } }
        
        if (financialLinks[operatorName]) {
           try {
             const finRes = await fetch(`http://localhost:8000/pipelines/${encodeURIComponent(operatorName)}/financials`);
             if (finRes.ok) {
               financialData = await finRes.json();
             }
           } catch (e) {
             console.error("Error fetching financials", e);
           }
        }

        setSelectedPipeline({ ...data, financials: financialData });
      }
    } catch (error) {
      console.error("Error fetching pipeline details:", error);
    }
  };

  const filteredTableData = useMemo(() => {
    if (!tableData) return [];
    return tableData.filter((row: any) => 
      row.pipeline?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      row.state_from?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      row.state_to?.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [tableData, searchTerm]);

  // Row renderer for react-window
  const Row = ({ index, style }: { index: number, style: any }) => {
    const row = filteredTableData[index];
    if (!row) return null;
    return (
      <div style={style} className="flex border-b border-gray-700 hover:bg-gray-700 text-sm text-gray-300">
        <div className="flex-1 px-6 py-3 font-medium text-white truncate" title={row.pipeline}>{row.pipeline}</div>
        <div className="w-24 px-6 py-3">{row.year}</div>
        <div className="w-24 px-6 py-3">{row.state_from}</div>
        <div className="w-24 px-6 py-3">{row.state_to}</div>
        <div className="w-32 px-6 py-3 text-right">{row.capacity_mmcfd?.toLocaleString()}</div>
      </div>
    );
  };

  const renderMapContent = (isMaximizedView: boolean) => (
    <>
      <div className="p-4 border-b border-gray-700 font-medium text-white flex justify-between items-center bg-gray-800">
        <div className="flex items-center gap-4">
          <span>{viewMode === 'map' ? 'Interstate Pipeline Network Flow' : 'Pipeline Capacity Data'}</span>
          {viewMode === 'map' && <span className="text-xs text-gray-400 font-normal">Click a link to see pipelines</span>}
        </div>
        <button
          onClick={() => setIsMaximized(!isMaximized)}
          className="p-1.5 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors"
          title={isMaximized ? "Minimize" : "Maximize"}
        >
          {isMaximized ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
        </button>
      </div>
      
      <div className="flex-1 relative bg-gray-900 min-h-0">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center text-gray-400">Loading...</div>
        ) : viewMode === 'map' ? (
          <div className="absolute inset-0">
            <AutoSizer>
              {({ width, height }) => (
                <React.Suspense fallback={<div className="text-gray-400 p-4">Loading Graph...</div>}>
                  <ForceGraph2D
                    key={isMaximizedView ? 'maximized' : 'normal'}
                    ref={fgRef}
                    graphData={graphData}
                    nodeLabel="name"
                    // Custom Node Rendering for prominence
                    nodeCanvasObject={(node: any, ctx: any, globalScale: number) => {
                      const val = node.val || 5;
                      const r = Math.sqrt(val) * 3; // Scale up radius
                      
                      // Glow effect
                      ctx.shadowColor = node.color || '#3b82f6';
                      ctx.shadowBlur = 15;
                      ctx.shadowOffsetX = 0;
                      ctx.shadowOffsetY = 0;

                      // Draw Circle
                      ctx.beginPath();
                      ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
                      ctx.fillStyle = node.color || '#3b82f6';
                      ctx.fill();
                      
                      // Reset shadow for border and text
                      ctx.shadowBlur = 0;

                      // Draw Border
                      ctx.lineWidth = 2 / globalScale;
                      ctx.strokeStyle = '#ffffff'; // White border for contrast
                      ctx.stroke();
                      
                      // Draw Label
                      const label = node.name;
                      const fontSize = 14 / globalScale; // Scale text
                      ctx.font = `bold ${fontSize}px Sans-Serif`;
                      ctx.textAlign = 'center';
                      ctx.textBaseline = 'middle';
                      ctx.fillStyle = '#ffffff';
                      // Draw label in center if large enough, otherwise below
                      if (r > fontSize) {
                         ctx.fillText(label, node.x, node.y);
                      } else {
                         ctx.fillText(label, node.x, node.y + r + 2);
                      }
                    }}
                    nodePointerAreaPaint={(node: any, color: string, ctx: any) => {
                      const val = node.val || 5;
                      const r = Math.sqrt(val) * 3;
                      ctx.fillStyle = color;
                      ctx.beginPath();
                      ctx.arc(node.x, node.y, r + 2, 0, 2 * Math.PI, false); // Slightly larger hit area
                      ctx.fill();
                    }}
                    
                    linkColor={(link: any) => link.color || '#4b5563'}
                    linkWidth={link => Math.sqrt(link.capacity) / 8} // Slightly thicker links
                    linkCurvature="curvature"
                    
                    // Prominent Flow Arrows
                    linkDirectionalArrowLength={10} // Larger arrows
                    linkDirectionalArrowRelPos={0.5}
                    linkDirectionalArrowColor={() => "#ffffff"} // White arrows for contrast
                    
                    // Removed Particles (Animation)
                    linkDirectionalParticles={0}
                    
                    backgroundColor="#1f2937"
                    width={width} 
                    height={height}
                    cooldownTicks={0} 
                    onLinkClick={(link: any) => {
                      fetchPipelineEdgeDetails(link);
                    }}
                    onNodeClick={(node: any) => {
                      fetchStateDetails(node.id);
                    }}
                  />
                </React.Suspense>
              )}
            </AutoSizer>
          </div>
        ) : (
          <div className="h-full w-full flex flex-col">
            <div className="flex border-b border-gray-700 bg-gray-750 text-xs text-gray-400 uppercase sticky top-0 z-10">
              <div className="flex-1 px-6 py-3">Pipeline</div>
              <div className="w-24 px-6 py-3">Year</div>
              <div className="w-24 px-6 py-3">From</div>
              <div className="w-24 px-6 py-3">To</div>
              <div className="w-32 px-6 py-3 text-right">Capacity (MMcf/d)</div>
            </div>
            <div className="flex-1 min-h-0">
              <AutoSizer>
                {({ height, width }) => (
                  <List
                    height={height}
                    itemCount={filteredTableData.length}
                    itemSize={48}
                    width={width}
                  >
                    {Row}
                  </List>
                )}
              </AutoSizer>
            </div>
          </div>
        )}

        {!loading && viewMode === 'map' && (
          <>
            <div className="absolute top-4 left-4 bg-gray-900/80 p-3 rounded-lg border border-gray-700 backdrop-blur-sm text-xs text-gray-300">
              <div className="font-semibold mb-2 text-white">Node Color (Net Flow)</div>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <span>Net Producer (Exporter)</span>
              </div>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-3 h-3 rounded-full bg-gray-500"></div>
                <span>Balanced / Transit</span>
              </div>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-3 h-3 rounded-full bg-[rgb(0,80,255)]"></div>
                <span>Net Consumer (Importer)</span>
              </div>
              
              <div className="font-semibold mb-2 text-white">Link Color (Utilization)</div>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-8 h-1 bg-emerald-500 rounded"></div>
                <span>Low (&lt;50%)</span>
              </div>
              <div className="flex items-center gap-2 mb-1">
                <div className="w-8 h-1 bg-amber-500 rounded"></div>
                <span>Medium (50-80%)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-8 h-1 bg-red-500 rounded"></div>
                <span>High (&gt;80%)</span>
              </div>
            </div>

            <div className="absolute bottom-4 right-4 flex gap-2 bg-gray-800/80 p-2 rounded-lg border border-gray-700 backdrop-blur-sm">
              <button 
                onClick={() => fgRef.current?.zoom(fgRef.current.zoom() * 1.2, 400)}
                className="p-2 bg-gray-700 text-gray-300 hover:text-white hover:bg-gray-600 rounded transition-colors"
                title="Zoom In"
              >
                <ZoomIn size={20} />
              </button>
              <button 
                onClick={() => fgRef.current?.zoom(fgRef.current.zoom() / 1.2, 400)}
                className="p-2 bg-gray-700 text-gray-300 hover:text-white hover:bg-gray-600 rounded transition-colors"
                title="Zoom Out"
              >
                <ZoomOut size={20} />
              </button>
              <button 
                onClick={() => fgRef.current?.zoomToFit(400)}
                className="p-2 bg-gray-700 text-gray-300 hover:text-white hover:bg-gray-600 rounded transition-colors"
                title="Reset View"
              >
                <RotateCcw size={20} />
              </button>
            </div>
          </>
        )}
      </div>
    </>
  );

  return (
    <div className="h-full flex flex-col space-y-6 relative">
      {/* Header Controls */}
      <div className="flex justify-between items-center bg-gray-800 p-4 rounded-lg">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold text-white">Natural Gas Pipelines</h1>
          <div className="h-6 w-px bg-gray-700"></div>
          <p className="text-gray-400">Interstate Capacity & Network Flows</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex bg-gray-700 rounded-lg p-1">
            <button
              onClick={() => setViewMode('map')}
              className={`px-3 py-1.5 rounded-md flex items-center space-x-2 text-sm font-medium transition-colors ${
                viewMode === 'map' ? 'bg-blue-600 text-white' : 'text-gray-300 hover:text-white'
              }`}
            >
              <MapIcon size={16} />
              <span>Map View</span>
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`px-3 py-1.5 rounded-md flex items-center space-x-2 text-sm font-medium transition-colors ${
                viewMode === 'table' ? 'bg-blue-600 text-white' : 'text-gray-300 hover:text-white'
              }`}
            >
              <TableIcon size={16} />
              <span>Table View</span>
            </button>
          </div>
          
          <select 
            value={year} 
            onChange={(e) => setYear(e.target.value === 'all' ? 'all' : Number(e.target.value))}
            className="bg-gray-700 border-none text-white text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2"
          >
            <option value="all">All Years</option>
            {[...Array(34)].map((_, i) => (
              <option key={i} value={2023 - i}>{2023 - i}</option>
            ))}
          </select>
        </div>

        {viewMode === 'table' && (
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
            <input
              type="text"
              placeholder="Search pipelines or states..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 bg-gray-700 border-none rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 text-sm w-64"
            />
          </div>
        )}
      </div>

      {/* Maximized Overlay */}
      {isMaximized && (
        <div className="fixed inset-4 z-[100] bg-gray-800 rounded-lg border border-gray-700 shadow-2xl flex flex-col overflow-hidden">
          {renderMapContent(true)}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100%-80px)]">
        {/* Main View Area (Map or Table) - Normal Mode */}
        <div className={`bg-gray-800 rounded-lg border border-gray-700 overflow-hidden flex flex-col relative lg:col-span-2 ${isMaximized ? 'invisible' : ''}`}>
          {!isMaximized && renderMapContent(false)}
        </div>

        {/* Sidebar Charts */}
        <div className="space-y-6">
          {/* ... (Charts remain same) ... */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-4 h-1/2 flex flex-col">
            <h3 className="text-lg font-medium text-white mb-4">Top Pipelines by Capacity ({year === 'all' ? 'All Time Peak' : year})</h3>
            <div className="flex-1 min-h-0">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topPipelines} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
                  <XAxis type="number" stroke="#9ca3af" tickFormatter={(val) => `${val/1000}k`} />
                  <YAxis dataKey="name" type="category" width={100} stroke="#9ca3af" style={{ fontSize: '10px' }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }}
                    formatter={(val: number) => [`${val.toLocaleString()} MMcf/d`, 'Capacity']}
                  />
                  <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
            <h3 className="text-lg font-medium text-white mb-2">About This Data</h3>
            <p className="text-sm text-gray-400">
              This data represents the estimated design capacity of interstate natural gas pipelines 
              at state borders. It is sourced from the EIA's "State-to-State Capacity" dataset.
            </p>
            <div className="mt-4 text-xs text-gray-500">
              <p>Total Records: {tableData?.length || 0}</p>
              <p>Source: EIA Natural Gas Pipeline Network</p>
            </div>
          </div>
        </div>
      </div>

      {/* Link Selection Modal */}
      {selectedLink && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[200] backdrop-blur-sm">
          <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-md max-h-[80vh] flex flex-col">
            <div className="p-4 border-b border-gray-800 flex justify-between items-center">
              <h3 className="text-lg font-bold text-white">
                {selectedLink.state_from} → {selectedLink.state_to}
              </h3>
              <button onClick={() => setSelectedLink(null)} className="text-gray-400 hover:text-white">
                <X size={20} />
              </button>
            </div>
            <div className="p-4 overflow-y-auto flex-1">
              <p className="text-sm text-gray-400 mb-4">
                Total Capacity: <span className="text-white font-mono">{selectedLink.total_capacity?.toLocaleString()} MMcf/d</span>
              </p>
              <div className="space-y-2">
                {selectedLink.pipelines?.map((p: any) => (
                  <button
                    key={p.id}
                    onClick={() => {
                      fetchPipelineDetails(p.id);
                      setSelectedLink(null);
                    }}
                    className="w-full text-left px-4 py-3 bg-gray-800 hover:bg-gray-700 rounded-lg border border-gray-700 transition-colors flex flex-col gap-1 group"
                  >
                    <div className="flex justify-between items-center w-full">
                      <span className="text-sm font-medium text-gray-200 group-hover:text-white capitalize truncate pr-2">
                        {p.name}
                      </span>
                      <Info size={16} className="text-blue-500 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                    </div>
                    <div className="flex justify-between items-center text-xs text-gray-400 w-full">
                      <span>{p.capacity.toLocaleString()} MMcf/d</span>
                      <span className="text-blue-400">{p.share.toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-1 bg-gray-700 rounded-full mt-1 overflow-hidden">
                      <div className="h-full bg-blue-500 rounded-full" style={{ width: `${p.share}%` }}></div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* State Profile Modal */}
      {selectedState && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[200] backdrop-blur-sm">
          <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col">
            <div className="p-6 border-b border-gray-800 flex justify-between items-center bg-gray-850 rounded-t-xl">
              <div>
                <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                  <span className="bg-blue-600 text-white text-sm font-bold px-2 py-1 rounded">{selectedState.state}</span>
                  {STATE_NAMES[selectedState.state] || selectedState.state} Profile
                </h2>
                <p className="text-sm text-gray-400 mt-1">Year: {selectedState.year}</p>
              </div>
              <button onClick={() => setSelectedState(null)} className="text-gray-400 hover:text-white p-2 hover:bg-gray-800 rounded-lg transition-colors">
                <X size={24} />
              </button>
            </div>
            
            {/* Tabs */}
            <div className="flex border-b border-gray-700 px-6">
              <button
                className={`py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
                  !selectedState.activeTab || selectedState.activeTab === 'interstate' 
                    ? 'border-blue-500 text-white' 
                    : 'border-transparent text-gray-400 hover:text-gray-300'
                }`}
                onClick={() => setSelectedState({ ...selectedState, activeTab: 'interstate' })}
              >
                Interstate Capacity
              </button>
              <button
                className={`py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
                  selectedState.activeTab === 'intrastate' 
                    ? 'border-blue-500 text-white' 
                    : 'border-transparent text-gray-400 hover:text-gray-300'
                }`}
                onClick={() => setSelectedState({ ...selectedState, activeTab: 'intrastate' })}
              >
                Intrastate Network
              </button>
              <button
                className={`py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
                  selectedState.activeTab === 'production' 
                    ? 'border-blue-500 text-white' 
                    : 'border-transparent text-gray-400 hover:text-gray-300'
                }`}
                onClick={() => setSelectedState({ ...selectedState, activeTab: 'production' })}
              >
                Production & Flow
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6">
              {(!selectedState.activeTab || selectedState.activeTab === 'interstate') ? (
                <>
                  {/* Summary Cards */}
                  <div className="grid grid-cols-2 gap-4 mb-8">
                    <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700/50">
                      <h3 className="text-sm font-medium text-gray-400 mb-1">Total Pipeline Inflow Capacity</h3>
                      <p className="text-2xl font-bold text-green-400">{selectedState.total_inflow?.toLocaleString()} <span className="text-sm text-gray-500 font-normal">MMcf/d</span></p>
                    </div>
                    <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700/50">
                      <h3 className="text-sm font-medium text-gray-400 mb-1">Total Pipeline Outflow Capacity</h3>
                      <p className="text-2xl font-bold text-blue-400">{selectedState.total_outflow?.toLocaleString()} <span className="text-sm text-gray-500 font-normal">MMcf/d</span></p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Inflow Section */}
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <Download size={20} className="text-green-500" />
                        Inflow Capacity
                      </h3>
                      <div className="space-y-4">
                        {selectedState.inflows?.map((conn: any, idx: number) => (
                          <div key={idx} className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
                            <div className="p-3 bg-gray-750 border-b border-gray-700 flex justify-between items-center">
                              <span className="font-bold text-white">From {conn.state}</span>
                              <span className="text-green-400 font-mono text-sm">{conn.capacity.toLocaleString()} MMcf/d</span>
                            </div>
                            <div className="p-2 space-y-1">
                              {conn.pipelines.slice(0, 3).map((p: any, pIdx: number) => (
                                <div key={pIdx} className="flex justify-between text-xs text-gray-400 px-2 py-1 hover:bg-gray-700/50 rounded cursor-pointer" onClick={() => {
                                    setSelectedState(null);
                                    // Need to find pipeline ID from name... tricky without ID in this response
                                    // Ideally backend should return ID.
                                }}>
                                  <span className="truncate pr-2">{p.name}</span>
                                  <span className="flex-shrink-0">{p.capacity.toLocaleString()}</span>
                                </div>
                              ))}
                              {conn.pipelines.length > 3 && (
                                <div className="text-xs text-gray-500 px-2 pt-1 text-center italic">
                                  + {conn.pipelines.length - 3} more pipelines
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                        {selectedState.inflows?.length === 0 && (
                          <div className="text-gray-500 text-sm italic p-4 text-center">No inflow connections found.</div>
                        )}
                      </div>
                    </div>

                    {/* Outflow Section */}
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <Download size={20} className="text-blue-500 rotate-180" />
                        Outflow Capacity
                      </h3>
                      <div className="space-y-4">
                        {selectedState.outflows?.map((conn: any, idx: number) => (
                          <div key={idx} className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
                            <div className="p-3 bg-gray-750 border-b border-gray-700 flex justify-between items-center">
                              <span className="font-bold text-white">To {conn.state}</span>
                              <span className="text-blue-400 font-mono text-sm">{conn.capacity.toLocaleString()} MMcf/d</span>
                            </div>
                            <div className="p-2 space-y-1">
                              {conn.pipelines.slice(0, 3).map((p: any, pIdx: number) => (
                                <div key={pIdx} className="flex justify-between text-xs text-gray-400 px-2 py-1 hover:bg-gray-700/50 rounded">
                                  <span className="truncate pr-2">{p.name}</span>
                                  <span className="flex-shrink-0">{p.capacity.toLocaleString()}</span>
                                </div>
                              ))}
                              {conn.pipelines.length > 3 && (
                                <div className="text-xs text-gray-500 px-2 pt-1 text-center italic">
                                  + {conn.pipelines.length - 3} more pipelines
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                        {selectedState.outflows?.length === 0 && (
                          <div className="text-gray-500 text-sm italic p-4 text-center">No outflow connections found.</div>
                        )}
                      </div>
                    </div>
                  </div>
                </>
              ) : selectedState.activeTab === 'intrastate' ? (
                <IntrastateTab stateCode={selectedState.state} />
              ) : (
                <ProductionFlowTab stateCode={selectedState.state} />
              )}
            </div>
          </div>
        </div>
      )}

      {/* Pipeline Profile Modal */}
      {selectedPipeline && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[200] backdrop-blur-sm">
          <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
            <div className="p-6 border-b border-gray-800 flex justify-between items-center bg-gray-850 rounded-t-xl">
              <div>
                <h2 className="text-2xl font-bold text-white">{selectedPipeline.name}</h2>
                <p className="text-sm text-gray-400 mt-1">Pipeline ID: {selectedPipeline.id}</p>
              </div>
              <button onClick={() => setSelectedPipeline(null)} className="text-gray-400 hover:text-white p-2 hover:bg-gray-800 rounded-lg transition-colors">
                <X size={24} />
              </button>
            </div>
            
            {/* Tabs */}
            <div className="flex border-b border-gray-700 px-6">
              <button
                className={`py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
                  !selectedPipeline.activeTab || selectedPipeline.activeTab === 'capacity' 
                    ? 'border-blue-500 text-white' 
                    : 'border-transparent text-gray-400 hover:text-gray-300'
                }`}
                onClick={() => setSelectedPipeline({ ...selectedPipeline, activeTab: 'capacity' })}
              >
                Capacity & Flow
              </button>
              {selectedPipeline.financials && selectedPipeline.financials.data_available && (
                <button
                  className={`py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
                    selectedPipeline.activeTab === 'financials' 
                      ? 'border-green-500 text-white' 
                      : 'border-transparent text-gray-400 hover:text-gray-300'
                  }`}
                  onClick={() => setSelectedPipeline({ ...selectedPipeline, activeTab: 'financials' })}
                >
                  Financial Performance
                </button>
              )}
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 space-y-8">
              {(!selectedPipeline.activeTab || selectedPipeline.activeTab === 'capacity') ? (
                <>
                  {/* History Chart */}
                  <div className="h-64 bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
                    <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                      Total System Capacity History
                    </h3>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={selectedPipeline.history}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                        <XAxis dataKey="year" stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                        <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `${val/1000}k`} />
                        <Tooltip 
                          contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }}
                          formatter={(val: number) => [`${val.toLocaleString()} MMcf/d`, 'Capacity']}
                        />
                        <Line type="monotone" dataKey="capacity" stroke="#3b82f6" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#60a5fa' }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Segments Table */}
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">Active Segments ({selectedPipeline.current_year})</h3>
                    <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
                      <table className="w-full text-sm text-left text-gray-300">
                        <thead className="text-xs text-gray-400 uppercase bg-gray-900/50">
                          <tr>
                            <th className="px-6 py-4 font-semibold">From</th>
                            <th className="px-6 py-4 font-semibold">To</th>
                            <th className="px-6 py-4 text-right font-semibold">Capacity (MMcf/d)</th>
                            <th className="px-6 py-4 text-right font-semibold">Share</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-700">
                          {selectedPipeline.segments.map((seg: any, idx: number) => {
                            const total = selectedPipeline.segments.reduce((acc: number, s: any) => acc + s.capacity, 0);
                            const percent = (seg.capacity / total) * 100;
                            return (
                              <tr key={idx} className="hover:bg-gray-700/50 transition-colors">
                                <td className="px-6 py-4 font-medium text-white">{seg.from}</td>
                                <td className="px-6 py-4 font-medium text-white">{seg.to}</td>
                                <td className="px-6 py-4 text-right font-mono text-blue-400">{seg.capacity.toLocaleString()}</td>
                                <td className="px-6 py-4 text-right">
                                  <div className="flex items-center justify-end gap-2">
                                    <span className="text-xs text-gray-500">{percent.toFixed(1)}%</span>
                                    <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                                      <div className="h-full bg-blue-500 rounded-full" style={{ width: `${percent}%` }}></div>
                                    </div>
                                  </div>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              ) : (
                <div className="space-y-6">
                  <div className="bg-green-900/10 border border-green-800 rounded-lg p-4 flex items-start gap-3">
                    <div className="p-2 bg-green-900/30 rounded-full text-green-400">
                      <DollarSign size={24} />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-white">{selectedPipeline.financials.company_name}</h3>
                      <p className="text-sm text-green-300">FERC Form 2 Financial Data ({selectedPipeline.financials.year})</p>
                    </div>
                    <Link 
                      to={`/finance/pipelines?search=${encodeURIComponent(selectedPipeline.financials.company_name)}`}
                      className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                    >
                      View Full Filing
                      <ArrowRight size={16} />
                    </Link>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-gray-800 p-4 rounded-xl border border-gray-700">
                      <h4 className="text-sm text-gray-400 mb-1">Operating Revenues</h4>
                      <p className="text-2xl font-bold text-white">${selectedPipeline.financials.operating_revenues?.toLocaleString()}</p>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-xl border border-gray-700">
                      <h4 className="text-sm text-gray-400 mb-1">Operating Expenses</h4>
                      <p className="text-2xl font-bold text-white">${selectedPipeline.financials.operating_expenses?.toLocaleString()}</p>
                    </div>
                    <div className="bg-gray-800 p-4 rounded-xl border border-gray-700">
                      <h4 className="text-sm text-gray-400 mb-1">Net Income</h4>
                      <p className={`text-2xl font-bold ${selectedPipeline.financials.net_income >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        ${selectedPipeline.financials.net_income?.toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                    <h3 className="text-lg font-semibold text-white mb-4">Profitability Overview</h3>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={[
                          { name: 'Revenues', value: selectedPipeline.financials.operating_revenues, fill: '#3b82f6' },
                          { name: 'Expenses', value: selectedPipeline.financials.operating_expenses, fill: '#ef4444' },
                          { name: 'Net Income', value: selectedPipeline.financials.net_income, fill: '#10b981' }
                        ]} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
                          <XAxis type="number" stroke="#9ca3af" tickFormatter={(val) => `$${val/1000000}M`} />
                          <YAxis dataKey="name" type="category" stroke="#9ca3af" width={100} />
                          <Tooltip 
                            cursor={{fill: 'transparent'}}
                            contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff' }}
                            formatter={(val: number) => [`$${val.toLocaleString()}`, 'Amount']}
                          />
                          <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={40}>
                            {
                              [
                                { name: 'Revenues', value: selectedPipeline.financials.operating_revenues, fill: '#3b82f6' },
                                { name: 'Expenses', value: selectedPipeline.financials.operating_expenses, fill: '#ef4444' },
                                { name: 'Net Income', value: selectedPipeline.financials.net_income, fill: '#10b981' }
                              ].map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.fill} />
                              ))
                            }
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NaturalGasPipelines;