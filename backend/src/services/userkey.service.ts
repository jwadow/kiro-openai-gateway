import { userKeyRepository } from '../repositories/user-key.repository.js';
import { CreateUserKeyInput, UpdateUserKeyInput } from '../dtos/user-key.dto.js';
import { IUserKey } from '../models/user-key.model.js';

export async function listUserKeys(): Promise<IUserKey[]> {
  return userKeyRepository.findAll();
}

export async function getUserKey(id: string): Promise<IUserKey | null> {
  return userKeyRepository.findById(id);
}

export async function createUserKey(input: CreateUserKeyInput): Promise<IUserKey> {
  return userKeyRepository.create(input);
}

export async function updateUserKey(id: string, input: UpdateUserKeyInput): Promise<IUserKey | null> {
  return userKeyRepository.update(id, input);
}

export async function deleteUserKey(id: string): Promise<IUserKey | null> {
  return userKeyRepository.delete(id);
}

export async function revokeUserKey(id: string): Promise<IUserKey | null> {
  return userKeyRepository.setActive(id, false);
}

export async function resetUserKeyUsage(id: string): Promise<IUserKey | null> {
  return userKeyRepository.resetUsage(id);
}

export async function getKeyStats(): Promise<{ total: number; active: number }> {
  return userKeyRepository.getStats();
}

export function maskKey(key: string): string {
  if (!key || key.length < 10) return '***';
  return key.substring(0, 7) + '***' + key.substring(key.length - 3);
}
