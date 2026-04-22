import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './hooks/useAuth';
import AppLayout from './App';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import InboundManagement from './pages/InboundManagement';
import OutboundManagement from './pages/OutboundManagement';
import InventoryManagement from './pages/InventoryManagement';
import CheckManagement from './pages/CheckManagement';
import AlertManagement from './pages/AlertManagement';
import ReportManagement from './pages/ReportManagement';
import Settings from './pages/Settings';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={<AppLayout />}>
                <Route index element={<Dashboard />} />
                <Route path="inbound" element={<InboundManagement />} />
                <Route path="outbound" element={<OutboundManagement />} />
                <Route path="inventory" element={<InventoryManagement />} />
                <Route path="check" element={<CheckManagement />} />
                <Route path="alerts" element={<AlertManagement />} />
                <Route path="reports" element={<ReportManagement />} />
                <Route path="settings" element={<Settings />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </QueryClientProvider>
    </ConfigProvider>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(<App />);