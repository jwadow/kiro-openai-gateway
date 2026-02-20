import { CreditsResetLog, ICreditsResetLog, ResetTrigger } from '../models/credits-reset-log.model.js';

export interface CreateResetLogData {
  username: string;
  creditsBefore: number;
  expiresAt: Date | null;
  resetBy: ResetTrigger;
  note?: string;
}

export class CreditsResetLogRepository {
  async create(data: CreateResetLogData): Promise<ICreditsResetLog> {
    const log = await CreditsResetLog.create({
      username: data.username,
      creditsBefore: data.creditsBefore,
      expiresAt: data.expiresAt,
      resetAt: new Date(),
      resetBy: data.resetBy,
      note: data.note || null,
    });
    return log.toObject();
  }

  async findByUsername(username: string, limit: number = 50, offset: number = 0): Promise<ICreditsResetLog[]> {
    return CreditsResetLog.find({ username })
      .sort({ resetAt: -1 })
      .skip(offset)
      .limit(limit)
      .lean();
  }

  async findRecent(limit: number = 100, offset: number = 0): Promise<ICreditsResetLog[]> {
    return CreditsResetLog.find()
      .sort({ resetAt: -1 })
      .skip(offset)
      .limit(limit)
      .lean();
  }

  async countByUsername(username: string): Promise<number> {
    return CreditsResetLog.countDocuments({ username });
  }

  async countAll(): Promise<number> {
    return CreditsResetLog.countDocuments();
  }
}

export const creditsResetLogRepository = new CreditsResetLogRepository();
