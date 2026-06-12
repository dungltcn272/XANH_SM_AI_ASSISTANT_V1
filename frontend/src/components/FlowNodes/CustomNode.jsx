import { Handle, Position } from '@xyflow/react';

export default function CustomNode({ data }) {
  const isActive = data.active;
  const isDone = data.done;

  // Defaults - Vibrant neon hacker theme
  let color = '#475569'; // default slate for done/inactive
  let textColor = '#cbd5e1';
  let filter = 'none';

  if (isActive) {
    if (data.type === 'input' || data.type === 'output') { color = '#0ea5e9'; filter = 'drop-shadow(0 0 12px rgba(14,165,233,0.8))'; textColor = '#fff'; }
    else if (data.type === 'gateway') { color = '#f43f5e'; filter = 'drop-shadow(0 0 12px rgba(244,63,94,0.8))'; textColor = '#fff'; }
    else if (data.type === 'block') { color = '#e11d48'; filter = 'drop-shadow(0 0 12px rgba(225,29,72,0.8))'; textColor = '#fff'; }
    else if (data.type === 'decision') { color = '#a855f7'; filter = 'drop-shadow(0 0 12px rgba(168,85,247,0.8))'; textColor = '#fff'; }
    else if (data.type === 'persona') { color = '#f59e0b'; filter = 'drop-shadow(0 0 12px rgba(245,158,11,0.8))'; textColor = '#fff'; }
    else { color = '#10b981'; filter = 'drop-shadow(0 0 12px rgba(16,185,129,0.8))'; textColor = '#fff'; }
  } else if (!isDone) {
    // Upcoming nodes
    color = '#1e293b'; textColor = '#64748b';
  }

  // Dimensions based on type
  let w = 220;
  let h = 60;
  let isDiamond = false;
  let borderRadius = '8px';

  if (data.type === 'gateway' || data.type === 'decision') { 
    w = 150; 
    h = 150; 
    isDiamond = true;
  } else if (data.type === 'input' || data.type === 'output') { 
    w = 160; 
    h = 40; 
    borderRadius = '9999px'; // Pill
  }

  // Background Shape using pure CSS
  // For diamond, the actual div needs to be smaller so its rotated bounding box fits in WxH
  const rectW = isDiamond ? w * 0.707 : w - 4;
  const rectH = isDiamond ? h * 0.707 : h - 4;

  const bgStyle = {
    position: 'absolute',
    width: rectW,
    height: rectH,
    backgroundColor: '#020617',
    border: `3px solid ${color}`,
    borderRadius: isDiamond ? '4px' : borderRadius,
    transform: isDiamond ? 'rotate(45deg)' : 'none',
    filter: isActive ? filter : 'none',
    boxShadow: isActive ? `0 0 20px ${color}40, inset 0 0 10px ${color}20` : 'none',
    transition: 'all 0.5s ease',
    zIndex: 0,
  };

  return (
    <div className={`relative flex items-center justify-center pointer-events-auto transition-transform duration-500 ${isActive ? 'scale-105' : 'scale-100'}`} style={{ width: w, height: h }}>
      {/* Top Handle */}
      <Handle type="target" position={Position.Top} className="w-1.5 h-1.5 rounded-full bg-gray-400 border-none z-20 opacity-0" />
      
      {/* CSS Background Shape */}
      <div style={bgStyle}></div>
      
      {/* Text Content */}
      <div 
        className="relative z-10 flex flex-col items-center justify-center pointer-events-none p-4 text-center w-full h-full"
        style={{ color: textColor }}
      >
        <div className="text-[12px] font-bold tracking-wide leading-snug break-words max-w-[90%] drop-shadow-md">
          {data.label.split('\n').map((line, i) => (
            <div key={i}>{line}</div>
          ))}
        </div>
      </div>

      {/* Bottom Handle */}
      <Handle type="source" position={Position.Bottom} className="w-1.5 h-1.5 rounded-full bg-gray-400 border-none z-20" />
    </div>
  );
}
