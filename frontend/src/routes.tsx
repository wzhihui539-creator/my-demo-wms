import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import InboundManagement from './pages/InboundManagement';
import OutboundManagement from './pages/OutboundManagement';
import InventoryManagement from './pages/InventoryManagement';
import CheckManagement from './pages/CheckManagement';
import AlertManagement from './pages/AlertManagement';
import ReportManagement from './pages/ReportManagement';
import Settings from './pages/Settings';

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/inbound" element={<InboundManagement />} />
      <Route path="/outbound" element={<OutboundManagement />} />
      <Route path="/inventory" element={<InventoryManagement />} />
      <Route path="/check" element={<CheckManagement />} />
      <Route path="/alerts" element={<AlertManagement />} />
      <Route path="/reports" element={<ReportManagement />} />
      <Route path="/settings" element={<Settings />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
