import React, { useState } from 'react';
import { X, Cloud, CheckCircle, AlertCircle, ExternalLink, Cpu } from 'lucide-react';

export default function ColabModal({ isOpen, onClose, colabUrl, onSaveColabUrl }) {
  const [urlInput, setUrlInput] = useState(colabUrl || '');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  if (!isOpen) return null;

  const handleTestAndSave = async () => {
    if (!urlInput.trim()) {
      onSaveColabUrl('');
      setTestResult({ success: true, message: 'Colab URL cleared. Using local GPU/CPU engine.' });
      return;
    }

    setTesting(true);
    setTestResult(null);

    const cleanUrl = urlInput.trim().replace(/\/+$/, '');
    try {
      const res = await fetch(`${cleanUrl}/health`, { method: 'GET' });
      if (res.ok) {
        const data = await res.json();
        setTestResult({
          success: true,
          message: `Connected to Google Colab GPU! GPU: ${data.gpu || 'NVIDIA T4/A100'}`
        });
        onSaveColabUrl(cleanUrl);
      } else {
        setTestResult({
          success: false,
          message: `Server returned HTTP status ${res.status}`
        });
      }
    } catch (err) {
      setTestResult({
        success: false,
        message: 'Could not connect to Colab URL. Check that ngrok/tunnel is active in your notebook.'
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-lg w-full p-6 shadow-2xl relative flex flex-col gap-4">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Cloud className="w-5 h-5 text-indigo-400" />
            <h3 className="text-base font-bold text-slate-100">Google Colab GPU Inference Server</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Instructions */}
        <div className="text-xs text-slate-400 flex flex-col gap-2">
          <p>
            When running heavy 3D diffusion models (like TripoSR or Stable Fast 3D) that exceed local 4GB VRAM,
            you can run the included Colab notebook on a free cloud NVIDIA T4/A100 GPU:
          </p>
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-300">
            notebooks/Sketch2Shape_Colab_Inference_Server.ipynb
          </div>
          <ol className="list-decimal list-inside space-y-1 text-slate-400 text-[11px]">
            <li>Open the notebook in Google Colab (with free GPU runtime).</li>
            <li>Run all cells to start the FastAPI TripoSR engine.</li>
            <li>Paste the generated ngrok or cloudflared public URL below.</li>
          </ol>
        </div>

        {/* Input */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs text-slate-300 font-medium">Colab Public Tunnel URL</label>
          <input
            type="text"
            placeholder="https://xxxx-xx-xx.ngrok-free.app"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 placeholder:text-slate-600 outline-none focus:border-indigo-500 font-mono"
          />
        </div>

        {/* Test Result Message */}
        {testResult && (
          <div className={`p-3 rounded-xl border flex items-center gap-2 text-xs ${
            testResult.success
              ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
              : 'bg-rose-950/40 border-rose-800 text-rose-300'
          }`}>
            {testResult.success ? <CheckCircle className="w-4 h-4 flex-shrink-0" /> : <AlertCircle className="w-4 h-4 flex-shrink-0" />}
            <span>{testResult.message}</span>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-2 mt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-slate-200"
          >
            Cancel
          </button>
          <button
            onClick={handleTestAndSave}
            disabled={testing}
            className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-colors flex items-center gap-1.5 shadow-lg shadow-indigo-600/30 disabled:opacity-50"
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>{testing ? 'Testing...' : 'Save & Connect'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
