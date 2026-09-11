import React, { useState, useMemo, useEffect } from 'react';
import { 
  Shield, 
  Sparkles, 
  Hammer, 
  Compass, 
  Share2, 
  Info, 
  ExternalLink, 
  Layers, 
  Zap, 
  Award, 
  ChevronRight, 
  Search, 
  Flame,
  Filter,
  Maximize2,
  RefreshCw,
  Eye,
  Sliders,
  Users
} from 'lucide-react';

// ============================================================================
// Types & Domain Schemas (Matching Valheim Chronicler Archive SDK)
// ============================================================================

export interface KinshipNode {
  id: string;
  name: string;
  role: string;
  avatar?: string;
  rank: 'Megabuilder' | 'Major Architect' | 'Homestead Artisan' | 'Runic Ally';
  kinshipScore: number; // Scaled 0 - 100
  sharedPieces: number;
  sharedBuilds: number;
  keyBuildId: string;
  keyBuildName: string;
  keyBuildPieces: number;
  eraContext: number[];
  color: string;
  x?: number;
  y?: number;
}

export interface SharedBuildLink {
  source: string;
  target: string;
  weight: number; // Kinship score
  sharedBuildsCount: number;
  monumentId: string;
}

// Sample Archival Dataset centered on Ditseey (Rank #4 Megabuilder)
const SEED_TARGET_BUILDER = {
  id: 'b_ditseey',
  name: 'Ditseey',
  title: 'Rune-Witch & Seaside Megabuilder',
  rank: 'Megabuilder',
  totalPieces: 80151,
  totalAlbums: 112,
  activeEras: [11, 12, 14, 16, 17],
  beaconStatus: 'ACTIVE IN REALM · CARVING RUNES',
  avatar: 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=160&auto=format&fit=crop&q=80'
};

const KINSHIP_COLLABORATORS: KinshipNode[] = [
  {
    id: 'b_bluecollar',
    name: 'Bluecollar',
    role: 'Co-Architect (Shield-Wall)',
    rank: 'Megabuilder',
    kinshipScore: 96.4,
    sharedPieces: 15807,
    sharedBuilds: 12,
    keyBuildId: 'bd1ac417',
    keyBuildName: 'The Grand Bastion Complex',
    keyBuildPieces: 15807,
    eraContext: [14],
    color: '#f59e0b', // Amber-500
  },
  {
    id: 'b_qtip',
    name: 'Qtip',
    role: 'Monolith Partner',
    rank: 'Major Architect',
    kinshipScore: 89.1,
    sharedPieces: 8420,
    sharedBuilds: 9,
    keyBuildId: 'cc73d139',
    keyBuildName: 'Deep Meadow Monolith',
    keyBuildPieces: 4413,
    eraContext: [11, 12],
    color: '#38bdf8', // Sky-400
  },
  {
    id: 'b_headcase',
    name: 'Head Case',
    role: 'Homestead Arch-Partner',
    rank: 'Megabuilder',
    kinshipScore: 84.6,
    sharedPieces: 6150,
    sharedBuilds: 14,
    keyBuildId: 'ce85e506',
    keyBuildName: 'Highland Rampart Keep',
    keyBuildPieces: 4045,
    eraContext: [11, 12],
    color: '#10b981', // Emerald-500
  },
  {
    id: 'b_revnafey',
    name: 'Revna Fey',
    role: 'Timber Framing Lead',
    rank: 'Major Architect',
    kinshipScore: 78.2,
    sharedPieces: 5871,
    sharedBuilds: 6,
    keyBuildId: 'fa06785d',
    keyBuildName: 'Citadel of the Runewitch',
    keyBuildPieces: 5871,
    eraContext: [14],
    color: '#a855f7', // Purple-500
  },
  {
    id: 'b_reinaborg',
    name: 'Reina Borg',
    role: 'Guild Shieldmaiden Lead',
    rank: 'Megabuilder',
    kinshipScore: 73.5,
    sharedPieces: 3950,
    sharedBuilds: 5,
    keyBuildId: 'b0bcd136',
    keyBuildName: 'High Guild Hall of Valhalla',
    keyBuildPieces: 742,
    eraContext: [12, 14],
    color: '#f43f5e', // Rose-500
  },
  {
    id: 'b_alashal',
    name: 'Alashal',
    role: 'Rampart Mason',
    rank: 'Homestead Artisan',
    kinshipScore: 68.9,
    sharedPieces: 2687,
    sharedBuilds: 4,
    keyBuildId: 'bd1ac417',
    keyBuildName: 'Cantilevered Sea Spire',
    keyBuildPieces: 15807,
    eraContext: [14],
    color: '#fb923c', // Orange-400
  },
  {
    id: 'b_argie',
    name: 'Argie',
    role: 'Colossus Fort Lead',
    rank: 'Megabuilder',
    kinshipScore: 62.0,
    sharedPieces: 10151,
    sharedBuilds: 3,
    keyBuildId: 'f6924293',
    keyBuildName: 'Argie Mountain Bastion',
    keyBuildPieces: 10151,
    eraContext: [11],
    color: '#eab308', // Yellow-500
  },
  {
    id: 'b_wootsie',
    name: 'Wootsie',
    role: 'Stone Foundation Ally',
    rank: 'Homestead Artisan',
    kinshipScore: 54.3,
    sharedPieces: 3586,
    sharedBuilds: 3,
    keyBuildId: '130ed533',
    keyBuildName: 'Iron Gate Citadel',
    keyBuildPieces: 3586,
    eraContext: [12],
    color: '#14b8a6', // Teal-500
  }
];

// ============================================================================
// Main Component: Valheim Kinship Graph & Shield-Wall Dashboard
// ============================================================================

export default function ValheimKinshipDashboard() {
  const [selectedNode, setSelectedNode] = useState<KinshipNode>(KINSHIP_COLLABORATORS[0]);
  const [hoveredNode, setHoveredNode] = useState<KinshipNode | null>(null);
  const [selectedEra, setSelectedEra] = useState<number | 'all'>('all');
  const [minPiecesFilter, setMinPiecesFilter] = useState<number>(1000);
  const [simulationSpeed, setSimulationSpeed] = useState<'realtime' | 'static'>('realtime');
  const [activeTab, setActiveTab] = useState<'matrix' | 'radial' | 'monuments'>('radial');
  const [searchQuery, setSearchQuery] = useState('');

  // Filter collaborators based on controls
  const filteredCollaborators = useMemo(() => {
    return KINSHIP_COLLABORATORS.filter(c => {
      const matchesEra = selectedEra === 'all' || c.eraContext.includes(selectedEra);
      const matchesPieces = c.sharedPieces >= minPiecesFilter;
      const matchesSearch = c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                            c.role.toLowerCase().includes(searchQuery.toLowerCase()) ||
                            c.keyBuildName.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesEra && matchesPieces && matchesSearch;
    });
  }, [selectedEra, minPiecesFilter, searchQuery]);

  // Calculate coordinates for Radial Shield-Wall layout
  const radialNodes = useMemo(() => {
    const center = { x: 300, y: 280 };
    const radius = 190;
    return filteredCollaborators.map((c, i, arr) => {
      const angle = (i / (arr.length || 1)) * 2 * Math.PI - Math.PI / 2;
      return {
        ...c,
        x: center.x + radius * Math.cos(angle),
        y: center.y + radius * Math.sin(angle),
        angle
      };
    });
  }, [filteredCollaborators]);

  return (
    <div className="min-h-screen bg-[#090f16] text-[#e2e8f0] font-sans antialiased p-4 md:p-8 selection:bg-amber-500/30 selection:text-amber-200">
      
      {/* --- Top Header & Telemetry Breadcrumbs --- */}
      <header className="max-w-7xl mx-auto mb-8 border-b border-[#1f2937]/80 pb-6">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 shadow-[0_0_15px_rgba(245,158,11,0.15)]">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 text-xs font-mono tracking-widest text-amber-500/80 uppercase">
                <span>The Comfy Community</span>
                <span>/</span>
                <span>FastAPI Graph Matrix Engine</span>
              </div>
              <h1 className="text-2xl md:text-3xl font-serif font-bold tracking-tight text-white flex items-center gap-3">
                Viking Kinship & Shield-Wall Top 8
                <span className="text-xs font-mono font-normal px-2.5 py-0.5 rounded-full border border-emerald-500/40 bg-emerald-950/40 text-emerald-400">
                  NumPy Sparse CSR · Live
                </span>
              </h1>
            </div>
          </div>

          {/* Quick Engine Telemetry Badges */}
          <div className="flex items-center gap-2">
            <div className="px-3 py-1.5 rounded-md bg-[#161c24] border border-[#2d3748] text-xs font-mono">
              <span className="text-gray-400">Target: </span>
              <span className="text-amber-400 font-semibold">{SEED_TARGET_BUILDER.name}</span>
            </div>
            <div className="px-3 py-1.5 rounded-md bg-[#161c24] border border-[#2d3748] text-xs font-mono hidden sm:block">
              <span className="text-gray-400">Formula: </span>
              <span className="text-teal-400 font-mono">Σ min(P_A, P_B) · log₁₀(Pieces)</span>
            </div>
          </div>
        </div>

        {/* Target Profile Mini Header Ribbon */}
        <div className="bg-[#121822] border border-[#222c3a] rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-14 h-14 rounded-xl overflow-hidden border-2 border-amber-500/50 shadow-md">
                <img 
                  src={SEED_TARGET_BUILDER.avatar} 
                  alt={SEED_TARGET_BUILDER.name} 
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-emerald-500 border-2 border-[#121822] flex items-center justify-center">
                <Zap className="w-3 h-3 text-black" />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white tracking-wide">{SEED_TARGET_BUILDER.name}</h2>
                <span className="text-xs px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 font-medium">
                  {SEED_TARGET_BUILDER.rank}
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">{SEED_TARGET_BUILDER.title}</p>
              <div className="flex items-center gap-3 text-xs font-mono text-gray-400 mt-1">
                <span>{SEED_TARGET_BUILDER.totalPieces.toLocaleString()} pieces</span>
                <span>•</span>
                <span>{SEED_TARGET_BUILDER.totalAlbums} albums</span>
                <span>•</span>
                <span className="text-emerald-400">{SEED_TARGET_BUILDER.beaconStatus}</span>
              </div>
            </div>
          </div>

          {/* Quick Tabs */}
          <div className="flex items-center gap-1 bg-[#090f16] p-1 rounded-lg border border-[#222c3a]">
            <button
              onClick={() => setActiveTab('radial')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'radial' 
                  ? 'bg-amber-500 text-black font-semibold shadow' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Radial Shield-Wall
            </button>
            <button
              onClick={() => setActiveTab('matrix')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'matrix' 
                  ? 'bg-amber-500 text-black font-semibold shadow' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Attribution Matrix
            </button>
            <button
              onClick={() => setActiveTab('monuments')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                activeTab === 'monuments' 
                  ? 'bg-amber-500 text-black font-semibold shadow' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Key Monuments
            </button>
          </div>
        </div>
      </header>

      {/* --- Main Dashboard Grid --- */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left / Center 8 Cols: Interactive Visualization Viewport */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          
          {/* Controls Bar */}
          <div className="bg-[#121822] border border-[#222c3a] rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter kin by name, role, monument..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-[#090f16] border border-[#222c3a] rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-amber-500 w-52 sm:w-64"
                />
              </div>

              {/* Era Filter Pill Selector */}
              <div className="flex items-center gap-1">
                <span className="text-xs text-gray-400 mr-1 hidden sm:inline">Era:</span>
                {[ 'all', 11, 12, 14 ].map((era) => (
                  <button
                    key={era}
                    onClick={() => setSelectedEra(era as any)}
                    className={`px-2.5 py-1 rounded text-xs font-mono transition-all ${
                      selectedEra === era
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold'
                        : 'bg-[#161c24] text-gray-400 border border-[#222c3a] hover:text-white'
                    }`}
                  >
                    {era === 'all' ? 'All' : `E${era}`}
                  </button>
                ))}
              </div>
            </div>

            {/* Threshold Slider */}
            <div className="flex items-center gap-2 text-xs font-mono text-gray-400">
              <Sliders className="w-3.5 h-3.5 text-amber-500" />
              <span>Min Pieces:</span>
              <input
                type="range"
                min="500"
                max="10000"
                step="500"
                value={minPiecesFilter}
                onChange={(e) => setMinPiecesFilter(Number(e.target.value))}
                className="w-20 accent-amber-500 cursor-pointer"
              />
              <span className="text-amber-400 min-w-[45px]">{minPiecesFilter}</span>
            </div>
          </div>

          {/* Visualization Canvas Container */}
          <div className="bg-[#0e141c] border border-[#222c3a] rounded-2xl p-6 relative overflow-hidden shadow-2xl flex flex-col items-center justify-center min-h-[580px]">
            
            {/* Background Ambient SVG Grid & Rune Rings */}
            <div className="absolute inset-0 pointer-events-none opacity-20">
              <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <radialGradient id="hearthGlow" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#090f16" stopOpacity="0" />
                  </radialGradient>
                </defs>
                <circle cx="50%" cy="50%" r="280" fill="url(#hearthGlow)" />
                <circle cx="50%" cy="50%" r="200" stroke="#f59e0b" strokeWidth="1" strokeDasharray="4 8" fill="none" opacity="0.3" />
                <circle cx="50%" cy="50%" r="130" stroke="#38bdf8" strokeWidth="1" strokeDasharray="2 6" fill="none" opacity="0.2" />
              </svg>
            </div>

            {/* TAB 1: RADIAL SHIELD-WALL GRAPH */}
            {activeTab === 'radial' && (
              <div className="relative w-full max-w-[620px] aspect-square flex items-center justify-center">
                <svg className="w-full h-full overflow-visible" viewBox="0 0 600 560">
                  {/* Connection Lines from Center to Collaborators */}
                  {radialNodes.map((node) => {
                    const isHovered = hoveredNode?.id === node.id;
                    const isSelected = selectedNode?.id === node.id;
                    const strokeColor = isSelected || isHovered ? node.color : '#334155';
                    const strokeWidth = isSelected || isHovered ? Math.max(3, (node.kinshipScore / 100) * 6) : 1.5;
                    const strokeOpacity = isSelected || isHovered ? 0.9 : 0.4;

                    return (
                      <g key={`line-${node.id}`}>
                        <line
                          x1={300}
                          y1={280}
                          x2={node.x}
                          y2={node.y}
                          stroke={strokeColor}
                          strokeWidth={strokeWidth}
                          strokeOpacity={strokeOpacity}
                          strokeDasharray={isSelected ? 'none' : '4 4'}
                          className="transition-all duration-300"
                        />
                        {/* Overlap Score Tag midway */}
                        {node.x && node.y && (
                          <g transform={`translate(${(300 + node.x) / 2}, ${(280 + node.y) / 2})`}>
                            <rect
                              x="-18"
                              y="-10"
                              width="36"
                              height="20"
                              rx="4"
                              fill="#090f16"
                              stroke={isSelected || isHovered ? node.color : '#1e293b'}
                              strokeWidth="1"
                            />
                            <text
                              textAnchor="middle"
                              dy="4"
                              className="text-[10px] font-mono font-bold"
                              fill={isSelected || isHovered ? node.color : '#94a3b8'}
                            >
                              {node.kinshipScore.toFixed(0)}
                            </text>
                          </g>
                        )}
                      </g>
                    );
                  })}

                  {/* Central Node: Ditseey */}
                  <g transform="translate(300, 280)" className="cursor-pointer">
                    <circle r="46" fill="#121822" stroke="#f59e0b" strokeWidth="2.5" className="shadow-lg" />
                    <circle r="40" fill="#1e293b" />
                    <image
                      href={SEED_TARGET_BUILDER.avatar}
                      x="-36"
                      y="-36"
                      width="72"
                      height="72"
                      clipPath="url(#centerClip)"
                      className="rounded-full"
                    />
                    <clipPath id="centerClip">
                      <circle cx="0" cy="0" r="36" />
                    </clipPath>
                    <circle r="46" fill="none" stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="3 6" className="animate-spin-slow origin-center" />
                    <text textAnchor="middle" y="62" className="text-xs font-bold font-serif fill-white tracking-wider">
                      {SEED_TARGET_BUILDER.name}
                    </text>
                    <text textAnchor="middle" y="76" className="text-[10px] font-mono fill-amber-400">
                      80,151 Pieces
                    </text>
                  </g>

                  {/* Satellite Collaborator Nodes */}
                  {radialNodes.map((node) => {
                    const isSelected = selectedNode?.id === node.id;
                    const isHovered = hoveredNode?.id === node.id;
                    const nodeRadius = 24 + (node.kinshipScore / 100) * 10;

                    return (
                      <g
                        key={`node-${node.id}`}
                        transform={`translate(${node.x}, ${node.y})`}
                        onMouseEnter={() => setHoveredNode(node)}
                        onMouseLeave={() => setHoveredNode(null)}
                        onClick={() => setSelectedNode(node)}
                        className="cursor-pointer group"
                      >
                        {/* Outer Glow Halo on Selection */}
                        {(isSelected || isHovered) && (
                          <circle
                            r={nodeRadius + 8}
                            fill={node.color}
                            fillOpacity="0.2"
                            className="animate-pulse"
                          />
                        )}

                        {/* Node Body */}
                        <circle
                          r={nodeRadius}
                          fill="#121822"
                          stroke={isSelected || isHovered ? node.color : '#334155'}
                          strokeWidth={isSelected ? 3 : 1.8}
                          className="transition-all duration-200 group-hover:scale-105"
                        />

                        {/* Node Initials or Icon */}
                        <text
                          textAnchor="middle"
                          dy="5"
                          className="text-xs font-bold font-mono select-none"
                          fill={isSelected || isHovered ? node.color : '#e2e8f0'}
                        >
                          {node.name.slice(0, 2).toUpperCase()}
                        </text>

                        {/* Label Badge */}
                        <g transform={`translate(0, ${nodeRadius + 14})`}>
                          <rect
                            x="-45"
                            y="-10"
                            width="90"
                            height="20"
                            rx="4"
                            fill="#090f16"
                            stroke={isSelected ? node.color : '#1e293b'}
                            strokeWidth="1"
                          />
                          <text
                            textAnchor="middle"
                            dy="4"
                            className="text-[11px] font-medium font-sans select-none"
                            fill={isSelected ? '#ffffff' : '#cbd5e1'}
                          >
                            {node.name}
                          </text>
                        </g>

                        {/* Role Subtext */}
                        <text
                          textAnchor="middle"
                          y={nodeRadius + 32}
                          className="text-[9px] font-mono select-none"
                          fill={isSelected ? node.color : '#64748b'}
                        >
                          {node.role.split(' ')[0]}
                        </text>
                      </g>
                    );
                  })}
                </svg>

                {/* Floating Bottom Explainer Pill */}
                <div className="absolute bottom-3 bg-[#121822]/90 backdrop-blur-md border border-[#222c3a] px-3 py-1.5 rounded-full text-xs font-mono text-gray-400 flex items-center gap-2 shadow-lg">
                  <Info className="w-3.5 h-3.5 text-amber-400" />
                  <span>Click any node to inspect collaborative piece splits</span>
                </div>
              </div>
            )}

            {/* TAB 2: ATTRIBUTION MATRIX VIEW */}
            {activeTab === 'matrix' && (
              <div className="w-full overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead>
                    <tr className="border-b border-[#222c3a] text-gray-400 bg-[#121822]">
                      <th className="p-3">Collaborator</th>
                      <th className="p-3">Norse Role Tag</th>
                      <th className="p-3 text-right">Shared Pieces</th>
                      <th className="p-3 text-right">Shared Builds</th>
                      <th className="p-3 text-right">Kinship Score</th>
                      <th className="p-3">Key Shared Monument</th>
                      <th className="p-3 text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1e293b]/60">
                    {filteredCollaborators.map((c) => (
                      <tr 
                        key={c.id} 
                        onClick={() => setSelectedNode(c)}
                        className={`cursor-pointer transition-colors ${
                          selectedNode.id === c.id 
                            ? 'bg-amber-500/10 text-white' 
                            : 'hover:bg-[#161c24] text-gray-300'
                        }`}
                      >
                        <td className="p-3 flex items-center gap-2 font-bold text-white">
                          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: c.color }} />
                          {c.name}
                        </td>
                        <td className="p-3 text-gray-400">{c.role}</td>
                        <td className="p-3 text-right font-semibold text-amber-400">
                          {c.sharedPieces.toLocaleString()}
                        </td>
                        <td className="p-3 text-right text-gray-300">{c.sharedBuilds}</td>
                        <td className="p-3 text-right font-bold text-teal-400">{c.kinshipScore.toFixed(1)}</td>
                        <td className="p-3 text-gray-400 truncate max-w-[160px]">{c.keyBuildName}</td>
                        <td className="p-3 text-center">
                          <button 
                            onClick={(e) => { e.stopPropagation(); setSelectedNode(c); }}
                            className="px-2 py-1 rounded bg-[#1e293b] hover:bg-amber-500 hover:text-black transition text-[10px]"
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* TAB 3: KEY MONUMENTS VIEW */}
            {activeTab === 'monuments' && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full p-2">
                {filteredCollaborators.map((c) => (
                  <div
                    key={c.id}
                    onClick={() => setSelectedNode(c)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${
                      selectedNode.id === c.id
                        ? 'bg-[#161c24] border-amber-500/60 shadow-[0_0_20px_rgba(245,158,11,0.15)]'
                        : 'bg-[#121822] border-[#222c3a] hover:border-[#374151]'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div>
                        <span className="text-[10px] font-mono text-amber-400 uppercase tracking-wider">
                          Build {c.keyBuildId} · Era {c.eraContext[0]}
                        </span>
                        <h4 className="text-sm font-serif font-bold text-white">{c.keyBuildName}</h4>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#1e293b] text-gray-300">
                        {c.keyBuildPieces.toLocaleString()} pcs
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mb-3 line-clamp-2">
                      Key collaborative anchor between <strong className="text-white">Ditseey</strong> and <strong className="text-white">{c.name}</strong> ({c.role}).
                    </p>
                    <div className="flex items-center justify-between text-xs font-mono pt-2 border-t border-[#1e293b]">
                      <span className="text-gray-400">Kinship Score</span>
                      <span className="font-bold text-teal-400">{c.kinshipScore} / 100</span>
                    </div>
                  </div>
                ))}
              </div>
            )}

          </div>

          {/* Quick Mathematical Formula Callout */}
          <div className="bg-[#121822] border border-[#222c3a] rounded-xl p-4 flex items-center justify-between text-xs font-mono text-gray-400">
            <div className="flex items-center gap-3">
              <Zap className="w-4 h-4 text-amber-400 shrink-0" />
              <span>
                Computed via SciPy sparse CSR projection over <strong className="text-white">2,585 registered builders</strong> and <strong className="text-white">12,102 build clusters</strong>.
              </span>
            </div>
            <button 
              onClick={() => { setSelectedEra('all'); setMinPiecesFilter(1000); setSearchQuery(''); }}
              className="flex items-center gap-1 text-amber-400 hover:underline shrink-0"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reset Filters</span>
            </button>
          </div>

        </div>

        {/* Right 4 Cols: Selected Collaborator Deep Attribution Inspector */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          
          {/* Detail Card */}
          <div className="bg-[#121822] border border-[#222c3a] rounded-2xl p-6 shadow-xl relative overflow-hidden">
            {/* Accent Top Border */}
            <div 
              className="absolute top-0 left-0 right-0 h-1.5 transition-all duration-300"
              style={{ backgroundColor: selectedNode.color }}
            />

            {/* Header / Avatar */}
            <div className="flex items-start justify-between gap-4 mb-5 pt-2">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
                    {selectedNode.rank}
                  </span>
                  <span className="text-[10px] font-mono text-gray-400">
                    ID: {selectedNode.id}
                  </span>
                </div>
                <h3 className="text-xl font-serif font-bold text-white tracking-tight">
                  {selectedNode.name}
                </h3>
                <p className="text-xs font-medium text-amber-400 mt-0.5">
                  {selectedNode.role}
                </p>
              </div>

              {/* Kinship Badge Score Dial */}
              <div className="flex flex-col items-center justify-center p-3 rounded-xl bg-[#090f16] border border-[#222c3a] min-w-[70px]">
                <span className="text-[10px] font-mono text-gray-400 uppercase">Kinship</span>
                <span className="text-lg font-mono font-bold text-teal-400">
                  {selectedNode.kinshipScore.toFixed(1)}
                </span>
                <span className="text-[9px] font-mono text-gray-500">/ 100</span>
              </div>
            </div>

            {/* Metrics Breakdown Grid */}
            <div className="grid grid-cols-2 gap-3 mb-6 font-mono">
              <div className="bg-[#090f16] p-3 rounded-lg border border-[#1e293b]">
                <span className="text-[10px] text-gray-500 uppercase block mb-1">Shared Pieces</span>
                <span className="text-sm font-bold text-amber-400">
                  {selectedNode.sharedPieces.toLocaleString()}
                </span>
              </div>
              <div className="bg-[#090f16] p-3 rounded-lg border border-[#1e293b]">
                <span className="text-[10px] text-gray-500 uppercase block mb-1">Shared Builds</span>
                <span className="text-sm font-bold text-white">
                  {selectedNode.sharedBuilds} Monuments
                </span>
              </div>
              <div className="bg-[#090f16] p-3 rounded-lg border border-[#1e293b]">
                <span className="text-[10px] text-gray-500 uppercase block mb-1">Active Eras</span>
                <span className="text-sm font-bold text-sky-400">
                  {selectedNode.eraContext.map(e => `E${e}`).join(', ')}
                </span>
              </div>
              <div className="bg-[#090f16] p-3 rounded-lg border border-[#1e293b]">
                <span className="text-[10px] text-gray-500 uppercase block mb-1">Overlap Class</span>
                <span className="text-sm font-bold text-emerald-400">
                  Tier {selectedNode.kinshipScore > 80 ? 'I' : 'II'} Co-op
                </span>
              </div>
            </div>

            {/* Signature Collaborative Monument Card */}
            <div className="bg-[#0e141c] border border-[#1f2937] rounded-xl p-4 mb-6">
              <div className="flex items-center gap-2 mb-2 text-xs font-mono text-amber-400">
                <Flame className="w-3.5 h-3.5" />
                <span>Primary Collaborative Monument</span>
              </div>
              <h4 className="text-sm font-serif font-bold text-white mb-1">
                {selectedNode.keyBuildName}
              </h4>
              <p className="text-xs text-gray-400 mb-3">
                Build ID: <span className="font-mono text-gray-300">{selectedNode.keyBuildId}</span> ({selectedNode.keyBuildPieces.toLocaleString()} total pieces recorded in archive).
              </p>

              {/* Mini Attribution Progress Bar */}
              <div className="w-full bg-[#1e293b] h-2 rounded-full overflow-hidden flex mb-2">
                <div className="bg-amber-500 h-full" style={{ width: '48%' }} title="Ditseey: 48%" />
                <div className="bg-teal-400 h-full" style={{ width: '38%' }} title={`${selectedNode.name}: 38%`} />
                <div className="bg-gray-600 h-full" style={{ width: '14%' }} title="Others: 14%" />
              </div>
              <div className="flex items-center justify-between text-[10px] font-mono text-gray-400">
                <span>Ditseey (~48%)</span>
                <span>{selectedNode.name} (~38%)</span>
                <span>Allies (14%)</span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col gap-2">
              <button 
                onClick={() => alert(`Navigating to /valheim/creators/${selectedNode.id} in Next.js router`)}
                className="w-full py-2.5 px-4 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-semibold text-xs transition flex items-center justify-center gap-2 shadow-md"
              >
                <span>View {selectedNode.name}'s Full Profile</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>

              <button 
                onClick={() => alert(`Inspect Build ${selectedNode.keyBuildId} in piece viewer`)}
                className="w-full py-2 px-4 rounded-xl bg-[#161c24] hover:bg-[#1e293b] border border-[#2d3748] text-gray-300 hover:text-white font-medium text-xs transition flex items-center justify-center gap-2"
              >
                <Layers className="w-3.5 h-3.5 text-gray-400" />
                <span>Inspect Shared Build Pieces</span>
              </button>
            </div>

          </div>

          {/* Quick Kinship Rationale Box */}
          <div className="bg-[#121822] border border-[#222c3a] rounded-xl p-5 text-xs text-gray-400 space-y-3">
            <h4 className="font-serif font-bold text-white text-sm flex items-center gap-2">
              <Award className="w-4 h-4 text-amber-400" />
              How Shield-Walls Are Calculated
            </h4>
            <p className="leading-relaxed">
              In the Comfy Community, world saves are immutable. The <strong className="text-gray-200">Kinship Overlap Engine</strong> computes the intersection of blocks co-placed across multiple server wipes.
            </p>
            <p className="leading-relaxed">
              Co-architecting a 15,000-piece mountain fortress scores orders of magnitude higher than incidental block placements, highlighting genuine Viking building bonds.
            </p>
          </div>

        </div>

      </div>

    </div>
  );
}
