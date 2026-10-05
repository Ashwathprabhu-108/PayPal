import axios from 'axios';
import type {
  AnalyzeRequest,
  AnalyzeResponse,
  CreateOrderRequest,
  CreateOrderResponse,
  CaptureOrderRequest,
  CaptureOrderResponse,
  TransactionListResponse,
  TransactionDetail,
  HealthResponse,
} from '../types/api';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Analysis ─────────────────────────────────────────────────
export const analyzePayment = async (request: AnalyzeRequest): Promise<AnalyzeResponse> => {
  const { data } = await api.post<AnalyzeResponse>('/api/analyze', request);
  return data;
};

// ── PayPal ───────────────────────────────────────────────────
export const createPayPalOrder = async (request: CreateOrderRequest): Promise<CreateOrderResponse> => {
  const { data } = await api.post<CreateOrderResponse>('/api/paypal/create-order', request);
  return data;
};

export const capturePayPalOrder = async (request: CaptureOrderRequest): Promise<CaptureOrderResponse> => {
  const { data } = await api.post<CaptureOrderResponse>('/api/paypal/capture-order', request);
  return data;
};

// ── Transactions ──────────────────────────────────────────────
export const listTransactions = async (limit = 20, offset = 0): Promise<TransactionListResponse> => {
  const { data } = await api.get<TransactionListResponse>('/api/transactions', {
    params: { limit, offset },
  });
  return data;
};

export const getTransaction = async (id: string): Promise<TransactionDetail> => {
  const { data } = await api.get<TransactionDetail>(`/api/transactions/${id}`);
  return data;
};

// ── Health ────────────────────────────────────────────────────
export const getHealth = async (): Promise<HealthResponse> => {
  const { data } = await api.get<HealthResponse>('/api/health');
  return data;
};

export default api;
