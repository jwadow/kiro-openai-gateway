import { UserNew, IUserNew, hashPassword, generateApiKey, generateReferralCode } from '../models/user-new.model.js';
import { MigrationLog } from '../models/migration-log.model.js';

export interface CreateUserNewData {
  username: string;
  password: string;
  role: 'admin' | 'user';
  referredBy?: string;
}

export function isCreditsExpired(user: IUserNew): boolean {
  if (!user.expiresAt) return true;
  return new Date() > new Date(user.expiresAt);
}

export class UserNewRepository {
  async findById(id: string): Promise<IUserNew | null> {
    let user = await UserNew.findById(id).lean();
    if (user) return user;

    user = await UserNew.findOne({
      _id: { $regex: new RegExp(`^\\s*${id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*$`, 'i') }
    }).lean();
    return user;
  }

  async findByUsername(username: string): Promise<IUserNew | null> {
    return this.findById(username);
  }

  async create(data: CreateUserNewData): Promise<IUserNew> {
    const { hash, salt } = hashPassword(data.password);
    const apiKey = generateApiKey();
    const now = new Date();

    let validReferredBy: string | null = null;
    if (data.referredBy) {
      const referrer = await UserNew.findOne({ referralCode: data.referredBy }).lean();
      if (referrer) {
        validReferredBy = referrer._id;
      }
    }

    let user;
    let createAttempts = 0;
    const maxCreateAttempts = 3;

    while (createAttempts < maxCreateAttempts) {
      let referralCode = generateReferralCode();
      let codeAttempts = 0;
      while (await UserNew.exists({ referralCode }) && codeAttempts < 10) {
        referralCode = generateReferralCode();
        codeAttempts++;
      }

      try {
        user = await UserNew.create({
          _id: data.username,
          passwordHash: hash,
          passwordSalt: salt,
          role: data.role,
          isActive: true,
          apiKey,
          apiKeyCreatedAt: now,
          credits: 0,
          creditsUsed: 0,
          referralCode,
          referredBy: validReferredBy,
          refCredits: 0,
          referralBonusAwarded: false,
          migration: true, // New users are on the new rate (no migration needed)
        });
        break;
      } catch (err: any) {
        if (err.code === 11000 && err.keyPattern?.referralCode) {
          createAttempts++;
          if (createAttempts >= maxCreateAttempts) {
            throw new Error('Failed to generate unique referral code after multiple attempts');
          }
          continue;
        }
        throw err;
      }
    }

    if (!user) {
      throw new Error('Failed to create user');
    }

    return user.toObject();
  }

  async updateLastLogin(id: string): Promise<void> {
    await UserNew.updateOne({ _id: id }, { lastLoginAt: new Date() });
  }

  async setActive(id: string, isActive: boolean): Promise<IUserNew | null> {
    return UserNew.findByIdAndUpdate(id, { isActive }, { new: true }).lean();
  }

  async exists(username: string): Promise<boolean> {
    const count = await UserNew.countDocuments({ _id: username });
    return count > 0;
  }

  async findByApiKey(apiKey: string): Promise<IUserNew | null> {
    return UserNew.findOne({ apiKey, isActive: true }).lean();
  }

  async rotateApiKey(username: string): Promise<string> {
    const user = await UserNew.findById(username).lean();
    if (!user) throw new Error('User not found');

    const newApiKey = generateApiKey();
    const now = new Date();

    await UserNew.updateOne(
      { _id: username },
      { apiKey: newApiKey, apiKeyCreatedAt: now }
    );

    return newApiKey;
  }

  async addCredits(username: string, credits: number): Promise<IUserNew | null> {
    return UserNew.findByIdAndUpdate(
      username,
      { $inc: { credits } },
      { new: true }
    ).lean();
  }

  async setCredits(username: string, credits: number): Promise<IUserNew | null> {
    return UserNew.findByIdAndUpdate(
      username,
      { credits },
      { new: true }
    ).lean();
  }

  async getFullUser(username: string): Promise<IUserNew | null> {
    return UserNew.findById(username).lean();
  }

  async listUsers(search?: string): Promise<IUserNew[]> {
    const query: any = {};
    if (search) {
      query._id = { $regex: search, $options: 'i' };
    }
    return UserNew.find(query)
      .select('-passwordHash -passwordSalt')
      .sort({ createdAt: -1 })
      .lean();
  }

  async getUserStats(period: string = 'all'): Promise<{
    total: number;
    totalCreditsUsed: number;
    totalCredits: number;
    totalRefCredits: number;
    totalInputTokens: number;
    totalOutputTokens: number;
    activeUsers: number
  }> {
    const total = await UserNew.countDocuments();

    const userAgg = await UserNew.aggregate([
      {
        $group: {
          _id: null,
          totalCredits: { $sum: '$credits' },
          totalRefCredits: { $sum: '$refCredits' },
          totalCreditsUsed: { $sum: '$creditsUsed' },
          totalInputTokens: { $sum: '$totalInputTokens' },
          totalOutputTokens: { $sum: '$totalOutputTokens' },
          activeUsers: {
            $sum: { $cond: [{ $or: [{ $gt: ['$credits', 0] }, { $gt: ['$refCredits', 0] }] }, 1, 0] }
          }
        }
      }
    ]);

    return {
      total,
      totalCreditsUsed: userAgg[0]?.totalCreditsUsed || 0,
      totalCredits: userAgg[0]?.totalCredits || 0,
      totalRefCredits: userAgg[0]?.totalRefCredits || 0,
      totalInputTokens: userAgg[0]?.totalInputTokens || 0,
      totalOutputTokens: userAgg[0]?.totalOutputTokens || 0,
      activeUsers: userAgg[0]?.activeUsers || 0
    };
  }

  async updateRefCredits(username: string, refCredits: number): Promise<IUserNew | null> {
    return UserNew.findByIdAndUpdate(
      username,
      { refCredits },
      { new: true }
    ).lean();
  }

  async resetExpiredCredits(username: string): Promise<IUserNew | null> {
    return UserNew.findByIdAndUpdate(
      username,
      {
        credits: 0,
        purchasedAt: null,
        expiresAt: null,
      },
      { new: true }
    ).lean();
  }

  async checkAndResetExpiredCredits(username: string): Promise<{ wasExpired: boolean; user: IUserNew | null }> {
    const user = await UserNew.findById(username).lean();
    if (!user) return { wasExpired: false, user: null };

    if (isCreditsExpired(user) && user.credits > 0) {
      const resetUser = await this.resetExpiredCredits(username);
      return { wasExpired: true, user: resetUser };
    }

    return { wasExpired: false, user };
  }

  // Referral methods
  async findByReferralCode(referralCode: string): Promise<IUserNew | null> {
    return UserNew.findOne({ referralCode }).lean();
  }

  async addRefCredits(username: string, amount: number): Promise<IUserNew | null> {
    return UserNew.findByIdAndUpdate(
      username,
      { $inc: { refCredits: amount } },
      { new: true }
    ).lean();
  }

  async setCreditPackage(username: string, credits: number, expiresAt: Date): Promise<IUserNew | null> {
    return UserNew.findByIdAndUpdate(
      username,
      {
        $set: {
          credits,
          expiresAt,
          purchasedAt: new Date()
        }
      },
      { new: true }
    ).lean();
  }

  async markReferralBonusAwarded(username: string): Promise<void> {
    await UserNew.updateOne(
      { _id: username },
      { referralBonusAwarded: true }
    );
  }

  async getReferralStats(username: string): Promise<{
    totalReferrals: number;
    successfulReferrals: number;
    totalRefCreditsEarned: number;
    currentRefCredits: number;
  }> {
    const user = await UserNew.findById(username).lean();
    if (!user) {
      return { totalReferrals: 0, successfulReferrals: 0, totalRefCreditsEarned: 0, currentRefCredits: 0 };
    }

    const totalReferrals = await UserNew.countDocuments({ referredBy: username });
    const successfulReferrals = await UserNew.countDocuments({
      referredBy: username,
      referralBonusAwarded: true
    });

    const totalRefCreditsEarned = successfulReferrals * 15;

    return {
      totalReferrals,
      successfulReferrals,
      totalRefCreditsEarned,
      currentRefCredits: user.refCredits || 0,
    };
  }

  async getReferredUsers(username: string): Promise<Array<{
    username: string;
    status: 'registered' | 'paid';
    bonusEarned: number;
    createdAt: Date;
  }>> {
    const referredUsers = await UserNew.find({ referredBy: username })
      .select('_id referralBonusAwarded createdAt')
      .sort({ createdAt: -1 })
      .lean();

    return referredUsers.map(u => ({
      username: u._id,
      status: u.referralBonusAwarded ? 'paid' : 'registered',
      bonusEarned: u.referralBonusAwarded ? 15 : 0,
      createdAt: u.createdAt,
    }));
  }

  // Bulk insert for migration
  async insertMany(users: IUserNew[]): Promise<void> {
    await UserNew.insertMany(users);
  }

  async countDocuments(): Promise<number> {
    return UserNew.countDocuments();
  }

  async updateDiscordId(username: string, discordId: string | null): Promise<IUserNew | null> {
    return UserNew.findByIdAndUpdate(
      username,
      { discordId },
      { new: true }
    ).lean();
  }

  // Migration methods
  async getMigrationStatus(userId: string): Promise<boolean> {
    const user = await UserNew.findById(userId).select('migration').lean();
    return user?.migration ?? false;
  }

  async setMigrated(userId: string, autoMigrated: boolean = false): Promise<{
    user: IUserNew | null;
    oldCredits: number;
    newCredits: number;
  } | null> {
    const user = await UserNew.findById(userId).lean();
    if (!user) return null;

    // Check if already migrated
    if (user.migration) {
      return null;
    }

    const oldCredits = user.credits;
    const newCredits = oldCredits / 2.5;

    // Update user with migrated status and new credits
    const updatedUser = await UserNew.findByIdAndUpdate(
      userId,
      {
        migration: true,
        credits: newCredits,
      },
      { new: true }
    ).lean();

    // Create migration log
    await MigrationLog.create({
      userId,
      username: user._id,
      oldCredits,
      newCredits,
      migratedAt: new Date(),
      oldRate: 1000,
      newRate: 2500,
      autoMigrated,
    });

    return {
      user: updatedUser,
      oldCredits,
      newCredits,
    };
  }
}

export const userNewRepository = new UserNewRepository();
