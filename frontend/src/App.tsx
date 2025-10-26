import { useState } from 'react';
import { WelcomeScreen } from './components/WelcomeScreen';
import { Sidebar } from './components/Sidebar';
import { CVScore } from './components/CVScore';
import { ChatAssistant } from './components/ChatAssistant';
import { GitHubProfile } from './components/GitHubProfile';
import { GitHubRepo } from './components/GitHubRepo';
import CareerTodoList from './components/CareerTodoList';
import { SidebarProvider } from './components/ui/sidebar';
import React from 'react';

// Hata olursa beyaz ekran yerine mesaj gösterelim
class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean; message?: string }>{
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, message: '' };
  }
  static getDerivedStateFromError(error: any) {
    return { hasError: true, message: String(error) };
  }
  componentDidCatch(error: any, info: any) {
    console.error('UI crashed:', error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="p-6 m-6 border border-red-300 bg-red-50 text-red-700 rounded">
          <h2 className="font-semibold mb-2">Bir hata oluştu</h2>
          <pre className="whitespace-pre-wrap text-sm">{this.state.message}</pre>
          <p className="mt-2 text-gray-600">Tarayıcı konsolundaki (F12) ayrıntıları da kontrol edin.</p>
        </div>
      );
    }
    return this.props.children as any;
  }
}

export default function App() {
  // Welcome ekranı sonrası ana sayfaya geçiş
  const [entered, setEntered] = useState(false);
  // Sekmeler: cv | github | chat | career (dashboard)
  const [activeView, setActiveView] = useState<'cv' | 'githubprofile' | 'githubrepo' | 'chat' | 'career'>('cv');

  const renderMainView = () => {
    switch (activeView) {
      case 'cv':
        return <CVScore />;
      case 'githubprofile':
        return <GitHubProfile />;
      case 'githubrepo':
        return <GitHubRepo />;
      case 'chat':
        return <ChatAssistant />;
      case 'career':
        return <CareerTodoList />; // Dashboard ayrı bir butonda, tam genişlikte
      default:
        return <CVScore />;
    }
  };

  if (!entered) {
    return (
      <ErrorBoundary>
        <div className="min-h-screen">
          <WelcomeScreen onEnter={() => setEntered(true)} />
        </div>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <SidebarProvider>
        <div className="min-h-screen bg-white">
          <div className="flex">
            {/* Sol menü: CV / GitHub / AI Assistant / Dashboard */}
            <Sidebar activeView={activeView} onNavigate={setActiveView} />

            {/* Ana içerik: seçilen sekmeye göre */}
            <main className="flex-1 p-6 lg:p-8">
              {renderMainView()}
            </main>
          </div>
        </div>
      </SidebarProvider>
    </ErrorBoundary>
  );
}


