import React, { useEffect, useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Plus, RefreshCw, AlertTriangle, Clock, CheckCircle2, XCircle, Loader2, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { listTransactions } from '../services/api';
import type { TransactionSummary, RiskLevel, PayPalStatus } from '../types/api';
import { getRiskColor, formatCurrency, formatDate } from '../utils/risk';

const PAYPAL_STATUS_ICONS: Record<PayPalStatus, React.ReactNode> = {
  NOT_INITIATED: <Clock size={12} className="text-slate-500" />,
  PENDING: <Loader2 size={12} className="text-blue-400 animate-spin" />,
  APPROVED: <CheckCircle2 size={12} className="text-blue-400" />,
  CAPTURED: <CheckCircle2 size={12} className="text-emerald-400" />,
  CANCELLED: <XCircle size={12} className="text-slate-500" />,
  FAILED: <XCircle size={12} className="text-red-400" />,
};

const PAYPAL_STATUS_LABEL: Record<PayPalStatus, string> = {
  NOT_INITIATED: 'Not paid',
  PENDING: 'Pending',
  APPROVED: 'Approved',
  CAPTURED: 'Completed',
  CANCELLED: 'Cancelled',
  FAILED: 'Failed',
};

const RiskBadge: React.FC<{ level: RiskLevel; score: number }> = ({ level, score }) => {
  const color = getRiskColor(level);
  return (
    <div className="flex items-center gap-2">
      <span className="font-bold text-lg" style={{ color }}>{score}</span>
      <span
        className="px-2 py-0.5 rounded-full text-xs font-bold"
        style={{ backgroundColor: `${color}20`, color, border: `1px solid ${color}30` }}
      >
        {level}
      </span>
    </div>
  );
};

export const HistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [transactions, setTransactions] = useState<TransactionSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await listTransactions(50);
      setTransactions(data.transactions);
      setTotal(data.total);
    } catch {
      setError('Failed to load transaction history. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const stats = useMemo(() => {
    const counts: Record<RiskLevel, number> = { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };
    let totalScore = 0;
    transactions.forEach(tx => {
      counts[tx.risk_level]++;
      totalScore += tx.risk_score;
    });
    const avgScore = transactions.length ? Math.round(totalScore / transactions.length) : 0;
    const chartData = (['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as RiskLevel[]).map(level => ({
      name: level,
      count: counts[level],
      color: getRiskColor(level),
    }));
    return { counts, avgScore, chartData };
  }, [transactions]);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Transaction History</h1>
          <p className="text-sm text-slate-500 mt-0.5">{total} analysis{total !== 1 ? 'es' : ''} recorded</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={load}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm text-slate-300 glass hover:border-slate-500 transition-all"
          >
            <RefreshCw size={14} />
            Refresh
          </button>
          <Link to="/analyze">
            <button
              id="new-analysis-btn"
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white transition-all"
              style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)' }}
            >
              <Plus size={14} />
              New Analysis
            </button>
          </Link>
        </div>
      </div>

      {/* Stats cards — shown once data is loaded */}
      {!loading && transactions.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mb-6 grid grid-cols-2 md:grid-cols-5 gap-3"
        >
          {(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as RiskLevel[]).map(level => {
            const color = getRiskColor(level);
            return (
              <div
                key={level}
                className="rounded-xl p-4 flex flex-col gap-1"
                style={{ background: `${color}10`, border: `1px solid ${color}25` }}
              >
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{level}</span>
                <span className="text-2xl font-bold" style={{ color }}>{stats.counts[level]}</span>
              </div>
            );
          })}
          {/* Average score card */}
          <div className="rounded-xl p-4 flex flex-col gap-1 glass">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide flex items-center gap-1">
              <TrendingUp size={11} /> Avg Score
            </span>
            <span className="text-2xl font-bold text-slate-200">{stats.avgScore}</span>
          </div>
        </motion.div>
      )}

      {/* Bar chart */}
      {!loading && transactions.length > 1 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="glass rounded-2xl p-5 mb-6"
        >
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Risk Distribution</p>
          <ResponsiveContainer width="100%" height={72}>
            <BarChart data={stats.chartData} layout="vertical" margin={{ left: 0, right: 16, top: 0, bottom: 0 }}>
              <XAxis type="number" hide allowDecimals={false} />
              <YAxis type="category" dataKey="name" width={72} tick={{ fontSize: 11, fill: '#64748b' }} />
              <Tooltip
                cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                contentStyle={{ background: '#111827', border: '1px solid #1e2d3d', borderRadius: 8, fontSize: 12 }}
                formatter={(val: number) => [`${val} transaction${val !== 1 ? 's' : ''}`, '']}
              />
              <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={14}>
                {stats.chartData.map(entry => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-16">
          <Loader2 size={24} className="animate-spin text-blue-400" />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          <AlertTriangle size={14} />
          {error}
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && transactions.length === 0 && (
        <div className="text-center py-20">
          <div className="text-4xl mb-4">🔍</div>
          <p className="text-slate-400 mb-4">No transactions analyzed yet.</p>
          <Link to="/analyze">
            <button className="px-6 py-2.5 rounded-xl text-sm font-semibold text-white"
              style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)' }}>
              Analyze your first payment
            </button>
          </Link>
        </div>
      )}

      {/* Transaction table */}
      {!loading && transactions.length > 0 && (
        <div className="glass rounded-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Date</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Recipient</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Amount</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Risk</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">PayPal</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Intent</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx, i) => (
                  <motion.tr
                    key={tx.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.04 }}
                    className="border-b border-slate-700/30 hover:bg-slate-800/30 transition-colors cursor-pointer"
                    onClick={() => navigate(`/transaction/${tx.id}`)}
                  >
                    <td className="px-5 py-4 text-xs text-slate-500 whitespace-nowrap">
                      {formatDate(tx.created_at)}
                    </td>
                    <td className="px-5 py-4">
                      <div className="text-sm font-medium text-slate-200">{tx.recipient_name}</div>
                      <div className="text-xs text-slate-500 truncate max-w-[160px]">{tx.purpose}</div>
                    </td>
                    <td className="px-5 py-4 text-sm font-semibold text-slate-200 whitespace-nowrap">
                      {formatCurrency(tx.amount, tx.currency)}
                    </td>
                    <td className="px-5 py-4">
                      <RiskBadge level={tx.risk_level} score={tx.risk_score} />
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-1.5 text-xs text-slate-400">
                        {PAYPAL_STATUS_ICONS[tx.paypal_status]}
                        {PAYPAL_STATUS_LABEL[tx.paypal_status]}
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      {tx.intent_mismatch ? (
                        <span className="flex items-center gap-1 text-xs text-orange-400">
                          <AlertTriangle size={11} />
                          Mismatch
                        </span>
                      ) : (
                        <span className="text-xs text-slate-500">—</span>
                      )}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
