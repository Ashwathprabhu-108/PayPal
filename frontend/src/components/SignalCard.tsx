import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, AlertTriangle, Zap, Brain, Eye } from 'lucide-react';
import type { RiskSignal } from '../types/api';
import { getSeverityColor, getSourceLabel } from '../utils/risk';

interface SignalCardProps {
  signal: RiskSignal;
  index: number;
}

const SOURCE_ICONS: Record<string, React.ReactNode> = {
  rule_engine: <Zap size={12} />,
  llm: <Brain size={12} />,
  intent_check: <Eye size={12} />,
};

export const SignalCard: React.FC<SignalCardProps> = ({ signal, index }) => {
  const [expanded, setExpanded] = useState(false);
  const color = getSeverityColor(signal.severity);

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.08 }}
      className="rounded-xl overflow-hidden cursor-pointer"
      style={{
        background: `${color}10`,
        border: `1px solid ${color}30`,
      }}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-center gap-3 p-4">
        {/* Severity dot */}
        <div
          className="w-2 h-2 rounded-full flex-shrink-0"
          style={{ backgroundColor: color, boxShadow: `0 0 6px ${color}` }}
        />

        {/* Title */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-sm text-slate-100">{signal.title}</span>
            {/* Source badge */}
            <span
              className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium"
              style={{ backgroundColor: `${color}20`, color }}
            >
              {SOURCE_ICONS[signal.source]}
              {getSourceLabel(signal.source)}
            </span>
          </div>
          {/* Severity label */}
          <div className="text-xs mt-0.5 font-medium capitalize" style={{ color }}>
            {signal.severity} severity
            {signal.score_contribution > 0 && (
              <span className="text-slate-500 ml-2">+{signal.score_contribution} pts</span>
            )}
          </div>
        </div>

        {/* Expand chevron */}
        <motion.div
          animate={{ rotate: expanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="text-slate-500 flex-shrink-0"
        >
          <ChevronDown size={16} />
        </motion.div>
      </div>

      {/* Expanded explanation */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <div
              className="px-4 pb-4 text-sm text-slate-300 leading-relaxed border-t"
              style={{ borderColor: `${color}20` }}
            >
              <div className="flex gap-2 mt-3">
                <AlertTriangle size={14} className="flex-shrink-0 mt-0.5" style={{ color }} />
                <p>{signal.explanation}</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

interface SignalListProps {
  signals: RiskSignal[];
}

export const SignalList: React.FC<SignalListProps> = ({ signals }) => {
  if (signals.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        <p>No specific risk signals detected.</p>
      </div>
    );
  }

  // Sort: critical → high → medium → low
  const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
  const sorted = [...signals].sort(
    (a, b) => severityOrder[a.severity] - severityOrder[b.severity]
  );

  return (
    <div className="flex flex-col gap-3">
      {sorted.map((signal, i) => (
        <SignalCard key={`${signal.type}-${signal.source}`} signal={signal} index={i} />
      ))}
    </div>
  );
};
