// API types matching backend Pydantic schemas

export type RecipientType = 'individual' | 'business' | 'unknown';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type PayPalStatus = 'NOT_INITIATED' | 'PENDING' | 'APPROVED' | 'CAPTURED' | 'CANCELLED' | 'FAILED';
export type SignalSeverity = 'low' | 'medium' | 'high' | 'critical';
export type SignalSource = 'rule_engine' | 'llm' | 'intent_check';

export interface AnalyzeRequest {
  amount: number;
  currency: string;
  recipient_name: string;
  recipient_type: RecipientType;
  purpose: string;
  message?: string;
  description?: string;
}

export interface RiskSignal {
  type: string;
  severity: SignalSeverity;
  title: string;
  explanation: string;
  score_contribution: number;
  source: SignalSource;
}

export interface AnalyzeResponse {
  transaction_id: string;
  risk_score: number;
  risk_level: RiskLevel;
  signals: RiskSignal[];
  intent_mismatch: boolean;
  intent_mismatch_explanation?: string;
  intent_summary?: string;
  recommendation: string;
  disclaimer: string;
  llm_used: boolean;
  llm_provider?: string;
  paypal_amount_usd?: number;
  currency_note?: string;
}

export interface CreateOrderRequest {
  transaction_id: string;
}

export interface CreateOrderResponse {
  order_id: string;
  approval_url: string;
  status: string;
  currency_note: string;
}

export interface CaptureOrderRequest {
  transaction_id: string;
  order_id: string;
}

export interface CaptureOrderResponse {
  order_id: string;
  capture_id: string;
  status: string;
  payer_name?: string;
  payer_email?: string;
  amount_usd?: number;
}

export interface TransactionSummary {
  id: string;
  created_at: string;
  amount: number;
  currency: string;
  recipient_name: string;
  purpose: string;
  risk_score: number;
  risk_level: RiskLevel;
  paypal_status: PayPalStatus;
  intent_mismatch: boolean;
}

export interface TransactionDetail {
  id: string;
  created_at: string;
  amount: number;
  currency: string;
  paypal_amount_usd?: number;
  recipient_name: string;
  recipient_type: string;
  purpose: string;
  message: string;
  description: string;
  risk_score: number;
  risk_level: RiskLevel;
  signals: RiskSignal[];
  intent_mismatch: boolean;
  intent_mismatch_explanation?: string;
  recommendation: string;
  disclaimer: string;
  llm_used: boolean;
  llm_provider?: string;
  paypal_order_id?: string;
  paypal_status: PayPalStatus;
  paypal_capture_id?: string;
}

export interface TransactionListResponse {
  transactions: TransactionSummary[];
  total: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  llm_available: boolean;
  llm_provider: string;
  paypal_configured: boolean;
  database: string;
}
