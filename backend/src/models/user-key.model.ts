import mongoose from 'mongoose';

export interface IUserKey {
  _id: string;
  name: string;
  // Note: tier is soft-deprecated as part of tier system removal (Story 3.2)
  // Field kept for backward compatibility but ignored in all business logic
  tier?: 'dev' | 'pro';
  tokensUsed: number;
  requestsCount: number;
  isActive: boolean;
  createdAt: Date;
  lastUsedAt?: Date;
  notes?: string;
  planExpiresAt?: Date | null;
}

const userKeySchema = new mongoose.Schema({
  _id: { type: String, required: true },
  name: { type: String, required: true },
  // Note: tier is soft-deprecated - kept in schema for backward compatibility
  // All User Keys now get 600 RPM regardless of tier value (Epic 1)
  tier: { type: String, enum: ['dev', 'pro'], default: 'dev' },
  tokensUsed: { type: Number, default: 0 },
  requestsCount: { type: Number, default: 0 },
  isActive: { type: Boolean, default: true },
  createdAt: { type: Date, default: Date.now },
  lastUsedAt: { type: Date },
  notes: { type: String },
  planExpiresAt: { type: Date, default: null },
});

userKeySchema.set('toJSON', { virtuals: true });
userKeySchema.set('toObject', { virtuals: true });

export const UserKey = mongoose.model<IUserKey>('UserKey', userKeySchema, 'user_keys');
