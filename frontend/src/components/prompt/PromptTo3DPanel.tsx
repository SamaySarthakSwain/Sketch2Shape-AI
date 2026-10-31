import React from 'react';
import { useAppStore } from '../../store/useAppStore';

const INSPIRATIONS = [
  { label: 'Red Sports Car', icon: '🏎️', prompt: 'A sleek crimson red sports car with silver rims and glossy finish' },
  { label: 'Blue Chair', icon: '🪑', prompt: 'A modern royal blue armchair with clean wooden legs and comfortable cushions' },
  { label: 'Turquoise Mug', icon: '☕', prompt: 'A handcrafted ceramic turquoise coffee mug with smooth rounded handle' },
  { label: 'Glossy Apple', icon: '🍎', prompt: 'A fresh vibrant red apple with realistic brown stem' },
];

export const PromptTo3DPanel: React.FC = () => {
  const { textPrompt, setTextPrompt } = useAppStore();

  return (
    <div className="space-y-3">
      <div>
        <textarea
          rows={3}
          value={textPrompt}
          onChange={(e) => setTextPrompt(e.target.value)}
          placeholder='Describe what to create (e.g. "A red sports car with silver wheels", "A modern blue chair")...'
          className="w-full text-xs bg-slate-900 border border-slate-800 rounded-xl p-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500/50 focus:border-blue-500/80 transition-all resize-none shadow-inner"
        />
      </div>

      {/* Quick Inspiration Pills */}
      <div>
        <span className="text-[11px] font-medium text-slate-400 block mb-1.5">
          Inspirations:
        </span>
        <div className="grid grid-cols-2 gap-1.5">
          {INSPIRATIONS.map((item) => (
            <button
              key={item.label}
              onClick={() => setTextPrompt(item.prompt)}
              className="px-2.5 py-1.5 rounded-lg border border-slate-800/80 bg-slate-900/60 hover:bg-slate-800/80 text-left text-xs text-slate-300 hover:text-white flex items-center gap-2 transition-all group"
            >
              <span className="text-sm group-hover:scale-110 transition-transform">{item.icon}</span>
              <span className="truncate text-[11px]">{item.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
