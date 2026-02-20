import { paymentRepository } from '../repositories/payment.repository.js';
import { userRepository } from '../repositories/user.repository.js';
import {
  IPayment,
  MIN_CREDITS,
  MAX_CREDITS,
  VND_RATE_NEW,
  VALIDITY_DAYS,
  calculateRefBonus,
  generateOrderCode,
  generateQRCodeUrl,
} from '../models/payment.model.js';
import { UserKey } from '../models/user-key.model.js';
import { expirationSchedulerService } from './expiration-scheduler.service.js';

// ============================================================
// PROMO CONFIGURATION - ENABLED
// ============================================================
const PROMO_CONFIG = {
  startDate: new Date('2026-01-01T00:00:00+07:00'),
  endDate: new Date('2026-01-03T00:00:00+07:00'),
  bonusPercent: 20,
};

function isPromoActive(): boolean {
  const now = new Date();
  return now >= PROMO_CONFIG.startDate && now < PROMO_CONFIG.endDate;
}

function calculateCreditsWithBonus(credits: number): number {
  if (isPromoActive()) {
    return credits * (1 + PROMO_CONFIG.bonusPercent / 100);
  }
  return credits;
}
// ============================================================

export interface CheckoutResult {
  paymentId: string;
  orderCode: string;
  qrCodeUrl: string;
  amount: number;
  credits: number;
  expiresAt: Date;
}

interface DiscordWebhookPayload {
  discordId: string;
  credits: string;
  username: string;
  orderCode: string;
  amount: number;
  transactionId: string;
}

export interface PaymentStatusResult {
  status: string;
  remainingSeconds: number;
  credits?: number;
  completedAt?: Date;
}

export interface SepayWebhookPayload {
  id: number;
  gateway: string;
  transactionDate: string;
  accountNumber: string;
  code: string | null;
  content: string;
  transferType: 'in' | 'out';
  transferAmount: number;
  accumulated: number;
  subAccount: string | null;
  referenceCode: string;
  description: string;
}

function extractOrderCode(text: string): string | null {
  // Try to find TROLL{amount}D pattern in the text (amount can be 20-100)
  const match = text.match(/TROLL(\d+)D\d+[A-Z0-9]+/i);
  return match ? match[0].toUpperCase() : null;
}

export class PaymentService {
  async createCheckout(userId: string, credits: number, discordId?: string, username?: string): Promise<CheckoutResult> {
    // Validate credits amount
    if (!Number.isInteger(credits) || credits < MIN_CREDITS || credits > MAX_CREDITS) {
      throw new Error(`Invalid amount. Must be between $${MIN_CREDITS} and $${MAX_CREDITS}`);
    }

    // Validate Discord ID format (should be 17-19 digit number)
    if (discordId && !/^\d{17,19}$/.test(discordId)) {
      throw new Error('Invalid Discord ID format. Please enter your Discord User ID (17-19 digits)');
    }

    const amount = credits * VND_RATE_NEW;
    const orderCode = generateOrderCode(credits);
    const expiresAt = new Date(Date.now() + 15 * 60 * 1000); // 15 minutes

    const payment = await paymentRepository.create({
      userId,
      discordId,
      username,
      credits,
      amount,
    });

    const qrCodeUrl = generateQRCodeUrl(payment.orderCode!, amount, username);

    return {
      paymentId: payment._id.toString(),
      orderCode: payment.orderCode!,
      qrCodeUrl,
      amount,
      credits,
      expiresAt: payment.expiresAt,
    };
  }

  async getPaymentStatus(paymentId: string, userId: string): Promise<PaymentStatusResult | null> {
    const payment = await paymentRepository.checkAndExpire(paymentId);
    if (!payment || payment.userId !== userId) {
      return null;
    }

    const now = new Date();
    const remainingMs = payment.expiresAt.getTime() - now.getTime();
    const remainingSeconds = Math.max(0, Math.floor(remainingMs / 1000));

    return {
      status: payment.status,
      remainingSeconds,
      credits: payment.status === 'success' ? payment.credits : undefined,
      completedAt: payment.completedAt,
    };
  }

  async processWebhook(payload: SepayWebhookPayload): Promise<{ processed: boolean; message: string }> {
    console.log('[Payment Webhook] Processing:', JSON.stringify(payload));

    // Validate transfer type
    if (payload.transferType !== 'in') {
      return { processed: false, message: 'Ignored: not incoming transfer' };
    }

    // Validate subAccount (virtual account identifier)
    const expectedAccount = process.env.SEPAY_ACCOUNT || 'VQRQAFRBD3142';
    if (payload.subAccount !== expectedAccount) {
      console.log(`[Payment Webhook] Account check: subAccount=${payload.subAccount}, expected=${expectedAccount}`);
      return { processed: false, message: 'Ignored: account mismatch' };
    }

    // Extract order code from content or description
    const content = payload.content || '';
    const description = payload.description || '';

    let orderCode = extractOrderCode(content);
    if (!orderCode) {
      orderCode = extractOrderCode(description);
    }

    if (!orderCode) {
      console.log(`[Payment Webhook] Unmatched content: ${content}`);
      console.log(`[Payment Webhook] Unmatched description: ${description}`);
      return { processed: false, message: 'No matching order code found' };
    }

    console.log(`[Payment Webhook] Found orderCode: ${orderCode}`);
    const payment = await paymentRepository.findByOrderCode(orderCode);

    if (!payment) {
      console.log(`[Payment Webhook] Order code not found in DB: ${orderCode}`);
      return { processed: false, message: 'Payment not found' };
    }

    console.log(`[Payment Webhook] Payment found: userId=${payment.userId}, status=${payment.status}, amount=${payment.amount}`);

    // Check if already processed
    if (payment.status === 'success') {
      console.log(`[Payment Webhook] Already processed: ${orderCode}`);
      return { processed: false, message: 'Already processed' };
    }

    // Check if expired
    if (payment.status === 'expired') {
      console.log(`[Payment Webhook] Payment expired: ${orderCode}`);
      return { processed: false, message: 'Payment expired' };
    }

    // Validate amount
    if (payload.transferAmount !== payment.amount) {
      console.log(`[Payment Webhook] Amount mismatch: expected ${payment.amount}, got ${payload.transferAmount}`);
      return { processed: false, message: 'Amount mismatch - logged for review' };
    }

    console.log(`[Payment Webhook] Updating payment status to success...`);

    // Process successful payment
    await paymentRepository.updateStatus(
      payment._id.toString(),
      'success',
      payload.id.toString()
    );

    // Credits = base amount + promo bonus (if active)
    const finalCredits = calculateCreditsWithBonus(payment.credits);

    console.log(`[Payment Webhook] Calling addCredits for ${payment.userId}...`);

    // Add credits to user
    await this.addCredits(payment.userId, finalCredits, payment.discordId, payment._id.toString());

    // Send webhook to Discord bot
    await this.notifyDiscordBot({
      discordId: payment.discordId || '',
      credits: `$${finalCredits}`,
      username: payment.userId,
      orderCode: payment.orderCode || orderCode,
      amount: payment.amount,
      transactionId: payload.id.toString(),
    });

    console.log(`[Payment Webhook] Success: ${orderCode} - User: ${payment.userId} - Credits: $${finalCredits}`);
    return { processed: true, message: 'Payment processed successfully' };
  }

  private async notifyDiscordBot(payload: DiscordWebhookPayload): Promise<void> {
    const webhookUrl = process.env.DISCORD_BOT_WEBHOOK_URL;
    const webhookSecret = process.env.DISCORD_BOT_WEBHOOK_SECRET;

    if (!webhookUrl) {
      console.log('[Discord Webhook] DISCORD_BOT_WEBHOOK_URL not configured, skipping');
      return;
    }

    try {
      const response = await fetch(webhookUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Api-Key': webhookSecret || '',
        },
        body: JSON.stringify(payload),
      });

      const result = await response.json() as { success?: boolean; error?: string };

      if (response.ok && result.success) {
        console.log(`[Discord Webhook] Role assigned for ${payload.discordId}: ${payload.credits}`);
      } else {
        console.error(`[Discord Webhook] Failed: ${result.error || response.statusText}`);
      }
    } catch (error) {
      console.error('[Discord Webhook] Error:', error);
    }
  }

  private async addCredits(userId: string, credits: number, discordId?: string, paymentId?: string): Promise<void> {
    console.log(`[Payment] Adding $${credits} creditsNew to user: ${userId}`);

    const user = await userRepository.getFullUser(userId);
    if (!user) {
      console.log(`[Payment] User not found: ${userId}`);
      throw new Error('User not found');
    }

    // Get current creditsNew before adding (for OpenHands system)
    const creditsBefore = user.creditsNew || 0;
    const creditsAfter = creditsBefore + credits;
    console.log(`[Payment] CreditsNew: before=${creditsBefore}, after=${creditsAfter}`);

    const now = new Date();

    // Always set expiration to 7 days from now (no stacking)
    const expiresAtNew = new Date(now.getTime() + VALIDITY_DAYS * 24 * 60 * 60 * 1000);
    console.log(`[Payment] Setting expiresAtNew to ${VALIDITY_DAYS} days from now: ${expiresAtNew}`);

    // Build update object for creditsNew (OpenHands system)
    const updateData: Record<string, unknown> = {
      purchasedAtNew: now,
      expiresAtNew,
      $inc: { creditsNew: credits },
    };

    // Only update discordId if provided (don't overwrite existing with empty value)
    if (discordId) {
      updateData.discordId = discordId;
      console.log(`[Payment] Saving discordId: ${discordId}`);
    }

    // Update user with new creditsNew - use UserNew model (usersNew collection)
    const { UserNew } = await import('../models/user-new.model.js');
    await UserNew.findByIdAndUpdate(userId, updateData);

    // Update payment record with creditsBefore and creditsAfter
    if (paymentId) {
      const { Payment } = await import('../models/payment.model.js');
      await Payment.findByIdAndUpdate(paymentId, {
        creditsBefore,
        creditsAfter,
      });
      console.log(`[Payment] Updated payment ${paymentId} with creditsBefore=${creditsBefore}, creditsAfter=${creditsAfter}`);
    }

    // Referral system disabled
    // await this.awardReferralBonus(userId, credits);

    // Sync to user_keys collection for GoProxy (use expiresAtNew)
    if (user.apiKey) {
      const existingKey = await UserKey.findById(user.apiKey);
      if (!existingKey) {
        // Create new user_key entry
        await UserKey.create({
          _id: user.apiKey,
          name: userId,
          tier: 'pro',
          tokensUsed: user.creditsNewUsed || 0,
          requestsCount: 0,
          isActive: true,
          createdAt: now,
          expiresAt: expiresAtNew,
        });
      } else {
        // Update existing user_key
        await UserKey.updateOne(
          { _id: user.apiKey },
          { expiresAt: expiresAtNew }
        );
      }
    }

    console.log(`[Payment] ✅ Added $${credits} creditsNew to ${userId}, expires: ${expiresAtNew}`);

    // Schedule expiration timer for creditsNew
    expirationSchedulerService.scheduleExpirationNew(userId, expiresAtNew);
  }

  private async awardReferralBonus(userId: string, credits: number): Promise<void> {
    console.log(`[Referral] Checking referral bonus for user: ${userId}`);

    const user = await userRepository.getFullUser(userId);
    if (!user) {
      console.log(`[Referral] User not found: ${userId}`);
      return;
    }

    console.log(`[Referral] User ${userId}: referredBy=${user.referredBy}, referralBonusAwarded=${user.referralBonusAwarded}`);

    // Check if user was referred and hasn't received bonus yet
    if (!user.referredBy) {
      console.log(`[Referral] User ${userId} was not referred by anyone`);
      return;
    }

    if (user.referralBonusAwarded) {
      console.log(`[Referral] User ${userId} already received referral bonus`);
      return;
    }

    // Calculate bonus credits (50% of credits, min $5)
    const bonusCredits = calculateRefBonus(credits);

    // Award refCredits to the referred user (new user)
    await userRepository.addRefCredits(userId, bonusCredits);
    await userRepository.markReferralBonusAwarded(userId);

    // Award refCredits to the referrer
    await userRepository.addRefCredits(user.referredBy, bonusCredits);

    console.log(`[Referral] ✅ Awarded $${bonusCredits} refCredits to ${userId} and ${user.referredBy} for $${credits} purchase`);
  }

  async getPaymentHistory(userId: string): Promise<IPayment[]> {
    return paymentRepository.findByUserId(userId);
  }

  async getUserPaymentStats(userId: string) {
    return paymentRepository.getUserPaymentStats(userId);
  }

  async getPaymentHistoryPaginated(
    userId: string,
    options: {
      page?: number;
      limit?: number;
      status?: string;
      from?: string;
      to?: string;
    }
  ) {
    const parsedOptions: {
      page?: number;
      limit?: number;
      status?: 'pending' | 'success' | 'failed' | 'expired';
      from?: Date;
      to?: Date;
    } = {
      page: options.page || 1,
      limit: options.limit || 20,
    };

    if (options.status && ['pending', 'success', 'failed', 'expired'].includes(options.status)) {
      parsedOptions.status = options.status as 'pending' | 'success' | 'failed' | 'expired';
    }
    if (options.from) {
      parsedOptions.from = new Date(options.from);
    }
    if (options.to) {
      parsedOptions.to = new Date(options.to);
    }

    return paymentRepository.findByUserIdPaginated(userId, parsedOptions);
  }
}

export const paymentService = new PaymentService();
