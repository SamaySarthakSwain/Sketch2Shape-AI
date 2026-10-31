import React from 'react';
import { useAppStore } from './store/useAppStore';
import { AppLayout } from './components/layout/AppLayout';
import { Home } from './pages/Home';
import { Workspace } from './pages/Workspace';
import { Gallery } from './pages/Gallery';
import { About } from './pages/About';

export default function App() {
  const { activeTab } = useAppStore();

  const renderActivePage = () => {
    switch (activeTab) {
      case 'home':
        return <Home />;
      case 'workspace':
        return <Workspace />;
      case 'gallery':
        return <Gallery />;
      case 'about':
        return <About />;
      default:
        return <Home />;
    }
  };

  return <AppLayout>{renderActivePage()}</AppLayout>;
}
