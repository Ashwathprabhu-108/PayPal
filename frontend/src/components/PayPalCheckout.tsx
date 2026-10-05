import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { PayPalButtons, PayPalScriptProvider } from '@paypal/react-paypal-js';
import { ExternalLink, Loader2, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import { createPayPalOrder, capturePayPalOrder } from '../services/api';
import type { RiskLevel } from '../types/api';
import { getRiskColor } from '../utils/risk';

interface PayPalCheckoutProps {
  transactionId: string;
  amountUsd: number;
  amountInr: number;
  riskLevel: RiskLevel;
  onSuccess: (captureId: string) => void;
  onCancel: () => void;
  onError: (error: string) => void;
}

export const PayPalCheckout: React.FC<PayPalCheckoutProps> = ({
  transactionId,
  amountUsd,
  amountInr,
  riskLevel,
  onSuccess,
  onCancel,
  onError,
}) => {
  const [status, setStatus] = useState<'idle' | 'processing' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const clientId = import.meta.env.VITE_PAYPAL_CLIENT_ID || '';
  const riskColor = getRiskColor(riskLevel);

  const handleCreateOrder = async () => {
    try {
      setStatus('processing');
      const order = await createPayPalOrder({ transaction_id: transactionId });
      return order.order_id;
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Failed to create PayPal order.';
      setStatus('error');
      setMessage(msg);
      onError(msg);
      throw err;
    }
  };

  const handleApprove = async (data: { orderID: string }) => {
    try {
      setStatus('processing');
      const capture = await capturePayPalOrder({
        transaction_id: transactionId,
        order_id: data.orderID,
      });
      setStatus('success');
      setMessage(`Payment captured. Capture ID: ${capture.capture_id}`);
      onSuccess(capture.capture_id);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Payment capture failed.';
      setStatus('error');
      setMessage(msg);
      onError(msg);
    }
  };

  if (!clientId) {
    return (
      <div className="rounded-xl p-4 bg-amber-500/10 border border-amber-500/30 text-amber-400 text-sm">
        <AlertTriangle size={14} className="inline mr-2" />
        PayPal Client ID not configured. Add <code>VITE_PAYPAL_CLIENT_ID</code> to your <code>.env</code> file.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Amount summary */}
      <div className="rounded-xl p-4 bg-slate-800/50 border border-slate-700/50">
        <div className="flex justify-between items-center text-sm">
          <span className="text-slate-400">Sandbox payment amount</span>
          <span className="font-bold text-white">${amountUsd.toFixed(2)} USD</span>
        </div>
        <div className="flex justify-between items-center text-xs mt-1">
          <span className="text-slate-500">Original amount</span>
          <span className="text-slate-400">₹{amountInr.toLocaleString('en-IN')} INR</span>
        </div>
        <p className="text-xs text-slate-500 mt-2 border-t border-slate-700/50 pt-2">
          🏖️ Sandbox mode — no real money is transferred
        </p>
      </div>

      {/* Risk warning for HIGH/CRITICAL */}
      {(riskLevel === 'HIGH' || riskLevel === 'CRITICAL') && (
        <div
          className="rounded-xl p-4 border text-sm"
          style={{ backgroundColor: `${riskColor}10`, borderColor: `${riskColor}30`, color: riskColor }}
        >
          <AlertTriangle size={14} className="inline mr-2" />
          <strong>You are proceeding despite {riskLevel.toLowerCase()} risk signals.</strong>
          <p className="mt-1 opacity-80 text-xs">
            This is a sandbox test only. In production, please verify this payment carefully.
          </p>
        </div>
      )}

      {/* Status messages */}
      {status === 'processing' && (
        <div className="flex items-center gap-2 text-blue-400 text-sm">
          <Loader2 size={14} className="animate-spin" />
          Processing payment...
        </div>
      )}
      {status === 'success' && (
        <div className="flex items-center gap-2 text-emerald-400 text-sm">
          <CheckCircle2 size={14} />
          {message}
        </div>
      )}
      {status === 'error' && (
        <div className="flex items-center gap-2 text-red-400 text-sm">
          <XCircle size={14} />
          {message}
        </div>
      )}

      {/* PayPal Buttons */}
      {status !== 'success' && (
        <PayPalScriptProvider
          options={{
            clientId,
            currency: 'USD',
            intent: 'capture',
          }}
        >
          <PayPalButtons
            style={{ layout: 'vertical', color: 'blue', shape: 'rect', label: 'pay' }}
            createOrder={handleCreateOrder}
            onApprove={handleApprove}
            onCancel={() => { setStatus('idle'); onCancel(); }}
            onError={(err) => {
              setStatus('error');
              setMessage('PayPal encountered an error. Please try again.');
              onError('PayPal SDK error');
            }}
          />
        </PayPalScriptProvider>
      )}
    </div>
  );
};
