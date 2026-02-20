import { Request, Response } from 'express';
import { z } from 'zod';
import { authService } from '../services/auth.service.js';
import { LoginDTO, RegisterDTO } from '../dtos/auth.dto.js';

export class AuthController {
  async login(req: Request, res: Response): Promise<void> {
    try {
      const input = LoginDTO.parse(req.body);
      const result = await authService.login(input);
      res.json(result);
    } catch (error: any) {
      if (error instanceof z.ZodError) {
        res.status(400).json({ error: 'Validation failed', details: error.errors });
        return;
      }
      if (error.message === 'Invalid credentials') {
        res.status(401).json({ error: error.message });
        return;
      }
      console.error('Login error:', error);
      res.status(500).json({ error: 'Login failed' });
    }
  }

  async register(req: Request, res: Response): Promise<void> {
    try {
      const input = RegisterDTO.parse(req.body);
      const result = await authService.register(input);
      res.status(201).json({
        message: 'User registered successfully',
        ...result,
      });
    } catch (error: any) {
      if (error instanceof z.ZodError) {
        res.status(400).json({ error: 'Validation failed', details: error.errors });
        return;
      }
      if (error.message === 'Username already exists') {
        res.status(409).json({ error: error.message });
        return;
      }
      console.error('Register error:', error);
      res.status(500).json({ error: 'Registration failed' });
    }
  }
}

export const authController = new AuthController();
