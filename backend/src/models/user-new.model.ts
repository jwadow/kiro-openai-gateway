import mongoose from 'mongoose';
// Re-export helper functions from user.model.ts to avoid duplication
export {
  hashPassword,
  verifyPassword,
  generateApiKey,
  maskApiKey,
  generateReferralCode,
  maskUsername,
  CreditPackage,
  CREDIT_PACKAGES,
} from './user.model.js';

export interface IUserNew {
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
  credits: number;           // OhMyGPT credits remaining (port 8005, USD)
  creditsUsed: number;       // OhMyGPT tokens used (lifetime, USD)
  creditsNew: number;        // OpenHands credits remaining (port 8004, USD)
  creditsNewUsed: number;    // OpenHands USD cost used (lifetime, USD)
  tokensUserNew: number;     // OpenHands tokens count (lifetime, for analytics)
  totalInputTokens: number;  // Input tokens used (for analytics)
  totalOutputTokens: number; // Output tokens used (for analytics)
  purchasedAt?: Date | null; // When credits (OhMyGPT) were purchased
  expiresAt?: Date | null;   // When credits (OhMyGPT) expire (7 days from purchase)
  purchasedAtNew?: Date | null; // When creditsNew (OpenHands) were purchased
  expiresAtNew?: Date | null;   // When creditsNew (OpenHands) expire (7 days from purchase)
  // Referral fields
  referralCode: string;
  referredBy?: string | null;
  refCredits: number;        // Referral credits (bonus, USD)
  referralBonusAwarded: boolean;
  // Discord integration
  discordId?: string;        // Discord User ID (17-19 digits)
  // Migration status for rate transition (1000 -> 2500 VNĐ/$)
  migration: boolean;        // true = on new rate, false = needs migration (existing users)
}

const userNewSchema = new mongoose.Schema({
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
  credits: { type: Number, default: 0 },           // OhMyGPT (port 8005)
  creditsUsed: { type: Number, default: 0 },       // OhMyGPT tokens used
  creditsNew: { type: Number, default: 0 },        // OpenHands (port 8004)
  creditsNewUsed: { type: Number, default: 0 },    // OpenHands USD cost used
  tokensUserNew: { type: Number, default: 0 },     // OpenHands tokens count (analytics)
  totalInputTokens: { type: Number, default: 0 },
  totalOutputTokens: { type: Number, default: 0 },
  purchasedAt: { type: Date, default: null },      // OhMyGPT credits
  expiresAt: { type: Date, default: null },        // OhMyGPT credits
  purchasedAtNew: { type: Date, default: null },   // OpenHands credits
  expiresAtNew: { type: Date, default: null },     // OpenHands credits
  // Referral fields
  referralCode: { type: String, unique: true, sparse: true },
  referredBy: { type: String, default: null },
  refCredits: { type: Number, default: 0 },
  referralBonusAwarded: { type: Boolean, default: false },
  // Discord integration
  discordId: { type: String, default: null },
  // Migration status for rate transition (1000 -> 2500 VNĐ/$)
  // New users default to true (on new rate), existing users who need migration have false
  migration: { type: Boolean, default: true },
});

export const UserNew = mongoose.model<IUserNew>('UserNew', userNewSchema, 'usersNew');
