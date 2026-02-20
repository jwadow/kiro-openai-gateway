import { z } from 'zod';

export const LoginDTO = z.object({
  username: z.string().trim().min(3, 'Username must be at least 3 characters').max(50),
  password: z.string(),
});

export const RegisterDTO = z.object({
  username: z.string()
    .trim()
    .toLowerCase()
    .min(3, 'Username must be at least 3 characters')
    .max(50)
    .regex(/^[a-z0-9_-]+$/, 'Username can only contain letters, numbers, underscores and hyphens'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  role: z.enum(['admin', 'user']).default('user'),
  ref: z.string().trim().toUpperCase().optional(),
});

export type LoginInput = z.infer<typeof LoginDTO>;
export type RegisterInput = z.infer<typeof RegisterDTO>;

export interface AuthResponse {
  token: string;
  username: string;
  role: string;
  expires_in: string;
}

export interface JwtPayload {
  username: string;
  role: string;
  iat?: number;
  exp?: number;
}
