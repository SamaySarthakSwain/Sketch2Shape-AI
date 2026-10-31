import React, { useRef, useState, useEffect } from 'react';
import { RotateCcw, Trash2, Palette } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

const PRESET_COLORS = [
  { name: 'Black', hex: '#000000' },
  { name: 'Red', hex: '#DC2626' },
  { name: 'Blue', hex: '#2563EB' },
  { name: 'Green', hex: '#059669' },
  { name: 'Gold', hex: '#D97706' },
  { name: 'Purple', hex: '#7C3AED' },
  { name: 'Orange', hex: '#EA580C' },
  { name: 'Pink', hex: '#EC4899' },
];

export const DrawingCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { setCurrentImage } = useAppStore();

  const [isDrawing, setIsDrawing] = useState(false);
  const [strokeColor, setStrokeColor] = useState<string>('#000000');
  const [history, setHistory] = useState<ImageData[]>([]);
  const [historyIndex, setHistoryIndex] = useState<number>(-1);

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

    const initial = ctx.getImageData(0, 0, canvas.width, canvas.height);
    setHistory([initial]);
    setHistoryIndex(0);
  }, []);

  const syncImageToStore = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dataUrl = canvas.toDataURL('image/png');
    setCurrentImage(dataUrl, 'sketch_drawing.png');
  };

  const saveHistory = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const currentData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(currentData);
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
    syncImageToStore();
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

    ctx.lineWidth = 4;
    ctx.strokeStyle = strokeColor;
    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const stopDrawing = () => {
    if (isDrawing) {
      setIsDrawing(false);
      saveHistory();
    }
  };

  const handleUndo = () => {
    if (historyIndex > 0) {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      const prev = history[historyIndex - 1];
      ctx.putImageData(prev, 0, 0);
      setHistoryIndex(historyIndex - 1);
      syncImageToStore();
    }
  };

  const handleClear = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    const initial = ctx.getImageData(0, 0, canvas.width, canvas.height);
    setHistory([initial]);
    setHistoryIndex(0);
    setCurrentImage(null, null);
  };

  return (
    <div className="space-y-3">
      {/* Sleek Tool & Color Bar */}
      <div className="flex items-center justify-between gap-2 p-2 rounded-xl bg-slate-900/80 border border-slate-800">
        {/* Colors */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {PRESET_COLORS.map((c) => (
            <button
              key={c.hex}
              title={c.name}
              onClick={() => setStrokeColor(c.hex)}
              className={`w-6 h-6 rounded-full transition-all border ${
                strokeColor.toLowerCase() === c.hex.toLowerCase()
                  ? 'ring-2 ring-blue-500 scale-110 border-white'
                  : 'border-slate-700/60 hover:scale-105'
              }`}
              style={{ backgroundColor: c.hex }}
            />
          ))}

          {/* Color Picker */}
          <label className="flex items-center cursor-pointer p-0.5 rounded-full hover:bg-slate-800 transition-colors" title="Custom Color">
            <Palette className="w-4 h-4 text-slate-400 hover:text-slate-200" />
            <input
              type="color"
              value={strokeColor}
              onChange={(e) => setStrokeColor(e.target.value)}
              className="w-0 h-0 opacity-0 absolute pointer-events-none"
            />
          </label>
        </div>

        {/* Undo & Clear */}
        <div className="flex items-center gap-1 border-l border-slate-800 pl-2">
          <button
            onClick={handleUndo}
            disabled={historyIndex <= 0}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 disabled:opacity-30 disabled:hover:bg-transparent transition-colors"
            title="Undo"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleClear}
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
            title="Clear Canvas"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex justify-center bg-white rounded-xl overflow-hidden border border-slate-800 shadow-md">
        <canvas
          ref={canvasRef}
          width={360}
          height={320}
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          onTouchStart={startDrawing}
          onTouchMove={draw}
          onTouchEnd={stopDrawing}
          className="cursor-crosshair touch-none w-full max-w-[360px] h-[320px]"
        />
      </div>
    </div>
  );
};
