import { useState, useEffect, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { SkipForward, RotateCcw, Workflow, ArrowRight, Lightbulb, Box, Star, HelpCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

import CustomNode from '../components/FlowNodes/CustomNode';
import AnimatedParticleEdge from '../components/FlowEdges/AnimatedParticleEdge';
import { initialNodes, initialEdges } from './PresentationFlow/Scenarios';
import { PRESENTATION_SLIDES } from './PresentationFlow/Slides';

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

function PresentationFlowInner() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(
    initialEdges.map(e => ({ ...e, type: 'particle', data: {} }))
  );
  
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const { fitBounds, fitView } = useReactFlow();

  const activeSlide = PRESENTATION_SLIDES[currentSlideIndex];

  // Handle stepping logic
  const handleNextStep = useCallback(() => {
    if (currentSlideIndex < PRESENTATION_SLIDES.length - 1) {
      setCurrentSlideIndex(prev => prev + 1);
    }
  }, [currentSlideIndex]);

  const handlePrevStep = useCallback(() => {
    if (currentSlideIndex > 0) {
      setCurrentSlideIndex(prev => prev - 1);
    }
  }, [currentSlideIndex]);

  const handleReset = useCallback(() => {
    setCurrentSlideIndex(0);
    setTimeout(() => {
      fitView({ duration: 800, padding: 0.2 });
    }, 100);
  }, [fitView]);

  // Keyboard binding
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Enter' || e.key === 'ArrowRight' || e.key === ' ') {
        handleNextStep();
      }
      if (e.key === 'ArrowLeft') {
        handlePrevStep();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleNextStep, handlePrevStep]);

  // Update Graph based on current slide
  useEffect(() => {
    const focusNodes = new Set(activeSlide.focusNodes || []);
    const activeEdges = new Set(activeSlide.activeEdges || []);
    const animatedNodes = new Set(activeSlide.animatedNodes || []);

    // 1. Update nodes opacity & styling
    setNodes((nds) => 
      nds.map((node) => {
        const isFocused = focusNodes.size === 0 || focusNodes.has(node.id);
        const isAnimated = animatedNodes.has(node.id);
        
        return {
          ...node,
          style: {
            ...node.style,
            opacity: isFocused ? 1 : 0.2,
            filter: isFocused ? 'none' : 'grayscale(100%) blur(2px)',
            transition: 'all 0.5s ease'
          },
          data: {
            ...node.data,
            active: isAnimated || isFocused, 
            done: !isAnimated && isFocused
          }
        };
      })
    );

    // 2. Update edges
    setEdges((eds) => 
      eds.map((edge) => {
        const isActive = activeEdges.has(edge.id);
        const isFocusedNodeEdge = focusNodes.size === 0 || (focusNodes.has(edge.source) && focusNodes.has(edge.target));
        
        return {
          ...edge,
          animated: isActive,
          style: {
            opacity: isActive ? 1 : (isFocusedNodeEdge ? 0.3 : 0.05),
            stroke: isActive ? '#00e6a8' : undefined,
            transition: 'all 0.5s ease'
          },
          data: {
            ...edge.data,
            active: isActive,
            payload: isActive ? edge.data.staticLabel : null,
          }
        };
      })
    );
  }, [activeSlide, setNodes, setEdges]);

  // Use initialNodes to calculate bounding box so it doesn't retrigger on nodes state change
  useEffect(() => {
    const focusNodes = new Set(activeSlide.focusNodes || []);
    if (focusNodes.size > 0 && activeSlide.animatedNodes?.length > 0) {
      const targetNodes = initialNodes.filter(n => focusNodes.has(n.id));
      if (targetNodes.length > 0) {
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        targetNodes.forEach(n => {
          if (n.position.x < minX) minX = n.position.x;
          if (n.position.y < minY) minY = n.position.y;
          if (n.position.x + 250 > maxX) maxX = n.position.x + 250;
          if (n.position.y + 150 > maxY) maxY = n.position.y + 150;
        });
        
        fitBounds(
          { x: minX, y: minY, width: maxX - minX, height: maxY - minY },
          { padding: 0.5, duration: 1200 }
        );
      }
    } else {
      fitView({ padding: 0.1, duration: 1200 });
    }
  }, [activeSlide, fitBounds, fitView]);

  return (
    <div className="w-full h-screen bg-[#020617] text-slate-200 overflow-hidden font-sans flex relative">
      {/* Sidebar Presentation Panel */}
      <div className="w-[450px] h-full bg-[#080c14] border-r border-[#00e6a8]/20 flex flex-col z-10 shadow-[8px_0_30px_rgba(0,230,168,0.05)] relative">
        <div className="p-8 border-b border-[#00e6a8]/20 bg-[#020617]">
          <h1 className="text-2xl font-black text-[#00e6a8] mb-2 flex items-center gap-3 tracking-widest uppercase">
            <Workflow size={28} className="text-[#00e6a8]" /> RAG Masterpiece
          </h1>
          <p className="text-sm text-slate-400 font-medium ml-[40px]">Interactive Technical Architecture</p>
        </div>
        
        <div className="flex-1 overflow-y-auto p-8 relative no-scrollbar">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeSlide.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.4, ease: "easeInOut" }}
              className="space-y-8"
            >
              <div>
                <h2 className="text-3xl font-black text-white leading-tight drop-shadow-[0_0_15px_rgba(255,255,255,0.3)]">
                  {activeSlide.title}
                </h2>
                {activeSlide.subtitle && (
                  <h3 className="text-[#00e6a8] font-bold tracking-widest uppercase mt-3 text-sm flex items-center gap-2">
                    <ArrowRight size={16} /> {activeSlide.subtitle}
                  </h3>
                )}
              </div>

              <div className="space-y-8 mt-6 p-1">
                {activeSlide.strategy && (
                  <div className="space-y-3">
                    <h4 className="flex items-center gap-2 text-xs font-bold text-[#00e6a8] uppercase tracking-widest">
                      <Lightbulb size={16} /> Tư duy Chiến lược
                    </h4>
                    <p className="text-slate-300 text-sm leading-relaxed border-l-2 border-[#00e6a8]/40 pl-4 py-1">
                      {activeSlide.strategy}
                    </p>
                  </div>
                )}

                {activeSlide.tech && (
                  <div className="space-y-3">
                    <h4 className="flex items-center gap-2 text-xs font-bold text-[#00e6a8] uppercase tracking-widest">
                      <Box size={16} /> Công nghệ Áp dụng
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {activeSlide.tech.split(',').map((t, i) => (
                        <span key={i} className="px-3 py-1.5 bg-[#00e6a8]/5 text-[#00e6a8] border border-[#00e6a8]/20 rounded-lg text-xs font-medium">
                          {t.trim()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {activeSlide.benefits && (
                  <div className="space-y-3">
                    <h4 className="flex items-center gap-2 text-xs font-bold text-[#00e6a8] uppercase tracking-widest">
                      <Star size={16} /> Lợi ích
                    </h4>
                    <div className="p-4 rounded-xl bg-[#08121a] border border-[#00e6a8]/20 shadow-[inset_0_0_20px_rgba(0,230,168,0.05)]">
                      <p className="text-slate-200 text-sm leading-relaxed font-medium">
                        {activeSlide.benefits}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </AnimatePresence>
        </div>

        <div className="p-8 border-t border-[#00e6a8]/20 bg-black/40 backdrop-blur-xl">
          <div className="flex justify-between items-center mb-6">
            <span className="text-xs font-bold text-slate-500 tracking-widest uppercase">
              Slide {currentSlideIndex + 1} / {PRESENTATION_SLIDES.length}
            </span>
            <div className="flex gap-1">
              {PRESENTATION_SLIDES.map((_, i) => (
                <div 
                  key={i} 
                  className={`h-1.5 rounded-full transition-all duration-300 ${i === currentSlideIndex ? 'w-8 bg-[#00e6a8] shadow-[0_0_10px_rgba(0,230,168,0.8)]' : 'w-2 bg-slate-700'}`}
                />
              ))}
            </div>
          </div>

          <div className="flex gap-3">
            <button 
              onClick={handleReset}
              className="px-4 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl flex items-center justify-center gap-2 transition-colors text-sm font-bold"
              title="Khởi động lại"
            >
              <RotateCcw size={18} />
            </button>
            
            <button 
              onClick={handlePrevStep}
              disabled={currentSlideIndex === 0}
              className={`flex-1 py-3 rounded-xl flex items-center justify-center transition-all text-sm font-bold ${
                currentSlideIndex === 0
                  ? 'bg-slate-800/50 text-slate-600 cursor-not-allowed border border-slate-800'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
              }`}
            >
              Back
            </button>

            <button 
              onClick={handleNextStep}
              disabled={currentSlideIndex === PRESENTATION_SLIDES.length - 1}
              className={`flex-[2] py-3 rounded-xl flex items-center justify-center gap-2 transition-all text-sm font-bold ${
                currentSlideIndex === PRESENTATION_SLIDES.length - 1
                  ? 'bg-slate-800/50 text-slate-600 cursor-not-allowed border border-slate-800'
                  : 'bg-[#00e6a8] text-black hover:bg-[#00e6a8]/90 shadow-[0_0_20px_rgba(0,230,168,0.3)] hover:shadow-[0_0_30px_rgba(0,230,168,0.5)]'
              }`}
            >
              Next <SkipForward size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* React Flow Canvas */}
      <div className="flex-1 h-full relative bg-transparent">
        {/* Leading Question Floating Box */}
        <div className="absolute top-8 right-8 z-50 max-w-sm pointer-events-none">
          <AnimatePresence mode="wait">
             {activeSlide.leadingQuestion && (
                <motion.div
                  key={activeSlide.id}
                  initial={{ opacity: 0, y: -20, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -10, scale: 0.95 }}
                  transition={{ duration: 0.5, delay: 0.8, ease: "easeOut" }}
                >
                  <div className="bg-slate-900/90 border border-[#00e6a8]/30 backdrop-blur-xl p-5 rounded-2xl shadow-[0_10px_40px_rgba(0,230,168,0.15)] text-slate-200">
                     <div className="flex items-center gap-2 text-[#00e6a8] font-bold text-[10px] mb-3 uppercase tracking-[0.2em]">
                       <HelpCircle size={14} /> Gợi mở vấn đề
                     </div>
                     <p className="text-sm font-medium leading-relaxed italic text-slate-300">
                       "{activeSlide.leadingQuestion}"
                     </p>
                  </div>
                </motion.div>
             )}
          </AnimatePresence>
        </div>

        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          minZoom={0.1}
          maxZoom={1.5}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#1e293b" gap={32} size={2} />
          
          {/* Keyframe animation injected for edges */}
          <svg style={{ width: 0, height: 0, position: 'absolute' }}>
            <defs>
              <style>
                {`
                  @keyframes flowAnimation {
                    from { stroke-dashoffset: 24; }
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

export default function PresentationFlow() {
  return (
    <ReactFlowProvider>
      <PresentationFlowInner />
    </ReactFlowProvider>
  );
}
