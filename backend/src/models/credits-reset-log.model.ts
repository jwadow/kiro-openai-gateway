import mongoose from 'mongoose';

export type ResetTrigger = 'auto' | 'admin' | 'login' | 'api';

export interface ICreditsResetLog {
  _id: mongoose.Types.ObjectId;
  username: string;           // User bị reset
  creditsBefore: number;      // Credits trước khi reset
  expiresAt: Date | null;     // Ngày hết hạn gốc
  resetAt: Date;              // Thời điểm reset
  resetBy: ResetTrigger;      // Nguồn trigger
  note?: string;              // Ghi chú (nếu admin reset manual)
}

const creditsResetLogSchema = new mongoose.Schema({
  username: { type: String, required: true, index: true },
  creditsBefore: { type: Number, required: true },
  expiresAt: { type: Date, default: null },
  resetAt: { type: Date, default: Date.now, index: true },
  resetBy: { type: String, enum: ['auto', 'admin', 'login', 'api'], required: true },
  note: { type: String, default: null },
});

// Compound index for querying by user with recent first
creditsResetLogSchema.index({ username: 1, resetAt: -1 });

export const CreditsResetLog = mongoose.model<ICreditsResetLog>(
  'CreditsResetLog',
  creditsResetLogSchema,
  'creditsResetLogs'
);
