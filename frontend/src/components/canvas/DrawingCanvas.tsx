import React, { useRef, useState, useEffect } from 'react';
import { Paintbrush, Eraser, RotateCcw, Palette } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

const PRESET_COLORS = [
  { name: 'Black', hex: '#000000' },
  { name: 'Red', hex: '#DC2626' },
  { name: 'Blue', hex: '#2563EB' },
  { name: 'Green', hex: '#059669' },
  { name: 'Yellow', hex: '#EAB308' },
  { name: 'Purple', hex: '#7C3AED' },
  { name: 'Orange', hex: '#EA580C' },
  { name: 'Pink', hex: '#EC4899' },
];

export const DrawingCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { setCurrentImage } = useAppStore();

  const [tool, setTool] = useState<'brush' | 'eraser'>('brush');
  const [brushSize, setBrushSize] = useState<number>(4);
  const [strokeColor, setStrokeColor] = useState<string>('#000000');
  const [isDrawing, setIsDrawing] = useState(false);

  // Initialize canvas with clean white background
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
  }, []);

  const syncImageToStore = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dataUrl = canvas.toDataURL('image/png');
    setCurrentImage(dataUrl, 'sketch_drawing.png');
  };

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    setIsDrawing(true);
    const rect = canvas.getBoundingClientRect();
    const x = 'touches' in e ? e.touches[0].clientX - rect.left : e.clientX - rect.left;
    const y = 'touches' in e ? e.touches[0].clientY - rect.top : e.clientY - rect.top;

    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    const x = 'touches' in e ? e.touches[0].clientX - rect.left : e.clientX - rect.left;
    const y = 'touches' in e ? e.touches[0].clientY - rect.top : e.clientY - rect.top;

    ctx.lineWidth = tool === 'eraser' ? brushSize * 3 : brushSize;
    ctx.strokeStyle = tool === 'eraser' ? '#ffffff' : strokeColor;
    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const stopDrawing = () => {
    if (isDrawing) {
      setIsDrawing(false);
      syncImageToStore();
    }
  };

  const handleReset = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    setCurrentImage(null, null);
  };

  return (
    <div className="space-y-3">
      {/* Basic Drawing Tools: Brush, Eraser, Canvas Reset */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-2 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
        {/* Brush & Eraser */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => setTool('brush')}
            className={`px-2.5 py-1 rounded-lg font-medium flex items-center gap-1.5 transition-all ${
              tool === 'brush'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <Paintbrush className="w-3.5 h-3.5" />
            <span>Brush</span>
          </button>
          <button
            onClick={() => setTool('eraser')}
            className={`px-2.5 py-1 rounded-lg font-medium flex items-center gap-1.5 transition-all ${
              tool === 'eraser'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <Eraser className="w-3.5 h-3.5" />
            <span>Eraser</span>
          </button>
        </div>

        {/* Brush Size */}
        <div className="flex items-center gap-1 px-2 border-l border-slate-800">
          <span className="text-[11px] text-slate-500 mr-1">Size:</span>
          {[2, 4, 8].map((s) => (
            <button
              key={s}
              onClick={() => setBrushSize(s)}
              className={`w-5 h-5 rounded flex items-center justify-center font-mono text-[10px] ${
                brushSize === s
                  ? 'bg-blue-600 text-white font-bold'
                  : 'text-slate-400 hover:text-slate-200 bg-slate-800/80'
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Canvas Reset */}
        <button
          onClick={handleReset}
          className="px-2.5 py-1 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 flex items-center gap-1.5 transition-colors border-l border-slate-800 pl-2"
          title="Reset Canvas"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset</span>
        </button>
      </div>

      {/* Color Palette */}
      {tool === 'brush' && (
        <div className="flex items-center justify-between px-2 py-1.5 rounded-lg bg-slate-900/60 border border-slate-800">
          <div className="flex items-center gap-1.5 flex-wrap">
            {PRESET_COLORS.map((c) => (
              <button
                key={c.hex}
                title={c.name}
                onClick={() => setStrokeColor(c.hex)}
                className={`w-5 h-5 rounded-full transition-transform border ${
                  strokeColor.toLowerCase() === c.hex.toLowerCase()
                    ? 'ring-2 ring-blue-500 scale-110 border-white'
                    : 'border-slate-700/60 hover:scale-105'
                }`}
                style={{ backgroundColor: c.hex }}
              />
            ))}
          </div>

          <label className="flex items-center gap-1 text-[11px] text-slate-400 cursor-pointer hover:text-slate-200" title="Custom Color">
            <Palette className="w-3.5 h-3.5" />
            <input
              type="color"
              value={strokeColor}
              onChange={(e) => setStrokeColor(e.target.value)}
              className="w-0 h-0 opacity-0 absolute pointer-events-none"
            />
          </label>
        </div>
      )}

      {/* Canvas Drawing Surface */}
      <div className="flex justify-center bg-white rounded-xl overflow-hidden border border-slate-800 shadow-inner">
        <canvas
          ref={canvasRef}
          width={360}
          height={300}
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          onTouchStart={startDrawing}
          onTouchMove={draw}
          onTouchEnd={stopDrawing}
          className="cursor-crosshair touch-none w-full max-w-[360px] h-[300px]"
        />
      </div>
    </div>
  );
};
