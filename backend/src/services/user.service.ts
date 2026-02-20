import { userRepository, isCreditsExpired } from '../repositories/user.repository.js';
import { maskApiKey, IUserNew } from '../models/user-new.model.js';
import { migrationService } from './migration.service.js';

// Alias for backward compatibility
type IUser = IUserNew;

export interface UserProfile {
  username: string;
  apiKey: string;
  apiKeyCreatedAt: Date;
  creditsUsed: number;
  credits: number;
  creditsNew: number;
  creditsNewUsed: number;
  tokensUserNew: number;
  refCredits: number;
  role: string;
  totalInputTokens: number;
  totalOutputTokens: number;
  purchasedAt: Date | null;
  expiresAt: Date | null;
  purchasedAtNew: Date | null;
  expiresAtNew: Date | null;
  discordId: string | null;
  migration: boolean;
}

export interface BillingInfo {
  creditsUsed: number;
  credits: number;
  creditsNew: number;
  creditsNewUsed: number;
  tokensUserNew: number;
  refCredits: number;
  purchasedAt: Date | null;
  expiresAt: Date | null;
  purchasedAtNew: Date | null;
  expiresAtNew: Date | null;
  daysUntilExpiration: number | null;
  daysUntilExpirationNew: number | null;
  subscriptionDays: number;
  isExpiringSoon: boolean;
  isExpiringSoonNew: boolean;
}

export class UserService {
  async getProfile(username: string): Promise<UserProfile | null> {
    const user = await userRepository.getFullUser(username);
    if (!user) return null;

    // Auto-migrate users with zero credits before returning profile
    if (!user.migration && user.credits === 0) {
      await migrationService.autoMigrateIfZeroCredits(username);
      // Fetch updated user after auto-migration
      const updatedUser = await userRepository.getFullUser(username);
      if (updatedUser) {
        return {
          username: updatedUser._id,
          apiKey: maskApiKey(updatedUser.apiKey),
          apiKeyCreatedAt: updatedUser.apiKeyCreatedAt,
          creditsUsed: updatedUser.creditsUsed,
          credits: updatedUser.credits || 0,
          creditsNew: updatedUser.creditsNew || 0,
          creditsNewUsed: (updatedUser as any).creditsNewUsed || 0,
          tokensUserNew: updatedUser.tokensUserNew || 0,
          refCredits: updatedUser.refCredits || 0,
          role: updatedUser.role,
          totalInputTokens: (updatedUser as any).totalInputTokens || 0,
          totalOutputTokens: (updatedUser as any).totalOutputTokens || 0,
          purchasedAt: updatedUser.purchasedAt || null,
          expiresAt: updatedUser.expiresAt || null,
          purchasedAtNew: (updatedUser as any).purchasedAtNew || null,
          expiresAtNew: (updatedUser as any).expiresAtNew || null,
          discordId: updatedUser.discordId || null,
          migration: updatedUser.migration || false,
        };
      }
    }

    return {
      username: user._id,
      apiKey: maskApiKey(user.apiKey),
      apiKeyCreatedAt: user.apiKeyCreatedAt,
      creditsUsed: user.creditsUsed,
      credits: user.credits || 0,
      creditsNew: user.creditsNew || 0,
      creditsNewUsed: (user as any).creditsNewUsed || 0,
      tokensUserNew: user.tokensUserNew || 0,
      refCredits: user.refCredits || 0,
      role: user.role,
      totalInputTokens: (user as any).totalInputTokens || 0,
      totalOutputTokens: (user as any).totalOutputTokens || 0,
      purchasedAt: user.purchasedAt || null,
      expiresAt: user.expiresAt || null,
      purchasedAtNew: (user as any).purchasedAtNew || null,
      expiresAtNew: (user as any).expiresAtNew || null,
      discordId: user.discordId || null,
      migration: user.migration || false,
    };
  }

  async getFullApiKey(username: string): Promise<string | null> {
    const user = await userRepository.getFullUser(username);
    return user?.apiKey || null;
  }

  async rotateApiKey(username: string): Promise<{ newApiKey: string; createdAt: Date }> {
    const newApiKey = await userRepository.rotateApiKey(username);
    return {
      newApiKey,
      createdAt: new Date(),
    };
  }

  async getBillingInfo(username: string): Promise<BillingInfo | null> {
    const user = await userRepository.getFullUser(username);
    if (!user) return null;

    // Calculate subscription days from purchasedAt and expiresAt (for credits/OhMyGPT)
    let subscriptionDays = 0;
    if (user.purchasedAt && user.expiresAt) {
      const purchasedAt = new Date(user.purchasedAt);
      const expiresAt = new Date(user.expiresAt);
      const totalDiff = expiresAt.getTime() - purchasedAt.getTime();
      subscriptionDays = Math.round(totalDiff / (1000 * 60 * 60 * 24));
    }

    // Calculate days until expiration for credits (OhMyGPT)
    let daysUntilExpiration: number | null = null;
    let isExpiringSoon = false;

    if (user.expiresAt && (user.credits > 0 || user.refCredits > 0)) {
      const now = new Date();
      const expiresAt = new Date(user.expiresAt);
      const diffTime = expiresAt.getTime() - now.getTime();
      daysUntilExpiration = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      isExpiringSoon = daysUntilExpiration <= 3 && daysUntilExpiration > 0;
    }

    // Calculate days until expiration for creditsNew (OpenHands)
    let daysUntilExpirationNew: number | null = null;
    let isExpiringSoonNew = false;
    const expiresAtNew = (user as any).expiresAtNew;

    if (expiresAtNew && user.creditsNew > 0) {
      const now = new Date();
      const expiresAtNewDate = new Date(expiresAtNew);
      const diffTime = expiresAtNewDate.getTime() - now.getTime();
      daysUntilExpirationNew = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      isExpiringSoonNew = daysUntilExpirationNew <= 3 && daysUntilExpirationNew > 0;
    }

    return {
      creditsUsed: user.creditsUsed,
      credits: user.credits || 0,
      creditsNew: user.creditsNew || 0,
      creditsNewUsed: (user as any).creditsNewUsed || 0,
      tokensUserNew: user.tokensUserNew || 0,
      refCredits: user.refCredits || 0,
      purchasedAt: user.purchasedAt || null,
      expiresAt: user.expiresAt || null,
      purchasedAtNew: (user as any).purchasedAtNew || null,
      expiresAtNew: expiresAtNew || null,
      daysUntilExpiration,
      daysUntilExpirationNew,
      subscriptionDays,
      isExpiringSoon,
      isExpiringSoonNew,
    };
  }

  async findByApiKey(apiKey: string): Promise<IUser | null> {
    return userRepository.findByApiKey(apiKey);
  }

  async checkAndResetExpiredCredits(username: string): Promise<{ wasExpired: boolean; user: IUser | null }> {
    return userRepository.checkAndResetExpiredCredits(username);
  }

  isCreditsExpired(user: IUser): boolean {
    return isCreditsExpired(user);
  }

  async updateDiscordId(username: string, discordId: string | null): Promise<{ success: boolean; discordId: string | null }> {
    // Validate Discord ID format if provided (17-19 digits)
    if (discordId && !/^\d{17,19}$/.test(discordId)) {
      throw new Error('Invalid Discord ID format');
    }

    const user = await userRepository.updateDiscordId(username, discordId);
    if (!user) {
      throw new Error('User not found');
    }

    return {
      success: true,
      discordId: user.discordId || null,
    };
  }
}

export const userService = new UserService();
