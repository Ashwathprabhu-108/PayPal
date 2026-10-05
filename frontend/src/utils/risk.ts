import type { RiskLevel, SignalSeverity } from '../types/api';

export const getRiskColor = (level: RiskLevel): string => {
  switch (level) {
    case 'LOW': return '#10b981';
    case 'MEDIUM': return '#f59e0b';
    case 'HIGH': return '#f97316';
    case 'CRITICAL': return '#ef4444';
    default: return '#64748b';
  }
};

export const getRiskBgClass = (level: RiskLevel): string => {
  switch (level) {
    case 'LOW': return 'bg-risk-low';
    case 'MEDIUM': return 'bg-risk-medium';
    case 'HIGH': return 'bg-risk-high';
    case 'CRITICAL': return 'bg-risk-critical';
    default: return '';
  }
};

export const getRiskTextClass = (level: RiskLevel): string => {
  switch (level) {
    case 'LOW': return 'risk-low';
    case 'MEDIUM': return 'risk-medium';
    case 'HIGH': return 'risk-high';
    case 'CRITICAL': return 'risk-critical';
    default: return '';
  }
};

export const getSeverityColor = (severity: SignalSeverity): string => {
  switch (severity) {
    case 'low': return '#64748b';
    case 'medium': return '#f59e0b';
    case 'high': return '#f97316';
    case 'critical': return '#ef4444';
    default: return '#64748b';
  }
};

export const formatCurrency = (amount: number, currency = 'INR'): string => {
  if (currency === 'INR') {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(amount);
};

export const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const getRiskEmoji = (level: RiskLevel): string => {
  switch (level) {
    case 'LOW': return '✅';
    case 'MEDIUM': return '⚠️';
    case 'HIGH': return '🚨';
    case 'CRITICAL': return '🛑';
    default: return '❓';
  }
};

export const getSourceLabel = (source: string): string => {
  switch (source) {
    case 'rule_engine': return 'Rule Engine';
    case 'llm': return 'AI Analysis';
    case 'intent_check': return 'Intent Check';
    default: return source;
  }
};
