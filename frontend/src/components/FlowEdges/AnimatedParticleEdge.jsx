import { BaseEdge, EdgeLabelRenderer, getBezierPath } from '@xyflow/react';

export default function AnimatedParticleEdge({
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  data,
}) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const isActive = data?.active;
  const edgeColor = isActive ? '#00e6a8' : '#666';
  const strokeWidth = isActive ? 2 : 1;

  return (
    <>
      <BaseEdge
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          ...style,
          stroke: edgeColor,
          strokeWidth,
          transition: 'stroke 0.3s ease',
          strokeDasharray: isActive ? '5 5' : 'none',
          animation: isActive ? 'flowAnimation 1s linear infinite' : 'none',
          filter: isActive ? 'drop-shadow(0 0 8px rgba(0,230,168,0.8))' : 'none'
        }}
      />
      
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            pointerEvents: 'all',
            zIndex: 20,
          }}
          className="nodrag nopan"
        >
          {data?.staticLabel && !isActive && (
            <div className="bg-[#444] text-gray-200 text-[10px] px-1.5 py-0.5 rounded shadow-sm whitespace-nowrap">
              {data.staticLabel}
            </div>
          )}
          {isActive && data?.payload && (
            <div className="bg-[#111] border border-[#00e6a8] text-[#00e6a8] text-[10px] px-2 py-1 rounded shadow-[0_0_10px_rgba(0,230,168,0.3)] whitespace-nowrap flex flex-col items-center">
              <span className="font-mono">{data.payload}</span>
              {data.latency && <span className="text-yellow-500 font-bold mt-0.5">{data.latency}</span>}
            </div>
          )}
        </div>
      </EdgeLabelRenderer>
    </>
  );
}
