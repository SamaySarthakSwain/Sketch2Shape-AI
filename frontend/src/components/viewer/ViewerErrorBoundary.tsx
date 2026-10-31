import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '../common/Button';

interface Props {
  children: ReactNode;
  fallbackMessage?: string;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ViewerErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Three.js Viewer Error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="w-full h-full min-h-[350px] flex flex-col items-center justify-center p-6 bg-slate-950/80 border border-slate-800 rounded-xl text-center">
          <div className="w-12 h-12 rounded-xl bg-amber-950/50 border border-amber-800/60 flex items-center justify-center text-amber-400 mb-3">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h4 className="text-sm font-semibold text-slate-200">Unable to Render 3D Mesh</h4>
          <p className="text-xs text-slate-400 max-w-sm mt-1 mb-4 font-mono text-[11px]">
            {this.state.error?.message || this.props.fallbackMessage || 'The 3D asset file could not be parsed or contains invalid geometry.'}
          </p>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              this.setState({ hasError: false, error: null });
              this.props.onReset?.();
            }}
            icon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Reset Viewport
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}
