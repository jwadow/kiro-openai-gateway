import mongoose from 'mongoose';

export interface IErrorLog {
  _id?: mongoose.Types.ObjectId;
  source: 'backend' | 'goproxy';
  method: string;
  path: string;
  endpoint: string;
  userId?: string;
  userKeyId?: string;
  clientIp: string;
  userAgent?: string;
  statusCode: number;
  errorType: string;
  errorMessage: string;
  errorDetails?: any;
  requestHeaders?: Record<string, string>;
  requestBody?: any;
  responseBody?: any;
  latencyMs?: number;
  stackTrace?: string;
  createdAt: Date;
}

const errorLogSchema = new mongoose.Schema({
  source: { type: String, required: true, enum: ['backend', 'goproxy'] },
  method: { type: String, required: true },
  path: { type: String, required: true },
  endpoint: { type: String },
  userId: { type: String, index: true },
  userKeyId: { type: String },
  clientIp: { type: String, required: true },
  userAgent: { type: String },
  statusCode: { type: Number, required: true },
  errorType: { type: String, required: true },
  errorMessage: { type: String, required: true },
  errorDetails: { type: mongoose.Schema.Types.Mixed },
  requestHeaders: { type: mongoose.Schema.Types.Mixed },
  requestBody: { type: mongoose.Schema.Types.Mixed },
  responseBody: { type: mongoose.Schema.Types.Mixed },
  latencyMs: { type: Number },
  stackTrace: { type: String },
  createdAt: { type: Date, default: Date.now, expires: 2592000 }, // 30 days TTL
});

// Compound indexes for common queries
errorLogSchema.index({ source: 1, createdAt: -1 });
errorLogSchema.index({ path: 1, createdAt: -1 });

export const ErrorLog = mongoose.model<IErrorLog>('ErrorLog', errorLogSchema, 'error_logs');
