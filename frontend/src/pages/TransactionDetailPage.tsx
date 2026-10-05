import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Loader2,
  AlertTriangle,
  Brain,
  Cpu,
  Eye,
  CreditCard,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldCheck,
  Info,
} from 'lucide-react';
import { getTransaction } from '../services/api';
import type { TransactionDetail, PayPalStatus, RiskLevel } from '../types/api';
import { RiskScoreGauge } from '../components/RiskScoreGauge';
import { SignalList } from '../components/SignalCard';
import { IntentMismatchCard } from '../components/IntentMismatchCard';
import { getRiskColor, formatCurrency, formatDate } from '../utils/risk';

type StatusIcon = React.FC<{ size?: number; style?: React.CSSProperties; className?: string }>;
const PAYPAL_STATUS_META: Record<PayPalStatus, { label: string; color: string; Icon: StatusIcon }> = {
  NOT_INITIATED: { label: 'Not Paid', color: '#64748b', Icon: Clock as StatusIcon },
  PENDING: { label: 'Pending', color: '#60a5fa', Icon: Loader2 as StatusIcon },
  APPROVED: { label: 'Approved', color: '#60a5fa', Icon: CheckCircle2 as StatusIcon },
  CAPTURED: { label: 'Completed', color: '#10b981', Icon: CheckCircle2 as StatusIcon },
  CANCELLED: { label: 'Cancelled', color: '#64748b', Icon: XCircle as StatusIcon },
  FAILED: { label: 'Failed', color: '#ef4444', Icon: XCircle as StatusIcon },
};

const DetailRow: React.FC<{ label: string; value: React.ReactNode }> = ({ label, value }) => (
  <div className="flex justify-between items-start py-2.5 border-b border-slate-700/30 last:border-0">
    <span className="text-xs text-slate-500 font-medium uppercase tracking-wide flex-shrink-0 mr-4">{label}</span>
    <span className="text-sm text-slate-200 text-right">{value}</span>
  </div>
);

export const TransactionDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [tx, setTx] = useState<TransactionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getTransaction(id)
      .then(setTx)
      .catch(() => setError('Transaction not found or backend is not running.'))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <Loader2 size={28} className="animate-spin text-blue-400" />
      </div>
    );
  }

  if (error || !tx) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <AlertTriangle size={40} className="text-red-400 mx-auto mb-4" />
        <p className="text-slate-400 mb-4">{error || 'Transaction not found.'}</p>
        <Link to="/history" className="text-blue-400 hover:underline">← Back to History</Link>
      </div>
    );
  }

  const riskColor = getRiskColor(tx.risk_level as RiskLevel);
  const paypalMeta = PAYPAL_STATUS_META[tx.paypal_status];

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Back button */}
      <button
        onClick={() => navigate('/history')}
        className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 mb-6 transition-colors"
      >
        <ArrowLeft size={14} />
        Back to History
      </button>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-slate-100 mb-1">Transaction Detail</h1>
          <p className="text-sm text-slate-500 font-mono">{tx.id}</p>
          <p className="text-xs text-slate-600 mt-1">{formatDate(tx.created_at)}</p>
        </div>

        {/* Risk score */}
        <div className="glass rounded-2xl p-8 mb-5 flex flex-col items-center">
          <RiskScoreGauge score={tx.risk_score} level={tx.risk_level as RiskLevel} animated={false} />

          <div className="mt-6 text-center">
            <div className="text-3xl font-bold text-slate-100">
              {formatCurrency(tx.amount, tx.currency)}
            </div>
            <div className="text-slate-400 text-sm mt-1">→ {tx.recipient_name}</div>
            <div className="text-slate-500 text-xs mt-0.5">{tx.purpose}</div>
          </div>

          {/* AI/Engine metadata */}
          <div className="flex items-center gap-4 mt-5 text-xs text-slate-500">
            <div className="flex items-center gap-1.5">
              <Cpu size={12} />
              Rule Engine: Active
            </div>
            <div className="flex items-center gap-1.5">
              <Brain size={12} style={{ color: tx.llm_used ? '#a78bfa' : undefined }} />
              AI: {tx.llm_used ? (tx.llm_provider || 'Active') : 'Rule engine only'}
            </div>
          </div>
        </div>

        {/* Recommendation */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="rounded-xl p-4 mb-5"
          style={{ background: `${riskColor}10`, border: `1px solid ${riskColor}30` }}
        >
          <p className="text-sm font-semibold" style={{ color: riskColor }}>Recommendation</p>
          <p className="text-sm text-slate-300 mt-1 leading-relaxed">{tx.recommendation}</p>
        </motion.div>

        {/* Payment Details */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.35 }}
          className="glass rounded-2xl p-5 mb-5"
        >
          <h2 className="text-base font-bold text-slate-100 mb-4 flex items-center gap-2">
            <Info size={16} className="text-blue-400" />
            Payment Details
          </h2>
          <DetailRow label="Recipient" value={tx.recipient_name} />
          <DetailRow label="Recipient Type" value={
            <span className="capitalize">{tx.recipient_type}</span>
          } />
          <DetailRow label="Amount" value={formatCurrency(tx.amount, tx.currency)} />
          {tx.paypal_amount_usd && (
            <DetailRow label="PayPal Amount" value={`$${tx.paypal_amount_usd.toFixed(2)} USD`} />
          )}
          <DetailRow label="Purpose" value={tx.purpose} />
          {tx.description && (
            <DetailRow label="Description" value={tx.description} />
          )}
          {tx.message && (
            <DetailRow
              label="Seller Message"
              value={
                <span className="max-w-xs text-xs text-slate-400 leading-relaxed whitespace-pre-wrap">
                  {tx.message.length > 200 ? tx.message.slice(0, 200) + '…' : tx.message}
                </span>
              }
            />
          )}
        </motion.div>

        {/* PayPal Status */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="glass rounded-2xl p-5 mb-5"
        >
          <h2 className="text-base font-bold text-slate-100 mb-4 flex items-center gap-2">
            <CreditCard size={16} className="text-blue-400" />
            PayPal Sandbox Status
          </h2>
          <div className="flex items-center gap-3">
            <paypalMeta.Icon size={18} style={{ color: paypalMeta.color }} className={tx.paypal_status === 'PENDING' ? 'animate-spin' : ''} />
            <span className="font-semibold text-sm" style={{ color: paypalMeta.color }}>
              {paypalMeta.label}
            </span>
          </div>
          {tx.paypal_order_id && (
            <p className="text-xs text-slate-500 mt-2 font-mono">Order ID: {tx.paypal_order_id}</p>
          )}
          {tx.paypal_capture_id && (
            <p className="text-xs text-slate-500 mt-1 font-mono">Capture ID: {tx.paypal_capture_id}</p>
          )}
          {tx.paypal_status === 'NOT_INITIATED' && (
            <p className="text-xs text-slate-600 mt-2">No PayPal payment was initiated for this analysis.</p>
          )}
        </motion.div>

        {/* Intent Mismatch */}
        <div className="mb-5">
          <IntentMismatchCard
            purpose={tx.purpose}
            recipientName={tx.recipient_name}
            description={tx.description}
            mismatchDetected={tx.intent_mismatch}
            explanation={tx.intent_mismatch_explanation}
            intentSummary={undefined}
          />
        </div>

        {/* Risk Signals */}
        {tx.signals.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mb-5"
          >
            <h2 className="text-base font-bold text-slate-100 mb-3 flex items-center gap-2">
              <ShieldCheck size={16} style={{ color: riskColor }} />
              Detected Risk Signals ({tx.signals.length})
            </h2>
            <SignalList signals={tx.signals} />
          </motion.div>
        )}

        {/* Disclaimer */}
        <div className="flex gap-2 p-4 rounded-xl bg-slate-800/40 border border-slate-700/40 mb-6">
          <Info size={13} className="text-slate-500 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-slate-500 leading-relaxed">{tx.disclaimer}</p>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <Link to="/history" className="flex-1">
            <button className="w-full py-3 rounded-xl text-sm font-semibold text-slate-300 glass hover:border-slate-500 transition-all">
              ← Back to History
            </button>
          </Link>
          <Link to="/analyze" className="flex-1">
            <button
              className="w-full py-3 rounded-xl text-sm font-semibold text-white transition-all"
              style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)' }}
            >
              Analyze Another
            </button>
          </Link>
        </div>
      </motion.div>
    </div>
  );
};
