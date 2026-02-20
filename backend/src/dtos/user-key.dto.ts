import { z } from 'zod';

// Note: tier removed from CreateUserKeyDTO as part of tier system deprecation (Story 3.2)
export const CreateUserKeyDTO = z.object({
  name: z.string().min(1).max(100),
  notes: z.string().max(500).optional(),
});

export const UpdateUserKeyDTO = z.object({
  notes: z.string().max(500).optional(),
  isActive: z.boolean().optional(),
});

export type CreateUserKeyInput = z.infer<typeof CreateUserKeyDTO>;
export type UpdateUserKeyInput = z.infer<typeof UpdateUserKeyDTO>;

// Note: tier removed from UserKeyResponse as part of tier system deprecation (Story 3.2)
export interface UserKeyResponse {
  id: string;
  name: string;
  tokensUsed: number;
  isActive: boolean;
  requestsCount: number;
  createdAt: string;
  lastUsedAt?: string;
  notes?: string;
}
