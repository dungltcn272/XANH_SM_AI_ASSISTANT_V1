import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  useNodesState,
  useEdgesState,
  Panel
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { SkipForward, RotateCcw, Workflow } from 'lucide-react';

import CustomNode from '../components/FlowNodes/CustomNode';
import AnimatedParticleEdge from '../components/FlowEdges/AnimatedParticleEdge';
import { SCENARIOS, initialNodes, initialEdges } from './PresentationFlow/Scenarios';

const nodeTypes = {
  user: CustomNode,
  gateway: CustomNode,
  cache: CustomNode,
  ai: CustomNode,
  process: CustomNode,
  decision: CustomNode,
  database: CustomNode,
  block: CustomNode,
  input: CustomNode,
  output: CustomNode,
  persona: CustomNode,
  out: CustomNode,
};

const edgeTypes = {
  particle: AnimatedParticleEdge,
};

export default function PresentationFlow() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(
    initialEdges.map(e => ({ ...e, type: 'particle', data: {} }))
  );
  
  const [activeScenarioId, setActiveScenarioId] = useState(SCENARIOS[0].id);
  const [currentStepIndex, setCurrentStepIndex] = useState(-1);

  const activeScenario = useMemo(() => 
    SCENARIOS.find(s => s.id === activeScenarioId) || SCENARIOS[0]
  , [activeScenarioId]);

  // Handle stepping logic
  const handleNextStep = useCallback(() => {
    if (currentStepIndex < activeScenario.steps.length - 1) {
      setCurrentStepIndex(prev => prev + 1);
    } else {
      // Done
    }
  }, [currentStepIndex, activeScenario]);

  const handleReset = useCallback(() => {
    setCurrentStepIndex(-1);
  }, []);

  const handleSelectScenario = useCallback((id) => {
    setActiveScenarioId(id);
    setCurrentStepIndex(-1);
  }, []);

  // Keyboard binding
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Enter' || e.key === 'ArrowRight' || e.key === ' ') {
        handleNextStep();
      }
      if (e.key === 'ArrowLeft') {
        setCurrentStepIndex(prev => Math.max(-1, prev - 1));
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleNextStep]);

  // Update Graph based on current step
  useEffect(() => {
    // Determine active nodes up to this step
    const pastNodes = new Set();
    let currentEdgeId = null;
    let currentPayload = null;
    let currentLatency = null;
    let activeNodeId = null;

    if (currentStepIndex >= 0) {
      for (let i = 0; i <= currentStepIndex; i++) {
        const step = activeScenario.steps[i];
        pastNodes.add(step.source);
        pastNodes.add(step.target);
        
        if (i === currentStepIndex) {
          currentEdgeId = step.edge;
          currentPayload = step.payload;
          currentLatency = step.latency;
          activeNodeId = step.target; // The node receiving data is active
        }
      }
    }

    setNodes((nds) => 
      nds.map((node) => {
        const isPast = pastNodes.has(node.id);
        const isActive = node.id === activeNodeId || (currentStepIndex === -1 && node.id === 'user');
        
        return {
          ...node,
          data: {
            ...node.data,
            active: isActive,
            done: isPast && !isActive,
          }
        };
      })
    );

    setEdges((eds) => 
      eds.map((edge) => {
        const isActiveEdge = edge.id === currentEdgeId;
        return {
          ...edge,
          animated: isActiveEdge,
          data: {
            active: isActiveEdge,
            payload: isActiveEdge ? currentPayload : null,
            latency: isActiveEdge ? currentLatency : null,
          },
          style: {
            opacity: currentStepIndex === -1 ? 0.3 : (isActiveEdge ? 1 : 0.1),
          }
        };
      })
    );
  }, [currentStepIndex, activeScenario, setNodes, setEdges]);

  return (
    <div className="w-full h-screen bg-[#050505] text-slate-200 overflow-hidden font-sans flex relative">
      {/* Sidebar Controls */}
      <div className="w-[350px] h-full bg-[#0a0a0a] border-r border-[#00e6a8]/20 flex flex-col z-10 shadow-[4px_0_24px_rgba(0,230,168,0.05)]">
        <div className="p-6 border-b border-[#00e6a8]/20">
          <h1 className="text-xl font-bold text-[#00e6a8] mb-2 flex items-center gap-2 tracking-widest uppercase">
            <Workflow size={20} /> Data Flow
          </h1>
          <p className="text-xs text-slate-400">Interactive Architecture Presentation</p>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 px-2">Scenarios</h2>
          {SCENARIOS.map((scenario) => (
            <button
              key={scenario.id}
              onClick={() => handleSelectScenario(scenario.id)}
              className={`w-full text-left px-4 py-3 rounded-xl border transition-all ${
                activeScenarioId === scenario.id 
                  ? 'bg-[#00e6a8]/10 border-[#00e6a8]/50 text-[#00e6a8]' 
                  : 'bg-transparent border-transparent text-slate-400 hover:bg-white/5 hover:text-slate-300'
              }`}
            >
              <div className="font-bold text-sm mb-1">{scenario.name}</div>
              <div className="text-[10px] opacity-80 leading-relaxed">{scenario.description}</div>
            </button>
          ))}
        </div>

        <div className="p-6 border-t border-[#00e6a8]/20 bg-black/20">
          <div className="flex gap-3">
            <button 
              onClick={handleReset}
              className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl flex items-center justify-center gap-2 transition-colors text-sm font-bold"
            >
              <RotateCcw size={16} /> Reset
            </button>
            <button 
              onClick={handleNextStep}
              disabled={currentStepIndex >= activeScenario.steps.length - 1}
              className={`flex-1 py-3 rounded-xl flex items-center justify-center gap-2 transition-all text-sm font-bold ${
                currentStepIndex >= activeScenario.steps.length - 1
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-[#00e6a8] text-black hover:bg-[#00e6a8]/90 shadow-[0_0_15px_rgba(0,230,168,0.4)]'
              }`}
            >
              Step <SkipForward size={16} />
            </button>
          </div>
          <div className="text-center text-[10px] text-slate-500 mt-3">
            Press <kbd className="px-1 py-0.5 bg-slate-800 rounded mx-1 font-mono">Enter</kbd> or <kbd className="px-1 py-0.5 bg-slate-800 rounded mx-1 font-mono">Space</kbd> to step
          </div>
        </div>
      </div>

      {/* React Flow Canvas */}
      <div className="flex-1 h-full relative bg-[#020617]">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          attributionPosition="bottom-right"
          minZoom={0.2}
        >
          <Background color="#1e293b" gap={24} size={2} />
          
          <Panel position="top-center" className="bg-black/60 backdrop-blur-md px-6 py-3 rounded-full border border-[#00e6a8]/30 shadow-[0_4px_20px_rgba(0,0,0,0.5)]">
            <div className="flex items-center gap-3">
              <span className="w-3 h-3 rounded-full bg-[#00e6a8] animate-pulse"></span>
              <span className="font-mono text-sm text-[#00e6a8] font-bold tracking-wider">
                {activeScenario.name}
              </span>
              <span className="text-slate-400 text-sm ml-2">
                Step {currentStepIndex + 1} / {activeScenario.steps.length}
              </span>
            </div>
          </Panel>

          {/* Keyframe animation injected for edges */}
          <svg style={{ width: 0, height: 0, position: 'absolute' }}>
            <defs>
              <style>
                {`
                  @keyframes flowAnimation {
                    from { stroke-dashoffset: 15; }
                    to { stroke-dashoffset: 0; }
                  }
                `}
              </style>
            </defs>
          </svg>
        </ReactFlow>
      </div>
    </div>
  );
}
