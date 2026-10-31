import React from 'react';
import { useAppStore } from './store/useAppStore';
import { AppLayout } from './components/layout/AppLayout';
import { Workspace } from './pages/Workspace';
import { Gallery } from './pages/Gallery';

export default function App() {
  const { activeTab } = useAppStore();

  const renderActivePage = () => {
    switch (activeTab) {
      case 'gallery':
        return <Gallery />;
      case 'workspace':
      default:
        return <Workspace />;
    }
  };

  return <AppLayout>{renderActivePage()}</AppLayout>;
}
