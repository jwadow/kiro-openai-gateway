import mongoose from "mongoose";

// Credit amount: any integer from 16 to 100 USD
export type PaymentStatus = "pending" | "success" | "failed" | "expired";
export type PaymentMethod = "sepay";

// Constants for credit purchases
export const MIN_CREDITS = 20;
export const MAX_CREDITS = 100;
export const VND_RATE = 2500; // 2500 VND = $1 (legacy reference, not used for new purchases)
export const VND_RATE_NEW = 1500; // 1500 VND = $1 (current rate for new purchases)
export const VALIDITY_DAYS = 7;

// Profit calculation constants
// Selling price: 2500 VND per $1, Profit: 740 VND per $1
export const PROFIT_VND_PER_USD = 740; // Profit per $1 credits sold
export const PROFIT_CUTOFF_DATE = "2026-01-06T20:49:00+07:00"; // Vietnam timezone (UTC+7)

export interface IPayment {
	_id: mongoose.Types.ObjectId;
	userId: string;
	discordId?: string;
	username?: string;
	credits: number;
	amount: number;
	currency: "VND";
	orderCode?: string;
	paymentMethod: PaymentMethod;
	status: PaymentStatus;
	sepayTransactionId?: string;
	creditsBefore?: number;
	creditsAfter?: number;
	createdAt: Date;
	expiresAt: Date;
	completedAt?: Date;
}

// Helper to calculate referral bonus (50% of credits, minimum $5)
export function calculateRefBonus(credits: number): number {
	return Math.max(5, Math.floor(credits * 0.5));
}

const paymentSchema = new mongoose.Schema({
	userId: { type: String, required: true, index: true },
	discordId: { type: String },
	username: { type: String },
	credits: { type: Number, required: true, min: MIN_CREDITS, max: MAX_CREDITS },
	amount: { type: Number, required: true },
	currency: { type: String, enum: ["VND"], default: "VND" },
	orderCode: { type: String, sparse: true, index: true },
	paymentMethod: { type: String, enum: ["sepay"], default: "sepay" },
	status: {
		type: String,
		enum: ["pending", "success", "failed", "expired"],
		default: "pending",
	},
	sepayTransactionId: { type: String },
	creditsBefore: { type: Number },
	creditsAfter: { type: Number },
	createdAt: { type: Date, default: Date.now },
	expiresAt: { type: Date, required: true },
	completedAt: { type: Date },
});

paymentSchema.index({ status: 1, expiresAt: 1 });

export const Payment = mongoose.model<IPayment>(
	"Payment",
	paymentSchema,
	"payments",
);

export function generateOrderCode(credits: number): string {
	const timestamp = Date.now();
	const random = Math.random().toString(36).substring(2, 6).toUpperCase();
	return `TROLL${credits}D${timestamp}${random}`;
}

export function generateQRCodeUrl(
	orderCode: string,
	amount: number,
	username?: string,
): string {
	const account = process.env.SEPAY_ACCOUNT || "VQRQAFRBD3142";
	const bank = process.env.SEPAY_BANK || "MBBank";
	const description = username ? `${orderCode} ${username}` : orderCode;
	return `https://qr.sepay.vn/img?acc=${account}&bank=${bank}&amount=${amount}&des=${encodeURIComponent(description)}`;
}
