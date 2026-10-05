import React from 'react';
import { motion } from 'framer-motion';
import { Shield, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { RiskLevel } from '../types/api';
import { getRiskColor } from '../utils/risk';

interface RiskScoreGaugeProps {
  score: number;
  level: RiskLevel;
  animated?: boolean;
}

const LEVEL_LABELS: Record<RiskLevel, string> = {
  LOW: 'Low Risk',
  MEDIUM: 'Medium Risk',
  HIGH: 'High Risk',
  CRITICAL: 'Critical Risk',
};

const LEVEL_ICONS: Record<RiskLevel, React.ReactNode> = {
  LOW: <TrendingDown size={20} />,
  MEDIUM: <Minus size={20} />,
  HIGH: <TrendingUp size={20} />,
  CRITICAL: <Shield size={20} />,
};

export const RiskScoreGauge: React.FC<RiskScoreGaugeProps> = ({
  score,
  level,
  animated = true,
}) => {
  const color = getRiskColor(level);
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative" style={{ width: 200, height: 200 }}>
        {/* Pulse ring for HIGH/CRITICAL */}
        {(level === 'HIGH' || level === 'CRITICAL') && (
          <div
            className="absolute inset-0 rounded-full animate-pulse-ring"
            style={{ border: `2px solid ${color}`, opacity: 0.3 }}
          />
        )}

        {/* Background SVG */}
        <svg width="200" height="200" style={{ transform: 'rotate(-90deg)' }}>
          {/* Track */}
          <circle
            cx="100" cy="100" r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.05)"
            strokeWidth="12"
          />
          {/* Score arc */}
          <motion.circle
            cx="100" cy="100" r={radius}
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: animated ? dashOffset : dashOffset }}
            transition={{ duration: 1.5, ease: 'easeOut', delay: 0.3 }}
            style={{ filter: `drop-shadow(0 0 8px ${color}40)` }}
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5, duration: 0.5 }}
            className="text-5xl font-bold"
            style={{ color }}
          >
            {score}
          </motion.div>
          <div className="text-sm text-slate-400 font-medium">/ 100</div>
        </div>
      </div>

      {/* Level badge */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="flex items-center gap-2 px-4 py-2 rounded-full font-semibold text-sm"
        style={{
          color,
          backgroundColor: `${color}20`,
          border: `1px solid ${color}40`,
        }}
      >
        {LEVEL_ICONS[level]}
        {LEVEL_LABELS[level]}
      </motion.div>
    </div>
  );
};
