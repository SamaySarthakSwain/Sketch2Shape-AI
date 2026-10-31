import React, { useState } from 'react';
import { Navbar } from '../common/Navbar';
import { Footer } from '../common/Footer';
import { HistoryDrawer } from '../history/HistoryDrawer';

interface AppLayoutProps {
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [historyOpen, setHistoryOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans selection:bg-blue-600/30 selection:text-blue-200">
      <Navbar onOpenHistory={() => setHistoryOpen(true)} />
      
      <main className="flex-1 flex flex-col">
        {children}
      </main>

      <Footer />

      <HistoryDrawer
        isOpen={historyOpen}
        onClose={() => setHistoryOpen(false)}
      />
    </div>
  );
};
