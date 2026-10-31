import React, { useRef, useState, useEffect } from 'react';
import {
  PenTool,
  Eraser,
  RotateCcw,
  Upload,
  Sparkles,
  Sliders,
  Eye,
  Crosshair
} from 'lucide-react';

export default function Canvas({ onSketchChange, onReconstruct, isGenerating }) {
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [tool, setTool] = useState('pen'); // 'pen' | 'eraser'
  const [brushSize, setBrushSize] = useState(6);
  const [showSymmetryGuide, setShowSymmetryGuide] = useState(true);
  const [hasStrokes, setHasStrokes] = useState(false);
  const fileInputRef = useRef(null);

  // Initialize Canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    // Draw initial sample vase
    loadPreset('vase');
  }, []);

  const getCanvasCoords = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;

    return {
      x: (clientX - rect.left) * scaleX,
      y: (clientY - rect.top) * scaleY
    };
  };

  const startDrawing = (e) => {
    e.preventDefault();
    const { x, y } = getCanvasCoords(e);
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.lineWidth = brushSize;
    ctx.strokeStyle = tool === 'eraser' ? '#FFFFFF' : '#111827';

    setIsDrawing(true);
    setHasStrokes(true);
  };

  const draw = (e) => {
    if (!isDrawing) return;
    e.preventDefault();
    const { x, y } = getCanvasCoords(e);
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const stopDrawing = () => {
    if (!isDrawing) return;
    setIsDrawing(false);
    notifyChange();
  };

  const notifyChange = () => {
    if (!canvasRef.current) return;
    const dataUrl = canvasRef.current.toDataURL('image/png');
    onSketchChange(dataUrl);
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    setHasStrokes(false);
    notifyChange();
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Aspect fit image
        const scale = Math.min((canvas.width * 0.85) / img.width, (canvas.height * 0.85) / img.height);
        const w = img.width * scale;
        const h = img.height * scale;
        const x = (canvas.width - w) / 2;
        const y = (canvas.height - h) / 2;

        ctx.drawImage(img, x, y, w, h);
        setHasStrokes(true);
        notifyChange();
      };
      img.src = event.target.result;
    };
    reader.readAsDataURL(file);
  };

  const loadPreset = (preset) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = '#111827';
    ctx.lineWidth = 5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    const cx = canvas.width / 2;
    const cy = canvas.height / 2;

    if (preset === 'vase') {
      ctx.beginPath();
      // Left contour of vase
      ctx.moveTo(cx - 30, cy - 140);
      ctx.bezierCurveTo(cx - 20, cy - 80, cx - 85, cy - 20, cx - 80, cy + 60);
      ctx.bezierCurveTo(cx - 75, cy + 120, cx - 45, cy + 140, cx - 40, cy + 150);
      // Base
      ctx.lineTo(cx + 40, cy + 150);
      // Right contour of vase (symmetric)
      ctx.bezierCurveTo(cx + 45, cy + 140, cx + 75, cy + 120, cx + 80, cy + 60);
      ctx.bezierCurveTo(cx + 85, cy - 20, cx + 20, cy - 80, cx + 30, cy - 140);
      // Lip
      ctx.lineTo(cx - 30, cy - 140);
      ctx.stroke();
    } else if (preset === 'mug') {
      ctx.beginPath();
      // Cup body
      ctx.roundRect ? ctx.roundRect(cx - 60, cy - 70, 110, 140, 12) : ctx.rect(cx - 60, cy - 70, 110, 140);
      ctx.stroke();
      // Handle
      ctx.beginPath();
      ctx.arc(cx + 60, cy, 35, -Math.PI / 2.2, Math.PI / 2.2);
      ctx.stroke();
    } else if (preset === 'chair') {
      ctx.beginPath();
      // Backrest
      ctx.moveTo(cx - 40, cy - 120);
      ctx.lineTo(cx - 40, cy + 20);
      // Seat
      ctx.lineTo(cx + 50, cy + 20);
      // Front Leg
      ctx.moveTo(cx + 45, cy + 20);
      ctx.lineTo(cx + 45, cy + 140);
      // Back Leg
      ctx.moveTo(cx - 35, cy + 20);
      ctx.lineTo(cx - 35, cy + 140);
      ctx.stroke();
    } else if (preset === 'airplane') {
      ctx.beginPath();
      // Fuselage
      ctx.ellipse(cx, cy, 18, 140, 0, 0, Math.PI * 2);
      // Wings
      ctx.moveTo(cx - 130, cy - 10);
      ctx.lineTo(cx + 130, cy - 10);
      ctx.lineTo(cx + 30, cy + 30);
      ctx.lineTo(cx - 30, cy + 30);
      ctx.closePath();
      // Tail
      ctx.moveTo(cx - 50, cy + 120);
      ctx.lineTo(cx + 50, cy + 120);
      ctx.stroke();
    } else if (preset === 'car') {
      ctx.beginPath();
      ctx.moveTo(cx - 130, cy + 30);
      ctx.quadraticCurveTo(cx - 110, cy - 10, cx - 60, cy - 15);
      ctx.quadraticCurveTo(cx - 20, cy - 60, cx + 50, cy - 50);
      ctx.quadraticCurveTo(cx + 100, cy - 30, cx + 130, cy + 10);
      ctx.lineTo(cx + 135, cy + 40);
      ctx.lineTo(cx - 130, cy + 40);
      ctx.stroke();
      // Wheels
      ctx.beginPath();
      ctx.arc(cx - 70, cy + 40, 20, 0, Math.PI * 2);
      ctx.arc(cx + 70, cy + 40, 20, 0, Math.PI * 2);
      ctx.stroke();
    }

    setHasStrokes(true);
    notifyChange();
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col gap-3 shadow-xl">
      {/* Top Toolbar */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-1.5 bg-slate-950/80 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setTool('pen')}
            className={`p-2 rounded-lg transition-colors ${
              tool === 'pen'
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
            title="Pencil Tool"
          >
            <PenTool className="w-4 h-4" />
          </button>
          <button
            onClick={() => setTool('eraser')}
            className={`p-2 rounded-lg transition-colors ${
              tool === 'eraser'
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                : 'text-slate-400 hover:text-slate-200'
            }`}
            title="Eraser Tool"
          >
            <Eraser className="w-4 h-4" />
          </button>
          <div className="h-4 w-px bg-slate-800 mx-1" />
          <button
            onClick={clearCanvas}
            className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
            title="Clear Canvas"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setShowSymmetryGuide(!showSymmetryGuide)}
            className={`p-2 rounded-lg transition-colors ${
              showSymmetryGuide ? 'text-indigo-400 bg-indigo-500/20' : 'text-slate-500'
            }`}
            title="Toggle Symmetry Guide"
          >
            <Crosshair className="w-4 h-4" />
          </button>
        </div>

        {/* Brush Size Slider */}
        <div className="flex items-center gap-2 bg-slate-950/80 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
          <span className="text-slate-400">Brush:</span>
          <input
            type="range"
            min="2"
            max="28"
            value={brushSize}
            onChange={(e) => setBrushSize(parseInt(e.target.value))}
            className="w-16 accent-cyan-500 cursor-pointer"
          />
          <span className="text-slate-300 font-mono w-4">{brushSize}</span>
        </div>

        {/* Preset Selector */}
        <div className="flex items-center gap-1.5">
          <select
            onChange={(e) => loadPreset(e.target.value)}
            defaultValue="vase"
            className="bg-slate-950/80 text-xs text-slate-300 border border-slate-800 rounded-xl px-2.5 py-2 outline-none focus:border-cyan-500"
          >
            <option value="vase">🏺 Vase Preset</option>
            <option value="mug">☕ Coffee Mug</option>
            <option value="chair">🪑 Modern Chair</option>
            <option value="car">🚗 Sports Car</option>
            <option value="airplane">✈️ Airplane</option>
          </select>

          {/* Upload Button */}
          <button
            onClick={() => fileInputRef.current?.click()}
            className="p-2 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700 transition-colors"
            title="Upload Sketch"
          >
            <Upload className="w-4 h-4" />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFileUpload}
          />
        </div>
      </div>

      {/* Canvas Viewport */}
      <div className="relative aspect-square w-full max-w-[480px] mx-auto rounded-2xl overflow-hidden border-2 border-slate-800 shadow-inner bg-white">
        <canvas
          ref={canvasRef}
          width={512}
          height={512}
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          onTouchStart={startDrawing}
          onTouchMove={draw}
          onTouchEnd={stopDrawing}
          className="w-full h-full cursor-crosshair touch-none"
        />

        {/* Symmetry Guide Overlay */}
        {showSymmetryGuide && (
          <div className="pointer-events-none absolute inset-0 flex justify-center">
            <div className="w-0.5 h-full border-r border-dashed border-cyan-500/50" />
            <div className="absolute top-2 left-2 text-[10px] text-slate-400/80 bg-slate-100/90 px-1.5 py-0.5 rounded shadow-sm">
              Symmetry Axis
            </div>
          </div>
        )}
      </div>

      {/* Action Button */}
      <button
        onClick={onReconstruct}
        disabled={isGenerating}
        className="w-full py-3.5 px-4 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-500 via-indigo-600 to-purple-600 hover:from-cyan-400 hover:via-indigo-500 hover:to-purple-500 text-white shadow-lg shadow-cyan-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform active:scale-[0.99]"
      >
        <Sparkles className={`w-4 h-4 ${isGenerating ? 'animate-spin' : ''}`} />
        <span>{isGenerating ? 'Reconstructing 3D Mesh...' : 'Reconstruct 3D Model'}</span>
      </button>
    </div>
  );
}
