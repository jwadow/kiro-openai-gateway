import { UserNew, IUserNew, hashPassword, generateApiKey, generateReferralCode } from '../models/user-new.model.js';
import { UserKey } from '../models/user-key.model.js';
import { RequestLog } from '../models/request-log.model.js';

// Alias for backward compatibility
const User = UserNew;
type IUser = IUserNew;

export interface CreateUserData {
  username: string;
  password: string;
  role: 'admin' | 'user';
  referredBy?: string;
}

export function isCreditsExpired(user: IUser): boolean {
  if (!user.expiresAt) return true;
  return new Date() > new Date(user.expiresAt);
}

export class UserRepository {
  async findById(id: string): Promise<IUser | null> {
    let user = await User.findById(id).lean();
    if (user) return user;
    
    user = await User.findOne({ 
      _id: { $regex: new RegExp(`^\\s*${id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*$`, 'i') }
    }).lean();
    return user;
  }

  async findByUsername(username: string): Promise<IUser | null> {
    return this.findById(username);
  }

  async create(data: CreateUserData): Promise<IUser> {
    const { hash, salt } = hashPassword(data.password);
    const apiKey = generateApiKey();
    const now = new Date();
    
    let validReferredBy: string | null = null;
    if (data.referredBy) {
      const referrer = await User.findOne({ referralCode: data.referredBy }).lean();
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
      while (await User.exists({ referralCode }) && codeAttempts < 10) {
        referralCode = generateReferralCode();
        codeAttempts++;
      }

      try {
        user = await User.create({
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
    await User.updateOne({ _id: id }, { lastLoginAt: new Date() });
  }

  async setActive(id: string, isActive: boolean): Promise<IUser | null> {
    return User.findByIdAndUpdate(id, { isActive }, { new: true }).lean();
  }

  async exists(username: string): Promise<boolean> {
    const count = await User.countDocuments({ _id: username });
    return count > 0;
  }

  async findByApiKey(apiKey: string): Promise<IUser | null> {
    return User.findOne({ apiKey, isActive: true }).lean();
  }

  async rotateApiKey(username: string): Promise<string> {
    const user = await User.findById(username).lean();
    if (!user) throw new Error('User not found');

    const oldApiKey = user.apiKey;
    const newApiKey = generateApiKey();
    const now = new Date();

    await User.updateOne(
      { _id: username },
      { apiKey: newApiKey, apiKeyCreatedAt: now }
    );

    if (user.credits > 0 || user.refCredits > 0) {
      if (oldApiKey) {
        await UserKey.deleteOne({ _id: oldApiKey });
      }
      await UserKey.create({
        _id: newApiKey,
        name: username,
        tier: 'pro',
        tokensUsed: user.creditsUsed || 0,
        requestsCount: 0,
        isActive: true,
        createdAt: now,
        expiresAt: user.expiresAt,
      });
    }

    return newApiKey;
  }

  async addCredits(username: string, credits: number, resetExpiration: boolean = true): Promise<IUser | null> {
    const VALIDITY_DAYS = 7;
    const now = new Date();
    const expiresAt = new Date(now.getTime() + VALIDITY_DAYS * 24 * 60 * 60 * 1000);

    const updateQuery: any = {
      $inc: { credits }
    };

    if (resetExpiration) {
      updateQuery.$set = { expiresAt, purchasedAt: now };
    }

    const updatedUser = await User.findByIdAndUpdate(
      username,
      updateQuery,
      { new: true }
    ).lean();

    if (resetExpiration && updatedUser?.apiKey) {
      await UserKey.updateOne(
        { _id: updatedUser.apiKey },
        { $set: { expiresAt } },
        { upsert: false }
      );
    }

    return updatedUser;
  }

  async setCredits(username: string, credits: number, resetExpiration: boolean = true): Promise<IUser | null> {
    const VALIDITY_DAYS = 7;
    const now = new Date();
    const expiresAt = new Date(now.getTime() + VALIDITY_DAYS * 24 * 60 * 60 * 1000);

    const setFields: any = { credits };
    if (resetExpiration) {
      setFields.expiresAt = expiresAt;
      setFields.purchasedAt = now;
    }

    const updatedUser = await User.findByIdAndUpdate(
      username,
      { $set: setFields },
      { new: true }
    ).lean();

    if (resetExpiration && updatedUser?.apiKey) {
      await UserKey.updateOne(
        { _id: updatedUser.apiKey },
        { $set: { expiresAt } },
        { upsert: false }
      );
    }

    return updatedUser;
  }

  async addCreditsNew(username: string, amount: number, resetExpiration: boolean = true): Promise<IUser | null> {
    const VALIDITY_DAYS = 7;
    const now = new Date();
    const expiresAtNew = new Date(now.getTime() + VALIDITY_DAYS * 24 * 60 * 60 * 1000);

    const updateQuery: any = {
      $inc: { creditsNew: amount }
    };

    if (resetExpiration) {
      updateQuery.$set = { expiresAtNew, purchasedAtNew: now };
    }

    const updatedUser = await User.findByIdAndUpdate(
      username,
      updateQuery,
      { new: true }
    ).lean();

    return updatedUser;
  }

  async setCreditsNew(username: string, creditsNew: number, resetExpiration: boolean = true): Promise<IUser | null> {
    const VALIDITY_DAYS = 7;
    const now = new Date();
    const expiresAtNew = new Date(now.getTime() + VALIDITY_DAYS * 24 * 60 * 60 * 1000);

    const setFields: any = { creditsNew };
    if (resetExpiration) {
      setFields.expiresAtNew = expiresAtNew;
      setFields.purchasedAtNew = now;
    }

    const updatedUser = await User.findByIdAndUpdate(
      username,
      { $set: setFields },
      { new: true }
    ).lean();

    return updatedUser;
  }

  async getFullUser(username: string): Promise<IUser | null> {
    return User.findById(username).lean();
  }

  async listUsers(search?: string): Promise<IUser[]> {
    const query: any = {};
    if (search) {
      query._id = { $regex: search, $options: 'i' };
    }
    return User.find(query)
      .select('-passwordHash -passwordSalt')
      .sort({ createdAt: -1 })
      .lean();
  }

  async getUserStats(period: string = 'all'): Promise<{
    total: number;
    totalCreditsUsed: number;
    totalCredits: number;
    totalRefCredits: number;
    totalCreditsNew: number;
    totalCreditsNewUsed: number;
    totalInputTokens: number;
    totalOutputTokens: number;
    activeUsers: number
  }> {
    const total = await User.countDocuments();

    // Get current credits/refCredits from User collection (always total, not filtered by period)
    const userAgg = await User.aggregate([
      {
        $group: {
          _id: null,
          totalCredits: { $sum: '$credits' },
          totalRefCredits: { $sum: '$refCredits' },
          totalCreditsNew: { $sum: '$creditsNew' },
          activeUsers: {
            $sum: { $cond: [{ $or: [{ $gt: ['$credits', 0] }, { $gt: ['$refCredits', 0] }] }, 1, 0] }
          }
        }
      }
    ]);

    // Calculate date filter for period-based stats from RequestLog
    let dateFilter: any = {};
    if (period !== 'all') {
      const now = new Date();
      let startDate: Date;
      switch (period) {
        case '1h':
          startDate = new Date(now.getTime() - 60 * 60 * 1000);
          break;
        case '2h':
          startDate = new Date(now.getTime() - 2 * 60 * 60 * 1000);
          break;
        case '3h':
          startDate = new Date(now.getTime() - 3 * 60 * 60 * 1000);
          break;
        case '4h':
          startDate = new Date(now.getTime() - 4 * 60 * 60 * 1000);
          break;
        case '8h':
          startDate = new Date(now.getTime() - 8 * 60 * 60 * 1000);
          break;
        case '24h':
          startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
          break;
        case '3d':
          startDate = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);
          break;
        case '7d':
          startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          break;
        case '30d':
          startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
          break;
        default:
          startDate = new Date(0);
      }
      dateFilter = { createdAt: { $gte: startDate } };
    }

    // Get usage stats from RequestLog (filtered by period)
    const logAgg = await RequestLog.aggregate([
      { $match: dateFilter },
      {
        $group: {
          _id: null,
          totalCreditsUsed: { $sum: '$creditsCost' },
          totalInputTokens: { $sum: '$inputTokens' },
          totalOutputTokens: { $sum: '$outputTokens' },
          activeUserIds: { $addToSet: '$userId' }
        }
      }
    ]);

    // Get OpenHands usage stats from RequestLog (filtered by period)
    const openhandsAgg = await RequestLog.aggregate([
      {
        $match: {
          ...dateFilter,
          creditType: 'openhands'
        }
      },
      {
        $group: {
          _id: null,
          totalCreditsNewUsed: { $sum: '$creditsCost' }
        }
      }
    ]);

    // For 'all' period, count users with credits > 0 as active
    // For specific periods, count distinct users who had activity in that period
    const activeUsers = period === 'all' 
      ? (userAgg[0]?.activeUsers || 0)
      : (logAgg[0]?.activeUserIds?.filter((id: string | null) => id != null).length || 0);

    return {
      total,
      totalCreditsUsed: logAgg[0]?.totalCreditsUsed || 0,
      totalCredits: userAgg[0]?.totalCredits || 0,
      totalRefCredits: userAgg[0]?.totalRefCredits || 0,
      totalCreditsNew: userAgg[0]?.totalCreditsNew || 0,
      totalCreditsNewUsed: openhandsAgg[0]?.totalCreditsNewUsed || 0,
      totalInputTokens: logAgg[0]?.totalInputTokens || 0,
      totalOutputTokens: logAgg[0]?.totalOutputTokens || 0,
      activeUsers
    };
  }

  async updateRefCredits(username: string, refCredits: number): Promise<IUser | null> {
    return User.findByIdAndUpdate(
      username,
      { refCredits },
      { new: true }
    ).lean();
  }

  async resetExpiredCredits(username: string): Promise<IUser | null> {
    const user = await User.findById(username).lean();
    if (!user || !user.apiKey) return null;

    await UserKey.deleteOne({ _id: user.apiKey });

    return User.findByIdAndUpdate(
      username,
      {
        credits: 0,
        purchasedAt: null,
        expiresAt: null,
      },
      { new: true }
    ).lean();
  }

  async checkAndResetExpiredCredits(username: string): Promise<{ wasExpired: boolean; user: IUser | null }> {
    const user = await User.findById(username).lean();
    if (!user) return { wasExpired: false, user: null };
    
    if (isCreditsExpired(user) && user.credits > 0) {
      const resetUser = await this.resetExpiredCredits(username);
      return { wasExpired: true, user: resetUser };
    }
    
    return { wasExpired: false, user };
  }

  // Referral methods
  async findByReferralCode(referralCode: string): Promise<IUser | null> {
    return User.findOne({ referralCode }).lean();
  }

  async addRefCredits(username: string, amount: number): Promise<IUser | null> {
    return User.findByIdAndUpdate(
      username,
      { $inc: { refCredits: amount } },
      { new: true }
    ).lean();
  }

  async setCreditPackage(username: string, credits: number, expiresAt: Date): Promise<IUser | null> {
    return User.findByIdAndUpdate(
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
    await User.updateOne(
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
    const user = await User.findById(username).lean();
    if (!user) {
      return { totalReferrals: 0, successfulReferrals: 0, totalRefCreditsEarned: 0, currentRefCredits: 0 };
    }

    const totalReferrals = await User.countDocuments({ referredBy: username });
    const successfulReferrals = await User.countDocuments({ 
      referredBy: username, 
      referralBonusAwarded: true 
    });

    // Average bonus is $15 (average of $10 and $20)
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
    const referredUsers = await User.find({ referredBy: username })
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

  async updateDiscordId(username: string, discordId: string | null): Promise<IUser | null> {
    return User.findByIdAndUpdate(
      username,
      { discordId },
      { new: true }
    ).lean();
  }

  async generateReferralCodeForExistingUsers(): Promise<number> {
    const usersWithoutCode = await User.find({ 
      $or: [
        { referralCode: { $exists: false } },
        { referralCode: null },
        { referralCode: '' },
        { referralCode: 'undefined' }
      ]
    }).lean();

    let updated = 0;
    for (const user of usersWithoutCode) {
      let referralCode = generateReferralCode();
      let attempts = 0;
      while (await User.exists({ referralCode }) && attempts < 10) {
        referralCode = generateReferralCode();
        attempts++;
      }
      await User.updateOne(
        { _id: user._id }, 
        { 
          $set: {
            referralCode,
            refCredits: (user as any).refCredits ?? 0,
            referralBonusAwarded: (user as any).referralBonusAwarded ?? false
          }
        }
      );
      updated++;
    }
    return updated;
  }
}

export const userRepository = new UserRepository();
