import React, { useRef, useState, useEffect } from 'react';
import { PenTool, Eraser, RotateCcw, RotateCw, Trash2, ArrowRight } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { Button } from '../common/Button';

export const DrawingCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { setCurrentImage } = useAppStore();

  const [isDrawing, setIsDrawing] = useState(false);
  const [brushSize, setBrushSize] = useState<number>(4);
  const [tool, setTool] = useState<'pen' | 'eraser'>('pen');
  const [history, setHistory] = useState<ImageData[]>([]);
  const [historyIndex, setHistoryIndex] = useState<number>(-1);

  // Initialize canvas with pure white background
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

    ctx.lineWidth = brushSize;
    ctx.strokeStyle = tool === 'pen' ? '#000000' : '#ffffff';
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
    }
  };

  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      const next = history[historyIndex + 1];
      ctx.putImageData(next, 0, 0);
      setHistoryIndex(historyIndex + 1);
    }
  };

  const handleClear = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    saveHistory();
  };

  const handleUseDrawing = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dataUrl = canvas.toDataURL('image/png');
    setCurrentImage(dataUrl, 'interactive_drawing.png');
  };

  return (
    <div className="space-y-3">
      {/* Canvas Toolset */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-2 rounded-lg bg-slate-900 border border-slate-800 text-xs">
        <div className="flex items-center gap-1">
          <Button
            variant={tool === 'pen' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setTool('pen')}
            icon={<PenTool className="w-3.5 h-3.5" />}
          >
            Pen
          </Button>
          <Button
            variant={tool === 'eraser' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setTool('eraser')}
            icon={<Eraser className="w-3.5 h-3.5" />}
          >
            Eraser
          </Button>
        </div>

        {/* Brush Size */}
        <div className="flex items-center gap-2 px-2 border-l border-slate-800">
          <span className="text-slate-400">Size:</span>
          {[2, 4, 8, 14].map((size) => (
            <button
              key={size}
              onClick={() => setBrushSize(size)}
              className={`w-6 h-6 rounded flex items-center justify-center font-mono ${
                brushSize === size
                  ? 'bg-blue-600 text-white font-bold'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {size}
            </button>
          ))}
        </div>

        {/* Undo / Redo / Clear */}
        <div className="flex items-center gap-1 border-l border-slate-800 pl-2">
          <Button
            variant="ghost"
            size="sm"
            disabled={historyIndex <= 0}
            onClick={handleUndo}
            icon={<RotateCcw className="w-3.5 h-3.5" />}
            title="Undo"
          />
          <Button
            variant="ghost"
            size="sm"
            disabled={historyIndex >= history.length - 1}
            onClick={handleRedo}
            icon={<RotateCw className="w-3.5 h-3.5" />}
            title="Redo"
          />
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClear}
            className="text-rose-400 hover:text-rose-300"
            icon={<Trash2 className="w-3.5 h-3.5" />}
            title="Clear Canvas"
          />
        </div>
      </div>

      {/* Drawing Surface */}
      <div className="flex justify-center bg-slate-950 p-2 rounded-xl border border-slate-800 shadow-inner">
        <canvas
          ref={canvasRef}
          width={400}
          height={400}
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          onTouchStart={startDrawing}
          onTouchMove={draw}
          onTouchEnd={stopDrawing}
          className="bg-white rounded-lg cursor-crosshair shadow-sm touch-none max-w-full h-auto"
        />
      </div>

      <div className="flex justify-end">
        <Button
          variant="primary"
          onClick={handleUseDrawing}
          icon={<ArrowRight className="w-4 h-4" />}
        >
          Use Drawing in Studio
        </Button>
      </div>
    </div>
  );
};
