import { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { X, Maximize2, Minimize2 } from 'lucide-react';

const TransmissionMap = () => {
  const [lines, setLines] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [minVoltage, setMinVoltage] = useState(0); // Default to all
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [selectedLine, setSelectedLine] = useState<any>(null);
  const [substations, setSubstations] = useState<any>(null);
  const [showSubstations, setShowSubstations] = useState(true);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [usStates, setUsStates] = useState<any>(null);
  const [transform, setTransform] = useState({ k: 1, x: 0, y: 0 });
  
  const svgRef = useRef<SVGSVGElement>(null);
  const gRef = useRef<SVGGElement>(null);

  useEffect(() => {
    // Fetch US States
    fetch('http://localhost:8000/reference/us_states')
      .then(res => res.json())
      .then(data => setUsStates(data))
      .catch(err => console.error(err));

    // Fetch Substations
    fetch('http://localhost:8000/spatial/substations')
      .then(res => res.json())
      .then(data => setSubstations(data))
      .catch(err => console.error(err));

    // Fetch Lines
    const fetchLines = async () => {
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/spatial/transmission-lines?min_voltage=${minVoltage}&limit=5000`);
        const data = await res.json();
        setLines(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchLines();
  }, [minVoltage]);

  // D3 Zoom
  useEffect(() => {
    if (!svgRef.current || !gRef.current) return;

    const zoom = d3.zoom()
      .scaleExtent([1, 100])
      .on('zoom', (event) => {
        d3.select(gRef.current).attr('transform', event.transform);
        setZoomLevel(event.transform.k);
        setTransform(event.transform);
      });

    d3.select(svgRef.current).call(zoom as any);
  }, [lines]); // Re-attach zoom when lines change/re-render

  // Projection helper (Albers USA or Mercator)
  const projection = d3.geoAlbersUsa().scale(1300).translate([400, 300]);

  return (
    <div className={`flex flex-col space-y-4 ${isFullScreen ? 'fixed inset-0 z-50 bg-gray-900 p-4' : 'h-full'}`}>
      <div className="flex justify-between items-center bg-gray-800 p-4 rounded-lg">
        <h3 className="text-lg font-semibold text-white">Transmission Grid Topology</h3>
        <div className="flex items-center gap-4">
          <label className="text-sm text-gray-300">Min Voltage (kV):</label>
          <select 
            value={minVoltage} 
            onChange={(e) => setMinVoltage(Number(e.target.value))}
            className="bg-gray-700 text-white rounded px-2 py-1 border border-gray-600"
          >
            <option value="0">All Voltages</option>
            <option value="69">69+ kV</option>
            <option value="138">138+ kV</option>
            <option value="230">230+ kV</option>
            <option value="345">345+ kV</option>
            <option value="500">500+ kV</option>
            <option value="765">765+ kV</option>
          </select>
          <button 
            onClick={() => setShowSubstations(!showSubstations)}
            className={`px-3 py-1 rounded text-xs font-medium border ${showSubstations ? 'bg-blue-600 border-blue-500 text-white' : 'bg-gray-700 border-gray-600 text-gray-300'}`}
          >
            Substations
          </button>
          <button 
            onClick={() => setIsFullScreen(!isFullScreen)}
            className="p-2 bg-gray-700 rounded hover:bg-gray-600 text-white"
            title={isFullScreen ? "Exit Full Screen" : "Full Screen"}
          >
            {isFullScreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
          </button>
        </div>
      </div>

      <div className="flex-1 bg-gray-900 rounded-lg border border-gray-700 relative overflow-hidden">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900/80 z-10">
            <div className="text-blue-400">Loading Grid Topology...</div>
          </div>
        )}
        
        {/* SVG Renderer for GeoJSON */}
        <svg 
          ref={svgRef}
          width="100%" 
          height="100%" 
          viewBox="0 0 800 600" 
          preserveAspectRatio="xMidYMid meet"
          className="cursor-move"
        >
           <g ref={gRef}>
             {/* Draw US States Background */}
             {usStates?.features?.map((feature: any, i: number) => {
               const pathGenerator = d3.geoPath().projection(projection);
               return (
                 <path 
                   key={`state-${i}`} 
                   d={pathGenerator(feature) || ''} 
                   fill="transparent" 
                   stroke="#6b7280" 
                   strokeWidth={1} 
                 />
               );
             })}
             
             {/* Draw Transmission Lines */}
             {lines?.features?.map((feature: any, i: number) => {
               const voltage = feature.properties.voltage;
               let color = '#6b7280'; // Default gray
               let width = 0.5;
               
               if (voltage >= 765) { color = '#ef4444'; width = 2; } // Red
               else if (voltage >= 500) { color = '#f97316'; width = 1.5; } // Orange
               else if (voltage >= 345) { color = '#eab308'; width = 1.2; } // Yellow
               else if (voltage >= 230) { color = '#84cc16'; width = 1; } // Lime
               else if (voltage >= 138) { color = '#22c55e'; width = 0.8; } // Green
               
               // Handle MultiLineString
               if (feature.geometry.type === 'MultiLineString') {
                 return feature.geometry.coordinates.map((segment: any[], j: number) => {
                   const pathGenerator = d3.geoPath().projection(projection);
                   const lineString = { type: 'LineString', coordinates: segment };
                   return (
                    <path 
                      key={`${i}-${j}`} 
                      d={pathGenerator(lineString as any) || ''} 
                      stroke={color} 
                      strokeWidth={width} 
                      fill="none" 
                      opacity={0.8}
                      vectorEffect="non-scaling-stroke"
                      className="hover:stroke-white hover:stroke-[3px] transition-all cursor-pointer"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedLine(feature.properties);
                      }}
                    />
                   );
                 });
               } else if (feature.geometry.type === 'LineString') {
                  const pathGenerator = d3.geoPath().projection(projection);
                  return (
                    <path 
                      key={i} 
                      d={pathGenerator(feature.geometry) || ''} 
                      stroke={color} 
                      strokeWidth={width} 
                      fill="none" 
                      opacity={0.8}
                      vectorEffect="non-scaling-stroke"
                      className="hover:stroke-white hover:stroke-[3px] transition-all cursor-pointer"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedLine(feature.properties);
                      }}
                    />
                  );
               }
               return null;
             })}

             {/* Draw Substations */}
             {showSubstations && substations?.features?.map((feature: any, i: number) => {
                const [long, lat] = feature.geometry.coordinates;
                const coords = projection([long, lat]);
                if (!coords) return null;
                const [x, y] = coords;

                // Scale radius: smaller when zoomed out, larger when zoomed in (but not too large)
                // At zoom 1: r = 1.5
                // At zoom 8: r = 3
                const radius = Math.max(1.5, 3 / Math.sqrt(zoomLevel));

                return (
                  <g key={`sub-${i}`}>
                    <circle
                      cx={x}
                      cy={y}
                      r={Math.max(1, 3 / Math.sqrt(zoomLevel))} 
                      fill="#fbbf24" 
                      stroke="#000"
                      strokeWidth={0.5 / zoomLevel}
                      className="cursor-pointer hover:fill-white"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedLine({
                          owner: "Substation",
                          voltage: `${feature.properties.min_voltage}-${feature.properties.max_voltage} kV`,
                          status: feature.properties.status,
                          type: feature.properties.name
                        });
                      }}
                    />
                    {zoomLevel > 2.5 && (
                      <text
                        x={x}
                        y={y - (Math.max(1, 3 / Math.sqrt(zoomLevel))) - (2 / zoomLevel)}
                        textAnchor="middle"
                        fill="white"
                        fontSize={12 / Math.sqrt(zoomLevel)}
                        className="pointer-events-none select-none drop-shadow-md font-sans font-bold"
                        style={{ textShadow: '0px 0px 3px rgba(0,0,0,0.8)' }}
                      >
                        {feature.properties.name}
                      </text>
                    )}
                  </g>
                );
             })}
           </g>
        </svg>
        
        {/* Legend */}
        <div className="absolute bottom-4 right-4 bg-gray-800/90 p-3 rounded border border-gray-700 text-xs pointer-events-none">
          <div className="font-semibold text-gray-300 mb-2">Voltage Class</div>
          <div className="flex items-center gap-2 mb-1"><div className="w-3 h-0.5 bg-red-500"></div> <span className="text-gray-400">765+ kV</span></div>
          <div className="flex items-center gap-2 mb-1"><div className="w-3 h-0.5 bg-orange-500"></div> <span className="text-gray-400">500-764 kV</span></div>
          <div className="flex items-center gap-2 mb-1"><div className="w-3 h-0.5 bg-yellow-500"></div> <span className="text-gray-400">345-499 kV</span></div>
          <div className="flex items-center gap-2 mb-1"><div className="w-3 h-0.5 bg-lime-500"></div> <span className="text-gray-400">230-344 kV</span></div>
          <div className="flex items-center gap-2"><div className="w-3 h-0.5 bg-green-500"></div> <span className="text-gray-400">138-229 kV</span></div>
        </div>

        {/* Info Modal */}
        {selectedLine && (
          <div className="absolute top-4 left-4 bg-gray-800 p-4 rounded border border-gray-600 shadow-lg w-64 z-20">
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-bold text-white">Line Details</h4>
              <button onClick={() => setSelectedLine(null)} className="text-gray-400 hover:text-white">
                <X size={16} />
              </button>
            </div>
            <div className="space-y-2 text-sm">
              <div>
                <span className="text-gray-400 block">Owner</span>
                <span className="text-white">{selectedLine.owner}</span>
              </div>
              <div>
                <span className="text-gray-400 block">Voltage</span>
                <span className="text-white">{selectedLine.voltage} kV ({selectedLine.class})</span>
              </div>
              <div>
                <span className="text-gray-400 block">Status</span>
                <span className="text-white">{selectedLine.status}</span>
              </div>
              <div>
                <span className="text-gray-400 block">Type</span>
                <span className="text-white">{selectedLine.type}</span>
              </div>
              {selectedLine.sub_1 && (
                <div>
                  <span className="text-gray-400 block">From</span>
                  <span className="text-white">{selectedLine.sub_1}</span>
                </div>
              )}
              {selectedLine.sub_2 && (
                <div>
                  <span className="text-gray-400 block">To</span>
                  <span className="text-white">{selectedLine.sub_2}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TransmissionMap;
