import { z } from 'zod';

export const ModelLimitSchema = z.object({
  modelId: z.string().min(1),
  limitUsd: z.number().min(0),
  enabled: z.boolean().optional().default(true),
});

export const UpdateModelLimitsDto = z.object({
  modelLimits: z.array(ModelLimitSchema),
});

export type UpdateModelLimitsInput = z.infer<typeof UpdateModelLimitsDto>;

export interface FriendKeyResponse {
  friendKey: string;
  isActive: boolean;
  createdAt: Date;
  rotatedAt?: Date;
  modelLimits: {
    modelId: string;
    limitUsd: number;
    usedUsd: number;
    enabled: boolean;
  }[];
  totalUsedUsd: number;
  requestsCount: number;
  lastUsedAt?: Date;
}

export interface ModelUsageResponse {
  modelId: string;
  modelName: string;
  limitUsd: number;
  usedUsd: number;
  remainingUsd: number;
  usagePercent: number;
  isExhausted: boolean;
  enabled: boolean;
}

export interface CreateFriendKeyResponse {
  friendKey: string;
  message: string;
}
