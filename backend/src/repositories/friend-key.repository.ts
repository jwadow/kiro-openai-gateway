import { FriendKey, IFriendKey, IModelLimit, generateFriendApiKey } from '../models/friend-key.model.js';

export class FriendKeyRepository {
  async findByApiKey(apiKey: string): Promise<IFriendKey | null> {
    return FriendKey.findById(apiKey).lean();
  }

  async findByOwnerId(ownerId: string): Promise<IFriendKey | null> {
    return FriendKey.findOne({ ownerId, isActive: true }).lean();
  }

  async findAnyByOwnerId(ownerId: string): Promise<IFriendKey | null> {
    return FriendKey.findOne({ ownerId }).lean();
  }

  async create(ownerId: string): Promise<IFriendKey> {
    const apiKey = generateFriendApiKey();
    const friendKey = await FriendKey.create({
      _id: apiKey,
      ownerId,
      isActive: true,
      modelLimits: [],
      totalUsedUsd: 0,
      requestsCount: 0,
    });
    return friendKey.toObject();
  }

  async rotate(ownerId: string): Promise<IFriendKey | null> {
    const existing = await FriendKey.findOne({ ownerId });
    if (!existing) return null;

    const newApiKey = generateFriendApiKey();
    const modelLimits = existing.modelLimits.map(ml => ({
      modelId: ml.modelId,
      limitUsd: ml.limitUsd,
      usedUsd: 0,
      enabled: ml.enabled ?? true,
    }));

    await FriendKey.deleteOne({ ownerId });

    const newKey = await FriendKey.create({
      _id: newApiKey,
      ownerId,
      isActive: true,
      rotatedAt: new Date(),
      modelLimits,
      totalUsedUsd: 0,
      requestsCount: 0,
    });
    return newKey.toObject();
  }

  async delete(ownerId: string): Promise<boolean> {
    const result = await FriendKey.deleteOne({ ownerId });
    return result.deletedCount > 0;
  }

  async setActive(ownerId: string, isActive: boolean): Promise<IFriendKey | null> {
    return FriendKey.findOneAndUpdate(
      { ownerId },
      { isActive },
      { new: true }
    ).lean();
  }

  async updateModelLimits(ownerId: string, modelLimits: { modelId: string; limitUsd: number; enabled?: boolean }[]): Promise<IFriendKey | null> {
    const existing = await FriendKey.findOne({ ownerId });
    if (!existing) return null;

    const updatedLimits: IModelLimit[] = modelLimits.map(ml => {
      const existingLimit = existing.modelLimits.find(el => el.modelId === ml.modelId);
      return {
        modelId: ml.modelId,
        limitUsd: ml.limitUsd,
        usedUsd: existingLimit?.usedUsd || 0,
        enabled: ml.enabled ?? existingLimit?.enabled ?? true,
      };
    });

    return FriendKey.findOneAndUpdate(
      { ownerId },
      { modelLimits: updatedLimits },
      { new: true }
    ).lean();
  }

  async updateModelUsage(apiKey: string, modelId: string, costUsd: number): Promise<IFriendKey | null> {
    const friendKey = await FriendKey.findById(apiKey);
    if (!friendKey) return null;

    const modelLimit = friendKey.modelLimits.find(ml => ml.modelId === modelId);
    if (modelLimit) {
      modelLimit.usedUsd += costUsd;
    }

    friendKey.totalUsedUsd += costUsd;
    friendKey.requestsCount += 1;
    friendKey.lastUsedAt = new Date();

    await friendKey.save();
    return friendKey.toObject();
  }

  async checkModelLimit(apiKey: string, modelId: string): Promise<{ allowed: boolean; limit?: number; used?: number; remaining?: number; enabled?: boolean }> {
    const friendKey = await FriendKey.findById(apiKey).lean();
    if (!friendKey || !friendKey.isActive) {
      return { allowed: false };
    }

    const modelLimit = friendKey.modelLimits.find(ml => ml.modelId === modelId);
    if (!modelLimit || modelLimit.limitUsd <= 0) {
      return { allowed: false, limit: 0, used: 0, remaining: 0, enabled: false };
    }

    // Check if model is enabled
    if (modelLimit.enabled === false) {
      return { allowed: false, limit: modelLimit.limitUsd, used: modelLimit.usedUsd, remaining: modelLimit.limitUsd - modelLimit.usedUsd, enabled: false };
    }

    const remaining = modelLimit.limitUsd - modelLimit.usedUsd;
    return {
      allowed: remaining > 0,
      limit: modelLimit.limitUsd,
      used: modelLimit.usedUsd,
      remaining: Math.max(0, remaining),
      enabled: true,
    };
  }
}

export const friendKeyRepository = new FriendKeyRepository();
