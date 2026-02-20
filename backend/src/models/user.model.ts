import mongoose from 'mongoose';
import crypto from 'crypto';

// Credit packages: $20 or $40 USD
export type CreditPackage = '20' | '40';

export const CREDIT_PACKAGES: Record<CreditPackage, { credits: number; price: number; days: number; refBonus: number }> = {
  '20': { credits: 20, price: 20000, days: 7, refBonus: 10 },
  '40': { credits: 40, price: 40000, days: 7, refBonus: 20 },
};

export interface IUser {
  _id: string;
  passwordHash: string;
  passwordSalt: string;
  role: 'admin' | 'user';
  isActive: boolean;
  createdAt: Date;
  lastLoginAt?: Date;
  apiKey: string;
  apiKeyCreatedAt: Date;
  // Credits-based billing (USD)
  credits: number;           // Credits remaining (USD)
  creditsUsed: number;       // Credits used (lifetime, USD)
  totalInputTokens: number;  // Input tokens used (for analytics)
  totalOutputTokens: number; // Output tokens used (for analytics)
  purchasedAt?: Date | null; // When credits were purchased
  expiresAt?: Date | null;   // When credits expire (7 days from purchase)
  // Referral fields
  referralCode: string;
  referredBy?: string | null;
  refCredits: number;        // Referral credits (bonus, USD)
  referralBonusAwarded: boolean;
}

const userSchema = new mongoose.Schema({
  _id: { type: String, required: true },
  passwordHash: { type: String, required: true },
  passwordSalt: { type: String, required: true },
  role: { type: String, enum: ['admin', 'user'], default: 'user' },
  isActive: { type: Boolean, default: true },
  createdAt: { type: Date, default: Date.now },
  lastLoginAt: { type: Date },
  apiKey: { type: String, unique: true, sparse: true },
  apiKeyCreatedAt: { type: Date },
  // Credits-based billing (USD)
  credits: { type: Number, default: 0 },
  creditsUsed: { type: Number, default: 0 },
  totalInputTokens: { type: Number, default: 0 },
  totalOutputTokens: { type: Number, default: 0 },
  purchasedAt: { type: Date, default: null },
  expiresAt: { type: Date, default: null },
  // Referral fields
  referralCode: { type: String, unique: true, sparse: true },
  referredBy: { type: String, default: null },
  refCredits: { type: Number, default: 0 },
  referralBonusAwarded: { type: Boolean, default: false },
});

export const User = mongoose.model<IUser>('User', userSchema, 'users');

export function hashPassword(password: string, salt?: string): { hash: string; salt: string } {
  const useSalt = salt || crypto.randomBytes(16).toString('hex');
  const hash = crypto.pbkdf2Sync(password, useSalt, 1000, 64, 'sha512').toString('hex');
  return { hash, salt: useSalt };
}

export function verifyPassword(password: string, hash: string, salt: string): boolean {
  const result = hashPassword(password, salt);
  return result.hash === hash;
}

export function generateApiKey(): string {
  const randomBytes = crypto.randomBytes(32);
  const hexString = randomBytes.toString('hex');
  return `sk-trollllm-${hexString}`;
}

export function maskApiKey(key: string): string {
  if (!key || key.length < 20) return '****';
  return key.slice(0, 15) + '****' + key.slice(-4);
}

export function generateReferralCode(): string {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
  let code = '';
  for (let i = 0; i < 8; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return code;
}

export function maskUsername(username: string): string {
  if (!username || username.length < 4) return '***';
  const start = username.slice(0, 3);
  const end = username.slice(-3);
  return `${start}***${end}`;
}
