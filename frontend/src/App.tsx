import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { HomePage } from './pages/HomePage';
import { AnalyzePage } from './pages/AnalyzePage';
import { ResultPage } from './pages/ResultPage';
import { HistoryPage } from './pages/HistoryPage';
import { TransactionDetailPage } from './pages/TransactionDetailPage';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/analyze" element={<AnalyzePage />} />
            <Route path="/result" element={<ResultPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/transaction/:id" element={<TransactionDetailPage />} />
            <Route path="*" element={
              <div className="text-center py-20 text-slate-400">
                Page not found. <a href="/" className="text-blue-400 hover:underline">Go home</a>
              </div>
            } />
          </Routes>
        </main>
        <footer className="text-center py-4 text-xs text-slate-600 border-t border-slate-800">
          PayGuard AI — PayPal AI Hackathon 2026 · Risk assessments are not fraud guarantees
        </footer>
      </div>
    </BrowserRouter>
  );
};

export default App;
