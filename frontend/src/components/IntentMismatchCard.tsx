import React from 'react';
import { motion } from 'framer-motion';
import { Target, AlertCircle, CheckCircle2 } from 'lucide-react';

interface IntentMismatchCardProps {
  purpose: string;
  recipientName: string;
  description: string;
  mismatchDetected: boolean;
  explanation?: string;
  intentSummary?: string;
}

export const IntentMismatchCard: React.FC<IntentMismatchCardProps> = ({
  purpose,
  recipientName,
  description,
  mismatchDetected,
  explanation,
  intentSummary,
}) => {
  const color = mismatchDetected ? '#f97316' : '#10b981';
  const Icon = mismatchDetected ? AlertCircle : CheckCircle2;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="rounded-2xl overflow-hidden"
      style={{
        background: `${color}08`,
        border: `1px solid ${color}30`,
      }}
    >
      {/* Header */}
      <div
        className="flex items-center gap-3 px-5 py-4"
        style={{ borderBottom: `1px solid ${color}20` }}
      >
        <div
          className="p-2 rounded-lg"
          style={{ backgroundColor: `${color}20` }}
        >
          <Target size={18} style={{ color }} />
        </div>
        <div>
          <h3 className="font-bold text-slate-100">Payment Intent Verification</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Comparing your stated purpose with payment details
          </p>
        </div>
        <div className="ml-auto">
          <Icon size={20} style={{ color }} />
        </div>
      </div>

      {/* Intent comparison grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-px" style={{ background: `${color}10` }}>
        {/* Your stated intent */}
        <div className="bg-[#0a0d14] px-5 py-4">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
            Your Stated Intent
          </div>
          <p className="text-slate-200 text-sm leading-relaxed">
            "{purpose}"
          </p>
          {intentSummary && (
            <p className="text-xs text-slate-500 mt-2 italic">
              AI summary: {intentSummary}
            </p>
          )}
        </div>

        {/* Actual payment details */}
        <div className="bg-[#0a0d14] px-5 py-4">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
            Actual Payment Details
          </div>
          <div className="space-y-1">
            <p className="text-slate-200 text-sm">
              <span className="text-slate-500">Recipient:</span> {recipientName}
            </p>
            {description && (
              <p className="text-slate-200 text-sm">
                <span className="text-slate-500">Description:</span> {description}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* AI Observation */}
      <div className="px-5 py-4">
        <div className="flex gap-3">
          <div className="flex-shrink-0 mt-0.5">
            <Icon size={16} style={{ color }} />
          </div>
          <div>
            <div className="text-xs font-semibold mb-1" style={{ color }}>
              {mismatchDetected ? 'Potential Mismatch Detected' : 'No Significant Mismatch Detected'}
            </div>
            <p className="text-sm text-slate-300 leading-relaxed">
              {mismatchDetected
                ? explanation || 'The payment details may not fully align with your stated purpose.'
                : 'Your stated payment purpose appears consistent with the payment details provided.'
              }
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
