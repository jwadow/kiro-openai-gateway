import { userNewRepository, isCreditsExpired } from '../repositories/user-new.repository.js';
import { maskApiKey, IUserNew } from '../models/user-new.model.js';
import { expirationSchedulerService } from './expiration-scheduler.service.js';
import { ResetTrigger } from '../models/credits-reset-log.model.js';

export interface UserNewProfile {
  username: string;
  apiKey: string;
  apiKeyCreatedAt: Date;
  creditsUsed: number;
  credits: number;
  refCredits: number;
  role: string;
  totalInputTokens: number;
  totalOutputTokens: number;
  purchasedAt: Date | null;
  expiresAt: Date | null;
}

export interface BillingInfoNew {
  creditsUsed: number;
  credits: number;
  refCredits: number;
  purchasedAt: Date | null;
  expiresAt: Date | null;
  daysUntilExpiration: number | null;
  isExpiringSoon: boolean;
}

export class UserNewService {
  async getProfile(username: string): Promise<UserNewProfile | null> {
    const user = await userNewRepository.getFullUser(username);
    if (!user) return null;

    return {
      username: user._id,
      apiKey: maskApiKey(user.apiKey),
      apiKeyCreatedAt: user.apiKeyCreatedAt,
      creditsUsed: user.creditsUsed,
      credits: user.credits || 0,
      refCredits: user.refCredits || 0,
      role: user.role,
      totalInputTokens: (user as any).totalInputTokens || 0,
      totalOutputTokens: (user as any).totalOutputTokens || 0,
      purchasedAt: user.purchasedAt || null,
      expiresAt: user.expiresAt || null,
    };
  }

  async getFullApiKey(username: string): Promise<string | null> {
    const user = await userNewRepository.getFullUser(username);
    return user?.apiKey || null;
  }

  async rotateApiKey(username: string): Promise<{ newApiKey: string; createdAt: Date }> {
    const newApiKey = await userNewRepository.rotateApiKey(username);
    return {
      newApiKey,
      createdAt: new Date(),
    };
  }

  async getBillingInfo(username: string): Promise<BillingInfoNew | null> {
    const user = await userNewRepository.getFullUser(username);
    if (!user) return null;

    let daysUntilExpiration: number | null = null;
    let isExpiringSoon = false;

    if (user.expiresAt && (user.credits > 0 || user.refCredits > 0)) {
      const now = new Date();
      const expiresAt = new Date(user.expiresAt);
      const diffTime = expiresAt.getTime() - now.getTime();
      daysUntilExpiration = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      isExpiringSoon = daysUntilExpiration <= 3 && daysUntilExpiration > 0;
    }

    return {
      creditsUsed: user.creditsUsed,
      credits: user.credits || 0,
      refCredits: user.refCredits || 0,
      purchasedAt: user.purchasedAt || null,
      expiresAt: user.expiresAt || null,
      daysUntilExpiration,
      isExpiringSoon,
    };
  }

  async findByApiKey(apiKey: string): Promise<IUserNew | null> {
    return userNewRepository.findByApiKey(apiKey);
  }

  async checkAndResetExpiredCredits(username: string, triggeredBy: ResetTrigger = 'login'): Promise<{ wasExpired: boolean; user: IUserNew | null }> {
    const user = await userNewRepository.findById(username);
    if (!user) return { wasExpired: false, user: null };

    if (isCreditsExpired(user) && user.credits > 0) {
      // Use scheduler service to reset and log
      await expirationSchedulerService.resetAndLog(username, triggeredBy);
      const updatedUser = await userNewRepository.findById(username);
      return { wasExpired: true, user: updatedUser };
    }

    return { wasExpired: false, user };
  }

  isCreditsExpired(user: IUserNew): boolean {
    return isCreditsExpired(user);
  }
}

export const userNewService = new UserNewService();
