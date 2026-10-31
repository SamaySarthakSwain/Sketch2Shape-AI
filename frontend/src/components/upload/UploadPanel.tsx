import React, { useRef, useState } from 'react';
import { Upload, X, ImageIcon, CheckCircle2 } from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

const SAMPLE_SKETCHES = [
  { name: 'Car', icon: '🚗', file: '/examples/quickdraw_car_normalized.png' },
  { name: 'Chair', icon: '🪑', file: '/examples/quickdraw_chair_normalized.png' },
  { name: 'Cup', icon: '☕', file: '/examples/quickdraw_cup_normalized.png' },
  { name: 'Apple', icon: '🍎', file: '/examples/quickdraw_apple_normalized.png' },
  { name: 'Bicycle', icon: '🚲', file: '/examples/quickdraw_bicycle_normalized.png' },
  { name: 'Airplane', icon: '✈️', file: '/examples/quickdraw_airplane_normalized.png' },
];

export const UploadPanel: React.FC = () => {
  const { currentImageBase64, currentImageName, setCurrentImage } = useAppStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const processFile = (file: File) => {
    setErrorMsg(null);
    const validExtensions = ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff'];
    const ext = file.name.split('.').pop()?.toLowerCase() || '';

    if (!validExtensions.includes(ext) && !file.type.startsWith('image/')) {
      setErrorMsg('Please upload a high-quality image (PNG, JPG, WebP, BMP).');
      return;
    }
    if (file.size > 50 * 1024 * 1024) {
      setErrorMsg('Image size exceeds 50MB limit.');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const b64 = e.target?.result as string;
      setCurrentImage(b64, file.name);
    };
    reader.readAsDataURL(file);
  };

  const loadSample = async (sample: typeof SAMPLE_SKETCHES[0]) => {
    try {
      const res = await fetch(sample.file);
      const blob = await res.blob();
      const reader = new FileReader();
      reader.onload = () => {
        setCurrentImage(reader.result as string, `${sample.name}.png`);
      };
      reader.readAsDataURL(blob);
    } catch {
      setErrorMsg(`Failed to load ${sample.name}`);
    }
  };

  return (
    <div className="space-y-3">
      {!currentImageBase64 ? (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            if (e.dataTransfer.files?.[0]) processFile(e.dataTransfer.files[0]);
          }}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-all ${
            isDragging
              ? 'border-blue-500 bg-blue-950/20 text-blue-200'
              : 'border-slate-800 hover:border-slate-700 bg-slate-900/40 text-slate-400 hover:text-slate-200'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp,image/bmp,image/tiff"
            className="hidden"
            onChange={(e) => {
              if (e.target.files?.[0]) processFile(e.target.files[0]);
            }}
          />
          <div className="w-10 h-10 rounded-xl bg-slate-800/80 flex items-center justify-center text-blue-400 mb-2">
            <Upload className="w-5 h-5" />
          </div>
          <span className="text-xs font-medium text-slate-200">
            Upload high-quality image or sketch
          </span>
          <span className="text-[11px] text-slate-500 mt-0.5">
            PNG, JPG, WebP, or BMP (up to 50MB)
          </span>
        </div>
      ) : (
        <div className="relative border border-slate-800 rounded-xl bg-slate-950/80 p-3">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-xs">
            <div className="flex items-center gap-1.5 truncate max-w-[220px]">
              <ImageIcon className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
              <span className="text-slate-200 font-medium truncate">
                {currentImageName || 'High-Quality Image'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-emerald-400 font-mono bg-emerald-950/60 border border-emerald-900/60 px-1.5 py-0.5 rounded flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                Ready
              </span>
              <button
                onClick={() => setCurrentImage(null, null)}
                className="text-slate-400 hover:text-rose-400 p-0.5 rounded transition-colors"
                title="Remove"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="h-44 w-full bg-slate-900/60 rounded-lg flex items-center justify-center p-2 border border-slate-800/50 overflow-hidden">
            <img
              src={currentImageBase64}
              alt="High-Quality Upload Preview"
              className="max-h-full max-w-full object-contain rounded"
            />
          </div>
        </div>
      )}

      {errorMsg && (
        <p className="text-xs text-rose-400 bg-rose-950/30 border border-rose-900/50 rounded-lg p-2">
          {errorMsg}
        </p>
      )}

      {/* Quick Test Samples */}
      <div className="pt-1">
        <span className="text-[11px] font-medium text-slate-400 block mb-1.5">
          Or test with sample image:
        </span>
        <div className="grid grid-cols-6 gap-1.5">
          {SAMPLE_SKETCHES.map((sample) => (
            <button
              key={sample.name}
              onClick={() => loadSample(sample)}
              className="border border-slate-800 hover:border-blue-500/50 bg-slate-900/60 hover:bg-slate-800/80 rounded-lg py-1.5 px-1 text-center transition-all flex flex-col items-center gap-1 group"
              title={sample.name}
            >
              <span className="text-base group-hover:scale-110 transition-transform">{sample.icon}</span>
              <span className="text-[10px] text-slate-400 group-hover:text-slate-200 truncate w-full">
                {sample.name}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
