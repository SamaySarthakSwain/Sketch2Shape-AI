import React, { useRef, useState } from 'react';
import { Upload, X, RefreshCw, Image as ImageIcon, Sparkles } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';
import { Button } from '../common/Button';

const SAMPLE_SKETCHES = [
  { name: 'Chair', file: '/examples/quickdraw_chair_normalized.png', category: 'chair' },
  { name: 'Car', file: '/examples/quickdraw_car_normalized.png', category: 'car' },
  { name: 'Airplane', file: '/examples/quickdraw_airplane_normalized.png', category: 'airplane' },
  { name: 'Cup', file: '/examples/quickdraw_cup_normalized.png', category: 'cup' },
  { name: 'Bicycle', file: '/examples/quickdraw_bicycle_normalized.png', category: 'bicycle' },
  { name: 'Apple', file: '/examples/quickdraw_apple_normalized.png', category: 'apple' },
];

export const UploadPanel: React.FC = () => {
  const { currentImageBase64, currentImageName, setCurrentImage } = useAppStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const processFile = (file: File) => {
    setErrorMsg(null);
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      setErrorMsg('Unsupported format. Please upload PNG, JPG, or WebP.');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg('Image size exceeds 10MB limit.');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const b64 = e.target?.result as string;
      setCurrentImage(b64, file.name);
    };
    reader.onerror = () => {
      setErrorMsg('Failed to read image file.');
    };
    reader.readAsDataURL(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const loadSample = async (sample: typeof SAMPLE_SKETCHES[0]) => {
    try {
      const res = await fetch(sample.file);
      const blob = await res.blob();
      const reader = new FileReader();
      reader.onload = () => {
        setCurrentImage(reader.result as string, `${sample.name}_sample.png`);
      };
      reader.readAsDataURL(blob);
    } catch (e) {
      setErrorMsg(`Failed to load ${sample.name} sample.`);
    }
  };

  return (
    <div className="space-y-4">
      {/* Upload Zone / Active Preview */}
      {!currentImageBase64 ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer transition-all ${
            isDragging
              ? 'border-blue-500 bg-blue-950/20 text-blue-200 scale-[0.99]'
              : 'border-slate-800 hover:border-slate-700 bg-slate-900/40 text-slate-400 hover:text-slate-200'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                processFile(e.target.files[0]);
              }
            }}
          />
          <div className="w-12 h-12 rounded-xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-slate-300 mb-3 shadow-inner">
            <Upload className="w-5 h-5 text-blue-400" />
          </div>
          <span className="text-sm font-medium text-slate-200 text-center">
            Drop your hand-drawn sketch here, or <span className="text-blue-400 underline">browse</span>
          </span>
          <span className="text-xs text-slate-500 mt-1">Supports PNG, JPG, JPEG, WebP (up to 10MB)</span>
        </div>
      ) : (
        <div className="relative border border-slate-800 rounded-xl bg-slate-950/80 overflow-hidden p-3">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800/80 text-xs">
            <span className="text-slate-300 font-medium truncate max-w-[200px] flex items-center gap-1.5">
              <ImageIcon className="w-3.5 h-3.5 text-blue-400" />
              {currentImageName || 'Loaded Sketch'}
            </span>
            <div className="flex items-center gap-1.5">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                icon={<RefreshCw className="w-3 h-3" />}
              >
                Replace
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCurrentImage(null)}
                className="text-rose-400 hover:text-rose-300"
                icon={<X className="w-3 h-3" />}
              >
                Remove
              </Button>
            </div>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                processFile(e.target.files[0]);
              }
            }}
          />
          <div className="h-48 w-full bg-slate-900 rounded-lg flex items-center justify-center p-2 border border-slate-800/50">
            <img
              src={currentImageBase64}
              alt="Active Sketch Preview"
              className="max-h-full max-w-full object-contain rounded"
            />
          </div>
        </div>
      )}

      {errorMsg && (
        <p className="text-xs text-rose-400 bg-rose-950/30 border border-rose-900/50 rounded-lg p-2.5">
          {errorMsg}
        </p>
      )}

      {/* Preset Sketch Library */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
            <Sparkles className="w-3 h-3 text-blue-400" />
            Verified Sample Sketches
          </span>
          <span className="text-[11px] text-slate-500">Quick, Draw! & TU-Berlin</span>
        </div>
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
          {SAMPLE_SKETCHES.map((sample) => (
            <button
              key={sample.name}
              onClick={() => loadSample(sample)}
              className="group border border-slate-800/80 hover:border-blue-500/50 bg-slate-900/60 hover:bg-slate-800/60 rounded-lg p-2 text-center transition-all flex flex-col items-center gap-1.5 focus:outline-none"
            >
              <div className="w-12 h-12 bg-white rounded flex items-center justify-center p-1 overflow-hidden shadow-sm">
                <img
                  src={sample.file}
                  alt={sample.name}
                  className="max-h-full max-w-full object-contain"
                />
              </div>
              <span className="text-[11px] font-medium text-slate-300 group-hover:text-blue-300">
                {sample.name}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
