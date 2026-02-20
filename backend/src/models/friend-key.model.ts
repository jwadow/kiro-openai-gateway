import mongoose from 'mongoose';
import crypto from 'crypto';

export interface IModelLimit {
  modelId: string;
  limitUsd: number;
  usedUsd: number;
  enabled: boolean;
}

export interface IFriendKey {
  _id: string;
  ownerId: string;
  isActive: boolean;
  createdAt: Date;
  rotatedAt?: Date;
  modelLimits: IModelLimit[];
  totalUsedUsd: number;
  requestsCount: number;
  lastUsedAt?: Date;
}

const modelLimitSchema = new mongoose.Schema({
  modelId: { type: String, required: true },
  limitUsd: { type: Number, required: true, default: 0 },
  usedUsd: { type: Number, default: 0 },
  enabled: { type: Boolean, default: true },
}, { _id: false });

const friendKeySchema = new mongoose.Schema({
  _id: { type: String, required: true },
  ownerId: { type: String, required: true, index: true },
  isActive: { type: Boolean, default: true },
  createdAt: { type: Date, default: Date.now },
  rotatedAt: { type: Date },
  modelLimits: { type: [modelLimitSchema], default: [] },
  totalUsedUsd: { type: Number, default: 0 },
  requestsCount: { type: Number, default: 0 },
  lastUsedAt: { type: Date },
});

friendKeySchema.index({ ownerId: 1 }, { unique: true });

export const FriendKey = mongoose.model<IFriendKey>('FriendKey', friendKeySchema, 'friend_keys');

export function generateFriendApiKey(): string {
  const randomBytes = crypto.randomBytes(32);
  const hexString = randomBytes.toString('hex');
  return `sk-trollllm-friend-${hexString}`;
}

export function maskFriendApiKey(key: string): string {
  if (!key || key.length < 25) return '****';
  return key.slice(0, 20) + '****' + key.slice(-4);
}

export function isFriendApiKey(key: string): boolean {
  return key.startsWith('sk-trollllm-friend-');
}
