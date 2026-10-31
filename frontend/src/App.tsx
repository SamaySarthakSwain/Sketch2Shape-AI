import React from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { Workspace } from './pages/Workspace';

export default function App() {
  return (
    <AppLayout>
      <Workspace />
    </AppLayout>
  );
}
