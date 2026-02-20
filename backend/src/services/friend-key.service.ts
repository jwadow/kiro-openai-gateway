import { friendKeyRepository } from '../repositories/friend-key.repository.js';
import { userRepository } from '../repositories/user.repository.js';
import { maskFriendApiKey, IFriendKey } from '../models/friend-key.model.js';
import { getModels } from './models.service.js';
import { FriendKeyResponse, ModelUsageResponse, CreateFriendKeyResponse } from '../dtos/friend-key.dto.js';

export class FriendKeyService {
  async getFriendKey(username: string): Promise<FriendKeyResponse | null> {
    const friendKey = await friendKeyRepository.findByOwnerId(username);
    if (!friendKey) return null;

    return {
      friendKey: maskFriendApiKey(friendKey._id),
      isActive: friendKey.isActive,
      createdAt: friendKey.createdAt,
      rotatedAt: friendKey.rotatedAt,
      modelLimits: friendKey.modelLimits.map(ml => ({
        modelId: ml.modelId,
        limitUsd: ml.limitUsd,
        usedUsd: ml.usedUsd,
        enabled: ml.enabled ?? true,
      })),
      totalUsedUsd: friendKey.totalUsedUsd,
      requestsCount: friendKey.requestsCount,
      lastUsedAt: friendKey.lastUsedAt,
    };
  }

  async getFullFriendKey(username: string): Promise<string | null> {
    const friendKey = await friendKeyRepository.findByOwnerId(username);
    return friendKey?._id || null;
  }

  async createFriendKey(username: string): Promise<CreateFriendKeyResponse> {
    const existing = await friendKeyRepository.findAnyByOwnerId(username);
    if (existing) {
      throw new Error('Friend Key already exists. Use rotate to generate a new one.');
    }

    const friendKey = await friendKeyRepository.create(username);
    return {
      friendKey: friendKey._id,
      message: 'Save this key - it will not be shown again',
    };
  }

  async rotateFriendKey(username: string): Promise<CreateFriendKeyResponse> {
    const existing = await friendKeyRepository.findAnyByOwnerId(username);
    if (!existing) {
      throw new Error('No Friend Key found to rotate');
    }

    const newKey = await friendKeyRepository.rotate(username);
    if (!newKey) {
      throw new Error('Failed to rotate Friend Key');
    }

    return {
      friendKey: newKey._id,
      message: 'Save this key - it will not be shown again. Old key has been invalidated.',
    };
  }

  async deleteFriendKey(username: string): Promise<boolean> {
    return friendKeyRepository.delete(username);
  }

  async updateModelLimits(username: string, modelLimits: { modelId: string; limitUsd: number; enabled?: boolean }[]): Promise<FriendKeyResponse | null> {
    const models = getModels();
    const validModelIds = new Set(models.map(m => m.id));
    
    for (const ml of modelLimits) {
      if (!validModelIds.has(ml.modelId)) {
        throw new Error(`Invalid model ID: ${ml.modelId}`);
      }
      if (ml.limitUsd < 0) {
        throw new Error(`Limit must be non-negative for model: ${ml.modelId}`);
      }
    }

    const updated = await friendKeyRepository.updateModelLimits(username, modelLimits);
    if (!updated) return null;

    return {
      friendKey: maskFriendApiKey(updated._id),
      isActive: updated.isActive,
      createdAt: updated.createdAt,
      rotatedAt: updated.rotatedAt,
      modelLimits: updated.modelLimits.map(ml => ({
        modelId: ml.modelId,
        limitUsd: ml.limitUsd,
        usedUsd: ml.usedUsd,
        enabled: ml.enabled ?? true,
      })),
      totalUsedUsd: updated.totalUsedUsd,
      requestsCount: updated.requestsCount,
      lastUsedAt: updated.lastUsedAt,
    };
  }

  async getModelUsage(username: string): Promise<ModelUsageResponse[]> {
    const friendKey = await friendKeyRepository.findByOwnerId(username);
    if (!friendKey) return [];

    const models = getModels();
    const modelMap = new Map(models.map(m => [m.id, m.name]));

    return friendKey.modelLimits.map(ml => {
      const remaining = Math.max(0, ml.limitUsd - ml.usedUsd);
      const usagePercent = ml.limitUsd > 0 ? (ml.usedUsd / ml.limitUsd) * 100 : 0;

      return {
        modelId: ml.modelId,
        modelName: modelMap.get(ml.modelId) || ml.modelId,
        limitUsd: ml.limitUsd,
        usedUsd: ml.usedUsd,
        remainingUsd: remaining,
        usagePercent: Math.min(100, usagePercent),
        isExhausted: ml.usedUsd >= ml.limitUsd,
        enabled: ml.enabled ?? true,
      };
    });
  }

  async validateFriendKeyRequest(apiKey: string, modelId: string): Promise<{
    valid: boolean;
    owner?: any;
    error?: string;
    errorType?: string;
  }> {
    const friendKey = await friendKeyRepository.findByApiKey(apiKey);
    if (!friendKey || !friendKey.isActive) {
      return { valid: false, error: 'Invalid API key', errorType: 'invalid_key' };
    }

    const owner = await userRepository.getFullUser(friendKey.ownerId);
    if (!owner || !owner.isActive) {
      return { valid: false, error: 'API key owner account is inactive', errorType: 'owner_inactive' };
    }

    if (owner.credits <= 0 && owner.refCredits <= 0) {
      return { valid: false, error: 'Friend Key owner must have credits', errorType: 'no_credits' };
    }

    const limitCheck = await friendKeyRepository.checkModelLimit(apiKey, modelId);
    if (!limitCheck.allowed) {
      if (limitCheck.enabled === false) {
        return { 
          valid: false, 
          error: 'This model is disabled for your Friend Key', 
          errorType: 'friend_key_model_disabled' 
        };
      }
      if (limitCheck.limit === 0) {
        return { 
          valid: false, 
          error: 'This model is not configured for your Friend Key', 
          errorType: 'friend_key_model_not_allowed' 
        };
      }
      return { 
        valid: false, 
        error: `Model spending limit exceeded (${limitCheck.used?.toFixed(2)}/${limitCheck.limit?.toFixed(2)} USD)`,
        errorType: 'friend_key_model_limit_exceeded'
      };
    }

    if (owner.credits <= 0 && owner.refCredits <= 0) {
      return { valid: false, error: 'API key owner has insufficient credits', errorType: 'owner_credits_exhausted' };
    }

    return { valid: true, owner };
  }

  async recordFriendKeyUsage(apiKey: string, modelId: string, costUsd: number): Promise<void> {
    await friendKeyRepository.updateModelUsage(apiKey, modelId, costUsd);
  }
}

export const friendKeyService = new FriendKeyService();
