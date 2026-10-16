import React, { useState, useEffect } from 'react';
import { AuthProvider } from './context/AuthContext';
import { Sidebar } from './components/layout/Sidebar';
import { TopNav } from './components/layout/TopNav';
import { OverviewView } from './components/views/OverviewView';
import { LiveMonitoringView } from './components/views/LiveMonitoringView';
import { EnvironmentalMapView } from './components/views/EnvironmentalMapView';
import { AiPredictionsView } from './components/views/AiPredictionsView';
import { AnalyticsView } from './components/views/AnalyticsView';
import { SmartAlertsView } from './components/views/SmartAlertsView';
import { ReportsView } from './components/views/ReportsView';
import { SettingsView } from './components/views/SettingsView';
import { AuthModal } from './components/common/AuthModal';
import { LoadingSkeleton, EmptyState, ErrorState } from './components/common/StateHandler';
import { MONITORING_LOCATIONS } from './data/mockData';
import api from './services/api';

function AppContent() {
  const [currentTab, setCurrentTab] = useState('overview');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [selectedStationId, setSelectedStationId] = useState('all');
  const [timeRange, setTimeRange] = useState('24h');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [viewState, setViewState] = useState('normal'); // 'normal', 'loading', 'empty', 'error'
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [activeAlertCount, setActiveAlertCount] = useState(3);

  const activeStation = MONITORING_LOCATIONS.find((l) => l.id === selectedStationId) || MONITORING_LOCATIONS[0];

  // Refresh alert stats counter
  const refreshStats = async () => {
    try {
      const stats = await api.getAlertStats();
      if (stats && stats.active !== undefined) {
        setActiveAlertCount(stats.active);
      }
    } catch {
      // Ignore if offline
    }
  };

  useEffect(() => {
    refreshStats();
  }, [currentTab]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    refreshStats();
    setTimeout(() => {
      setIsRefreshing(false);
    }, 600);
  };

  const renderActiveView = () => {
    // Demonstrate Loading, Empty, or Error state if requested via state toggle
    if (viewState === 'loading') {
      return (
        <div className="space-y-6">
          <LoadingSkeleton count={4} type="card" />
          <LoadingSkeleton count={1} type="chart" />
        </div>
      );
    }

    if (viewState === 'empty') {
      return (
        <EmptyState
          title="No Station Telemetry Selected"
          message="There are currently no active sensor readings matching your query parameters."
          onReset={() => {
            setSelectedStationId('all');
            setViewState('normal');
          }}
        />
      );
    }

    if (viewState === 'error') {
      return (
        <ErrorState
          title="Telemetry Ingestion Disrupted"
          message="Unable to reach the regional sensor gateway or backend API. Please verify FastAPI backend is active on port 8000."
          onRetry={() => setViewState('normal')}
        />
      );
    }

    // Normal view routing
    switch (currentTab) {
      case 'overview':
        return <OverviewView activeStation={activeStation} />;
      case 'live-monitoring':
        return <LiveMonitoringView />;
      case 'environmental-map':
        return <EnvironmentalMapView />;
      case 'ai-predictions':
        return <AiPredictionsView />;
      case 'analytics':
        return <AnalyticsView />;
      case 'smart-alerts':
        return <SmartAlertsView />;
      case 'reports':
        return <ReportsView />;
      case 'settings':
        return <SettingsView onOpenAuth={() => setIsAuthModalOpen(true)} />;
      default:
        return <OverviewView activeStation={activeStation} />;
    }
  };

  return (
    <div className="min-h-screen bg-[#041510] text-slate-100 flex flex-col antialiased">
      <div className="flex flex-1 min-h-screen relative">
        {/* Collapsible / Responsive Sidebar */}
        <Sidebar
          currentTab={currentTab}
          onSelectTab={setCurrentTab}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          mobileOpen={mobileMenuOpen}
          onCloseMobile={() => setMobileMenuOpen(false)}
        />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0">
          <TopNav
            onToggleMobile={() => setMobileMenuOpen(!mobileMenuOpen)}
            selectedStationId={selectedStationId}
            onSelectStation={setSelectedStationId}
            timeRange={timeRange}
            onSelectTimeRange={setTimeRange}
            onRefresh={handleRefresh}
            isRefreshing={isRefreshing}
            viewState={viewState}
            onToggleViewState={setViewState}
            onOpenAuth={() => setIsAuthModalOpen(true)}
            activeAlertCount={activeAlertCount}
            onNavigateTab={setCurrentTab}
          />

          <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
            {renderActiveView()}
          </main>

          {/* Footer with stage and project info */}
          <footer className="border-t border-forest-800/60 bg-forest-950/40 py-4 px-6 text-center text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2">
            <span>EcoPulse AI — Cloud-Based Environmental Monitoring, Analytics & Prediction Platform</span>
            <span className="text-emerald-400/80 font-mono">Stage 2 Security, Smart Alerts & Reporting</span>
          </footer>
        </div>
      </div>

      {/* Global Authentication Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
