import React, { useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  X,
  ShieldCheck,
  CreditCard,
  Info,
  Brain,
  Cpu,
} from 'lucide-react';
import type { AnalyzeResponse, AnalyzeRequest } from '../types/api';
import { RiskScoreGauge } from '../components/RiskScoreGauge';
import { SignalList } from '../components/SignalCard';
import { IntentMismatchCard } from '../components/IntentMismatchCard';
import { PayPalCheckout } from '../components/PayPalCheckout';
import { getRiskColor, formatCurrency } from '../utils/risk';

export const ResultPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as { result: AnalyzeResponse; request: AnalyzeRequest } | null;

  const [showPayPal, setShowPayPal] = useState(false);
  const [paymentSuccess, setPaymentSuccess] = useState(false);
  const [captureId, setCaptureId] = useState('');

  if (!state?.result) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <p className="text-slate-400 mb-4">No analysis result found.</p>
        <Link to="/analyze" className="text-blue-400 hover:underline">← Analyze a payment</Link>
      </div>
    );
  }

  const { result, request } = state;
  const riskColor = getRiskColor(result.risk_level);

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Back button */}
      <button
        onClick={() => navigate('/analyze')}
        className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 mb-6 transition-colors"
      >
        <ArrowLeft size={14} />
        Analyze another payment
      </button>

      {/* ── Header ─────────────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-8"
      >
        <h1 className="text-2xl font-bold text-slate-100 mb-1">Risk Assessment Result</h1>
        <p className="text-sm text-slate-500">Transaction ID: {result.transaction_id.slice(0, 8)}...</p>
      </motion.div>

      {/* ── Risk Score ──────────────────────────────────────── */}
      <div className="glass rounded-2xl p-8 mb-5 flex flex-col items-center">
        <RiskScoreGauge score={result.risk_score} level={result.risk_level} />

        {/* Transaction amount summary */}
        <div className="mt-6 text-center">
          <div className="text-3xl font-bold text-slate-100">
            {formatCurrency(request.amount, request.currency)}
          </div>
          <div className="text-slate-400 text-sm mt-1">
            → {request.recipient_name}
          </div>
          <div className="text-slate-500 text-xs mt-0.5">{request.purpose}</div>
        </div>

        {/* AI metadata */}
        <div className="flex items-center gap-4 mt-5 text-xs text-slate-500">
          <div className="flex items-center gap-1.5">
            <Cpu size={12} />
            Rule Engine: Active
          </div>
          <div className="flex items-center gap-1.5">
            <Brain size={12} style={{ color: result.llm_used ? '#a78bfa' : undefined }} />
            AI: {result.llm_used ? (result.llm_provider || 'Active') : 'Unavailable (rule engine only)'}
          </div>
        </div>
      </div>

      {/* ── Recommendation ─────────────────────────────────── */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="rounded-xl p-4 mb-5"
        style={{ background: `${riskColor}10`, border: `1px solid ${riskColor}30` }}
      >
        <p className="text-sm font-semibold" style={{ color: riskColor }}>
          Recommendation
        </p>
        <p className="text-sm text-slate-300 mt-1 leading-relaxed">{result.recommendation}</p>
      </motion.div>

      {/* ── Intent Mismatch Card ────────────────────────────── */}
      <div className="mb-5">
        <IntentMismatchCard
          purpose={request.purpose}
          recipientName={request.recipient_name}
          description={request.description || ''}
          mismatchDetected={result.intent_mismatch}
          explanation={result.intent_mismatch_explanation}
          intentSummary={result.intent_summary}
        />
      </div>

      {/* ── Risk Signals ────────────────────────────────────── */}
      {result.signals.length > 0 && (
        <div className="mb-5">
          <h2 className="text-base font-bold text-slate-100 mb-3 flex items-center gap-2">
            <ShieldCheck size={16} style={{ color: riskColor }} />
            Detected Risk Signals ({result.signals.length})
          </h2>
          <SignalList signals={result.signals} />
        </div>
      )}

      {/* ── Disclaimer ──────────────────────────────────────── */}
      <div className="flex gap-2 p-4 rounded-xl bg-slate-800/40 border border-slate-700/40 mb-6">
        <Info size={13} className="text-slate-500 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-slate-500 leading-relaxed">{result.disclaimer}</p>
      </div>

      {/* ── Actions ─────────────────────────────────────────── */}
      {!paymentSuccess && !showPayPal && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-3"
        >
          <button
            onClick={() => navigate('/analyze')}
            className="flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold text-slate-300 glass hover:border-slate-500 transition-all"
          >
            <X size={16} />
            Cancel Payment
          </button>
          <Link to={`/transaction/${result.transaction_id}`} className="md:col-span-1">
            <button className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold text-slate-300 glass hover:border-slate-500 transition-all">
              View Full Details
            </button>
          </Link>
          <button
            id="proceed-to-paypal"
            onClick={() => setShowPayPal(true)}
            className="flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-semibold text-white transition-all"
            style={{ background: 'linear-gradient(135deg, #003087, #009cde)' }}
          >
            <CreditCard size={16} />
            Proceed to PayPal
          </button>
        </motion.div>
      )}

      {/* ── PayPal Checkout ─────────────────────────────────── */}
      {showPayPal && !paymentSuccess && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-slate-100">PayPal Sandbox Checkout</h2>
            <button onClick={() => setShowPayPal(false)} className="text-slate-500 hover:text-slate-300">
              <X size={16} />
            </button>
          </div>
          <PayPalCheckout
            transactionId={result.transaction_id}
            amountUsd={result.paypal_amount_usd || (request.amount / 84)}
            amountInr={request.amount}
            riskLevel={result.risk_level}
            onSuccess={(cid) => { setPaymentSuccess(true); setCaptureId(cid); }}
            onCancel={() => setShowPayPal(false)}
            onError={(err) => console.error('PayPal error:', err)}
          />
        </motion.div>
      )}

      {/* ── Payment Success ─────────────────────────────────── */}
      {paymentSuccess && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="rounded-2xl p-8 text-center bg-emerald-500/10 border border-emerald-500/30"
        >
          <div className="text-4xl mb-3">✅</div>
          <h2 className="text-xl font-bold text-emerald-400 mb-2">Sandbox Payment Captured!</h2>
          <p className="text-sm text-slate-400 mb-4">
            This was a PayPal Sandbox test — no real money was transferred.
          </p>
          <p className="text-xs text-slate-500">Capture ID: {captureId}</p>
          <Link to="/history">
            <button className="mt-4 px-6 py-2 rounded-xl text-sm font-semibold text-emerald-400 border border-emerald-500/40 hover:bg-emerald-500/10 transition-all">
              View Transaction History
            </button>
          </Link>
        </motion.div>
      )}
    </div>
  );
};
