import { z } from 'zod';

export const CreateProxyDTO = z.object({
  name: z.string().min(1).max(100),
  type: z.enum(['http', 'socks5']),
  host: z.string().min(1),
  port: z.number().int().min(1).max(65535),
  username: z.string().optional(),
  password: z.string().optional(),
});

export const UpdateProxyDTO = z.object({
  name: z.string().min(1).max(100).optional(),
  type: z.enum(['http', 'socks5']).optional(),
  host: z.string().min(1).optional(),
  port: z.number().int().min(1).max(65535).optional(),
  username: z.string().optional(),
  password: z.string().optional(),
  isActive: z.boolean().optional(),
});

export const BindKeyDTO = z.object({
  factoryKeyId: z.string().min(1),
  priority: z.number().int().min(1).max(2).default(1),
});

export type CreateProxyInput = z.infer<typeof CreateProxyDTO>;
export type UpdateProxyInput = z.infer<typeof UpdateProxyDTO>;
export type BindKeyInput = z.infer<typeof BindKeyDTO>;

export interface ProxyResponse {
  id: string;
  name: string;
  type: string;
  host: string;
  port: number;
  username?: string;
  status: string;
  lastLatencyMs?: number;
  lastCheckedAt?: string;
  lastError?: string;
  failCount: number;
  isActive: boolean;
  createdAt: string;
}
