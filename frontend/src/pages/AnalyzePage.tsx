import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Loader2, Send, Info, ChevronDown } from 'lucide-react';
import { analyzePayment } from '../services/api';
import type { AnalyzeRequest, AnalyzeResponse } from '../types/api';

const CURRENCIES = ['INR', 'USD', 'EUR', 'GBP', 'SGD', 'AED'];
const RECIPIENT_TYPES = [
  { value: 'individual', label: 'Individual Person' },
  { value: 'business', label: 'Business / Company' },
  { value: 'unknown', label: 'Not sure' },
];

const EXAMPLE_SCAM = {
  amount: 40000,
  currency: 'INR',
  recipient_name: 'John Kumar',
  recipient_type: 'individual' as const,
  purpose: 'Buying a second-hand laptop',
  message: "Send the money immediately. Do not mention the laptop in the payment description. Use personal payment. If you don't pay within 10 minutes I will sell it to someone else.",
  description: 'Personal transfer',
};

interface FieldProps {
  label: string;
  hint?: string;
  required?: boolean;
  children: React.ReactNode;
}

const Field: React.FC<FieldProps> = ({ label, hint, required, children }) => (
  <div>
    <label className="block text-sm font-medium text-slate-300 mb-1.5">
      {label}
      {required && <span className="text-red-400 ml-1">*</span>}
    </label>
    {children}
    {hint && <p className="text-xs text-slate-500 mt-1">{hint}</p>}
  </div>
);

const inputClass =
  'w-full px-4 py-2.5 rounded-xl text-sm text-slate-100 bg-slate-800/60 border border-slate-700/60 ' +
  'focus:outline-none focus:border-blue-500/60 focus:ring-1 focus:ring-blue-500/30 ' +
  'placeholder:text-slate-600 transition-all';

export const AnalyzePage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [form, setForm] = useState<AnalyzeRequest>({
    amount: 0,
    currency: 'INR',
    recipient_name: '',
    recipient_type: 'unknown',
    purpose: '',
    message: '',
    description: '',
  });

  const setField = (field: keyof AnalyzeRequest, value: string | number) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const loadExample = () => setForm(EXAMPLE_SCAM);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.amount <= 0) { setError('Please enter a valid amount.'); return; }
    if (!form.recipient_name.trim()) { setError('Please enter the recipient name.'); return; }
    if (!form.purpose.trim()) { setError('Please enter the payment purpose.'); return; }

    setLoading(true);
    setError('');
    try {
      const result: AnalyzeResponse = await analyzePayment(form);
      // Navigate to results page, passing data via state
      navigate('/result', { state: { result, request: form } });
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Analysis failed. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-100 mb-2">Analyze a Payment</h1>
          <p className="text-slate-400">
            Enter the payment details to receive an AI-powered risk assessment.
          </p>
        </div>

        {/* Load example button */}
        <div className="mb-6">
          <button
            onClick={loadExample}
            type="button"
            className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1.5 transition-colors"
          >
            <Info size={14} />
            Load example scam scenario
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Amount + Currency row */}
          <div className="grid grid-cols-2 gap-4">
            <Field label="Amount" required>
              <input
                id="amount"
                type="number"
                min="0"
                step="any"
                placeholder="40000"
                value={form.amount || ''}
                onChange={e => setField('amount', parseFloat(e.target.value) || 0)}
                className={inputClass}
              />
            </Field>
            <Field label="Currency">
              <div className="relative">
                <select
                  id="currency"
                  value={form.currency}
                  onChange={e => setField('currency', e.target.value)}
                  className={`${inputClass} appearance-none pr-10`}
                >
                  {CURRENCIES.map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
                <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
              </div>
            </Field>
          </div>

          {/* Recipient name + type */}
          <div className="grid grid-cols-2 gap-4">
            <Field label="Recipient Name" required>
              <input
                id="recipient-name"
                type="text"
                placeholder="John Kumar"
                value={form.recipient_name}
                onChange={e => setField('recipient_name', e.target.value)}
                className={inputClass}
              />
            </Field>
            <Field label="Recipient Type">
              <div className="relative">
                <select
                  id="recipient-type"
                  value={form.recipient_type}
                  onChange={e => setField('recipient_type', e.target.value as any)}
                  className={`${inputClass} appearance-none pr-10`}
                >
                  {RECIPIENT_TYPES.map(rt => (
                    <option key={rt.value} value={rt.value}>{rt.label}</option>
                  ))}
                </select>
                <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
              </div>
            </Field>
          </div>

          {/* Purpose */}
          <Field
            label="Payment Purpose"
            required
            hint="What is this payment for? Be specific."
          >
            <input
              id="purpose"
              type="text"
              placeholder="Buying a second-hand laptop"
              value={form.purpose}
              onChange={e => setField('purpose', e.target.value)}
              className={inputClass}
            />
          </Field>

          {/* Payment description */}
          <Field
            label="Payment Description / Reference"
            hint="The note or description that will appear on the payment."
          >
            <input
              id="description"
              type="text"
              placeholder="Personal transfer"
              value={form.description}
              onChange={e => setField('description', e.target.value)}
              className={inputClass}
            />
          </Field>

          {/* Message from seller */}
          <Field
            label="Message / Conversation from Seller"
            hint="Paste any message, chat, or instructions you received. The more context, the better."
          >
            <textarea
              id="seller-message"
              rows={5}
              placeholder="Send the money immediately. Do not mention the laptop..."
              value={form.message}
              onChange={e => setField('message', e.target.value)}
              className={`${inputClass} resize-none`}
            />
          </Field>

          {/* Error */}
          {error && (
            <div className="text-sm text-red-400 bg-red-400/10 border border-red-400/30 rounded-xl px-4 py-3">
              {error}
            </div>
          )}

          {/* Submit */}
          <motion.button
            type="submit"
            disabled={loading}
            whileHover={{ scale: loading ? 1 : 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full flex items-center justify-center gap-3 py-3.5 rounded-xl font-semibold text-white transition-all disabled:opacity-60"
            style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)' }}
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Analyzing payment...
              </>
            ) : (
              <>
                <Send size={18} />
                Analyze Payment
              </>
            )}
          </motion.button>
        </form>
      </motion.div>
    </div>
  );
};
