import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Shield, Zap, Eye, History, ArrowRight, CheckCircle2, AlertTriangle } from 'lucide-react';

const FEATURES = [
  {
    icon: <Shield size={22} />,
    color: '#3b82f6',
    title: 'AI Risk Analysis',
    desc: 'LLM-powered analysis of payment context, language, and pressure tactics.',
  },
  {
    icon: <Eye size={22} />,
    color: '#a78bfa',
    title: 'Intent Verification',
    desc: 'Compares your stated purpose against actual payment details for inconsistencies.',
  },
  {
    icon: <Zap size={22} />,
    color: '#f59e0b',
    title: 'Deterministic Engine',
    desc: 'Rule-based pattern detection that always runs — even without AI.',
  },
  {
    icon: <History size={22} />,
    color: '#10b981',
    title: 'Transaction History',
    desc: 'Review past analyses with full risk breakdowns and PayPal status.',
  },
];

const EXAMPLE_SCENARIOS = [
  { score: 12, level: 'LOW', desc: 'Paying rent to your landlord', color: '#10b981' },
  { score: 64, level: 'MEDIUM', desc: 'Buying from an unverified online seller', color: '#f59e0b' },
  { score: 87, level: 'HIGH', desc: '"Send immediately, don\'t mention the purpose"', color: '#f97316' },
];

export const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen">
      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="relative overflow-hidden px-4 pt-20 pb-16 md:pt-32 md:pb-24 text-center">
        {/* Background glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full opacity-20"
          style={{ background: 'radial-gradient(ellipse, #3b82f6, transparent 70%)', filter: 'blur(60px)' }}
        />

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="relative max-w-3xl mx-auto"
        >
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium mb-6"
            style={{ background: '#3b82f620', border: '1px solid #3b82f640', color: '#60a5fa' }}>
            <Shield size={14} />
            PayPal AI Hackathon 2026
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold mb-4 leading-tight">
            <span className="gradient-text">Think before</span>
            <br />
            <span className="text-slate-100">you pay.</span>
          </h1>

          <p className="text-lg md:text-xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed">
            PayGuard AI analyzes the context of your payment — the message, the recipient, the
            purpose — and highlights potential risks <em>before</em> you send money.
          </p>

          <div className="flex flex-wrap justify-center gap-4">
            <Link to="/analyze">
              <motion.button
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.97 }}
                className="flex items-center gap-2 px-8 py-3.5 rounded-xl font-semibold text-white text-base transition-all"
                style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)' }}
              >
                Analyze a Payment
                <ArrowRight size={18} />
              </motion.button>
            </Link>
            <Link to="/history">
              <motion.button
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.97 }}
                className="flex items-center gap-2 px-8 py-3.5 rounded-xl font-semibold text-slate-300 text-base glass transition-all"
              >
                <History size={18} />
                View History
              </motion.button>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* ── Example risk scores ──────────────────────────────── */}
      <section className="px-4 pb-16 max-w-4xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {EXAMPLE_SCENARIOS.map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + i * 0.1 }}
              className="rounded-xl p-5 glass"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-3xl font-bold" style={{ color: s.color }}>{s.score}</span>
                <span
                  className="px-3 py-1 rounded-full text-xs font-bold"
                  style={{ backgroundColor: `${s.color}20`, color: s.color, border: `1px solid ${s.color}40` }}
                >
                  {s.level}
                </span>
              </div>
              <p className="text-sm text-slate-400">{s.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────── */}
      <section className="px-4 pb-20 max-w-5xl mx-auto">
        <motion.h2
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          className="text-2xl md:text-3xl font-bold text-center text-slate-100 mb-10"
        >
          How PayGuard AI protects you
        </motion.h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {FEATURES.map((f, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="rounded-xl p-6 glass hover:border-slate-600 transition-colors"
            >
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center mb-4"
                style={{ backgroundColor: `${f.color}20`, color: f.color }}
              >
                {f.icon}
              </div>
              <h3 className="font-bold text-slate-100 mb-2">{f.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Disclaimer ───────────────────────────────────────── */}
      <section className="px-4 pb-12 max-w-2xl mx-auto text-center">
        <div className="flex items-start gap-2 p-4 rounded-xl bg-slate-800/40 border border-slate-700/50">
          <AlertTriangle size={14} className="text-amber-400 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-slate-500 text-left leading-relaxed">
            PayGuard AI provides risk assessments based on AI analysis and rule-based detection.
            It does not guarantee that any transaction is safe or fraudulent.
            The final payment decision is always yours.
          </p>
        </div>
      </section>
    </div>
  );
};
