import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, LayoutDashboard, PlusCircle, History } from 'lucide-react';

const NAV_ITEMS = [
  { to: '/', label: 'Home', icon: <LayoutDashboard size={15} /> },
  { to: '/analyze', label: 'Analyze', icon: <PlusCircle size={15} /> },
  { to: '/history', label: 'History', icon: <History size={15} /> },
];

export const Navbar: React.FC = () => {
  const { pathname } = useLocation();

  return (
    <nav className="sticky top-0 z-50 px-4 py-3 glass-strong border-b border-slate-700/40">
      <div className="max-w-5xl mx-auto flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)' }}>
            <Shield size={16} className="text-white" />
          </div>
          <span className="font-bold text-slate-100 text-base">
            Pay<span className="gradient-text">Guard</span> AI
          </span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          {NAV_ITEMS.map(item => {
            const active =
              item.to === '/'
                ? pathname === '/'
                : pathname.startsWith(item.to) ||
                  (item.to === '/history' && pathname.startsWith('/transaction'));
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  active
                    ? 'text-blue-400 bg-blue-500/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/30'
                }`}
              >
                {item.icon}
                <span className="hidden sm:inline">{item.label}</span>
              </Link>
            );
          })}
        </div>

        {/* Sandbox badge */}
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 border border-amber-500/30 text-amber-400">
          🏖️ Sandbox
        </div>
      </div>
    </nav>
  );
};
