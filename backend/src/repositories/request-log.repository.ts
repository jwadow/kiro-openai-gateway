import { RequestLog, IRequestLog } from '../models/request-log.model.js';

export interface CreateRequestLogData {
  userId?: string;
  userKeyId: string;
  factoryKeyId: string;
  model?: string;
  inputTokens?: number;
  outputTokens?: number;
  cacheWriteTokens?: number;
  cacheHitTokens?: number;
  creditsCost?: number;
  tokensUsed: number;
  statusCode: number;
  latencyMs?: number;
  isSuccess?: boolean;
}

export interface RequestHistoryQuery {
  userId: string;
  page?: number;
  limit?: number;
  from?: Date;
  to?: Date;
  friendKeyOnly?: boolean;
}

export interface RequestHistoryResult {
  requests: IRequestLog[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

export class RequestLogRepository {
  async create(data: CreateRequestLogData): Promise<IRequestLog> {
    const log = await RequestLog.create({
      ...data,
      isSuccess: data.isSuccess ?? (data.statusCode >= 200 && data.statusCode < 300),
    });
    return log.toObject();
  }

  async findByUserKey(userKeyId: string, limit: number = 100): Promise<IRequestLog[]> {
    return RequestLog.find({ userKeyId })
      .sort({ createdAt: -1 })
      .limit(limit)
      .lean();
  }

  async findByFactoryKey(factoryKeyId: string, limit: number = 100): Promise<IRequestLog[]> {
    return RequestLog.find({ factoryKeyId })
      .sort({ createdAt: -1 })
      .limit(limit)
      .lean();
  }

  async findByUserId(query: RequestHistoryQuery): Promise<RequestHistoryResult> {
    const { userId, page = 1, limit = 20, from, to, friendKeyOnly } = query;
    const safeLimit = Math.min(Math.max(1, limit), 100);
    const safePage = Math.max(1, page);
    const skip = (safePage - 1) * safeLimit;

    const filter: any = { userId };
    if (from || to) {
      filter.createdAt = {};
      if (from) filter.createdAt.$gte = from;
      if (to) filter.createdAt.$lte = to;
    }
    if (friendKeyOnly) {
      filter.friendKeyId = { $exists: true, $ne: null };
    }

    const [requests, total] = await Promise.all([
      RequestLog.find(filter)
        .sort({ createdAt: -1 })
        .skip(skip)
        .limit(safeLimit)
        .lean(),
      RequestLog.countDocuments(filter),
    ]);

    return {
      requests,
      total,
      page: safePage,
      limit: safeLimit,
      totalPages: Math.ceil(total / safeLimit),
    };
  }

  async getMetrics(since?: Date): Promise<{
    totalRequests: number;
    tokensUsed: number;
    avgLatencyMs: number;
    successRate: number;
  }> {
    const match = since ? { createdAt: { $gte: since } } : {};
    
    const result = await RequestLog.aggregate([
      { $match: match },
      {
        $group: {
          _id: null,
          totalRequests: { $sum: 1 },
          tokensUsed: { $sum: '$tokensUsed' },
          avgLatencyMs: { $avg: '$latencyMs' },
          successCount: { $sum: { $cond: ['$isSuccess', 1, 0] } },
        },
      },
    ]);

    if (result.length === 0) {
      return { totalRequests: 0, tokensUsed: 0, avgLatencyMs: 0, successRate: 100 };
    }

    const { totalRequests, tokensUsed, avgLatencyMs, successCount } = result[0];
    const successRate = totalRequests > 0 ? (successCount / totalRequests) * 100 : 100;

    return {
      totalRequests,
      tokensUsed,
      avgLatencyMs: Math.round(avgLatencyMs || 0),
      successRate: Math.round(successRate * 100) / 100,
    };
  }

  async getTokenAnalytics(factoryKeyId?: string): Promise<{
    last1h: number;
    last24h: number;
    last7d: number;
  }> {
    const now = new Date();
    const hour1 = new Date(now.getTime() - 60 * 60 * 1000);
    const hours24 = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    const days7 = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    const match: any = {};
    if (factoryKeyId) match.factoryKeyId = factoryKeyId;

    const [h1, h24, d7] = await Promise.all([
      RequestLog.aggregate([
        { $match: { ...match, createdAt: { $gte: hour1 } } },
        { $group: { _id: null, total: { $sum: '$tokensUsed' } } },
      ]),
      RequestLog.aggregate([
        { $match: { ...match, createdAt: { $gte: hours24 } } },
        { $group: { _id: null, total: { $sum: '$tokensUsed' } } },
      ]),
      RequestLog.aggregate([
        { $match: { ...match, createdAt: { $gte: days7 } } },
        { $group: { _id: null, total: { $sum: '$tokensUsed' } } },
      ]),
    ]);

    return {
      last1h: h1[0]?.total || 0,
      last24h: h24[0]?.total || 0,
      last7d: d7[0]?.total || 0,
    };
  }

  async getCreditsUsageByPeriod(userId?: string): Promise<{
    last1h: number;
    last24h: number;
    last7d: number;
    last30d: number;
  }> {
    const now = new Date();
    const hour1 = new Date(now.getTime() - 60 * 60 * 1000);
    const hours24 = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    const days7 = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const days30 = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    const match: any = {};
    if (userId) match.userId = userId;

    const [h1, h24, d7, d30] = await Promise.all([
      RequestLog.aggregate([
        { $match: { ...match, createdAt: { $gte: hour1 } } },
        { $group: { _id: null, total: { $sum: '$creditsCost' } } },
      ]),
      RequestLog.aggregate([
        { $match: { ...match, createdAt: { $gte: hours24 } } },
        { $group: { _id: null, total: { $sum: '$creditsCost' } } },
      ]),
      RequestLog.aggregate([
        { $match: { ...match, createdAt: { $gte: days7 } } },
        { $group: { _id: null, total: { $sum: '$creditsCost' } } },
      ]),
      RequestLog.aggregate([
        { $match: { ...match, createdAt: { $gte: days30 } } },
        { $group: { _id: null, total: { $sum: '$creditsCost' } } },
      ]),
    ]);

    return {
      last1h: h1[0]?.total || 0,
      last24h: h24[0]?.total || 0,
      last7d: d7[0]?.total || 0,
      last30d: d30[0]?.total || 0,
    };
  }

  async getTotalCreditsBurned(since?: Date): Promise<number> {
    const match = since ? { createdAt: { $gte: since } } : {};
    const result = await RequestLog.aggregate([
      { $match: match },
      { $group: { _id: null, total: { $sum: '$creditsCost' } } },
    ]);
    return result[0]?.total || 0;
  }

  async getCreditsBurnedByUser(): Promise<Record<string, number>> {
    const result = await RequestLog.aggregate([
      { $group: { _id: '$userId', total: { $sum: '$creditsCost' } } },
    ]);
    const map: Record<string, number> = {};
    result.forEach((r) => {
      if (r._id) map[r._id] = r.total || 0;
    });
    return map;
  }

  async getDetailedUsageByPeriod(userId: string, period: '1h' | '24h' | '7d' | '30d' = '24h'): Promise<{
    inputTokens: number;
    outputTokens: number;
    cacheWriteTokens: number;
    cacheHitTokens: number;
    creditsBurned: number;
    requestCount: number;
  }> {
    const now = new Date();
    const periodMs: Record<string, number> = {
      '1h': 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
      '30d': 30 * 24 * 60 * 60 * 1000,
    };
    const since = new Date(now.getTime() - periodMs[period]);

    const result = await RequestLog.aggregate([
      { $match: { userId, createdAt: { $gte: since } } },
      {
        $group: {
          _id: null,
          inputTokens: { $sum: { $ifNull: ['$inputTokens', 0] } },
          outputTokens: { $sum: { $ifNull: ['$outputTokens', 0] } },
          cacheWriteTokens: { $sum: { $ifNull: ['$cacheWriteTokens', 0] } },
          cacheHitTokens: { $sum: { $ifNull: ['$cacheHitTokens', 0] } },
          creditsBurned: { $sum: { $ifNull: ['$creditsCost', 0] } },
          requestCount: { $sum: 1 },
        },
      },
    ]);

    if (result.length === 0) {
      return {
        inputTokens: 0,
        outputTokens: 0,
        cacheWriteTokens: 0,
        cacheHitTokens: 0,
        creditsBurned: 0,
        requestCount: 0,
      };
    }

    return {
      inputTokens: result[0].inputTokens || 0,
      outputTokens: result[0].outputTokens || 0,
      cacheWriteTokens: result[0].cacheWriteTokens || 0,
      cacheHitTokens: result[0].cacheHitTokens || 0,
      creditsBurned: result[0].creditsBurned || 0,
      requestCount: result[0].requestCount || 0,
    };
  }

  async getRequestLogsByPeriod(
    userId: string,
    period: '1h' | '24h' | '7d' | '30d' = '24h',
    page: number = 1,
    limit: number = 50
  ): Promise<{
    requests: {
      id: string;
      model: string;
      upstream: string;
      inputTokens: number;
      outputTokens: number;
      cacheWriteTokens: number;
      cacheHitTokens: number;
      creditsCost: number;
      latencyMs: number;
      isSuccess: boolean;
      createdAt: Date;
    }[];
    total: number;
    page: number;
    limit: number;
    totalPages: number;
  }> {
    const now = new Date();
    const periodMs: Record<string, number> = {
      '1h': 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
      '30d': 30 * 24 * 60 * 60 * 1000,
    };
    const since = new Date(now.getTime() - periodMs[period]);
    const skip = (page - 1) * limit;

    const filter = { userId, createdAt: { $gte: since } };

    const [requests, total] = await Promise.all([
      RequestLog.find(filter)
        .sort({ createdAt: -1 })
        .skip(skip)
        .limit(limit)
        .lean(),
      RequestLog.countDocuments(filter),
    ]);

    return {
      requests: requests.map((r) => ({
        id: r._id?.toString() || '',
        model: r.model || 'unknown',
        upstream: r.upstream || ((r as any).trollKeyId?.toLowerCase().includes('openhands') ? 'openhands' : 'main'),
        inputTokens: r.inputTokens || 0,
        outputTokens: r.outputTokens || 0,
        cacheWriteTokens: r.cacheWriteTokens || 0,
        cacheHitTokens: r.cacheHitTokens || 0,
        creditsCost: r.creditsCost || 0,
        latencyMs: r.latencyMs || 0,
        isSuccess: r.isSuccess,
        createdAt: r.createdAt,
      })),
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getModelStats(since?: Date): Promise<{
    model: string;
    inputTokens: number;
    outputTokens: number;
    cacheWriteTokens: number;
    cacheHitTokens: number;
    totalTokens: number;
    creditsBurned: number;
    requestCount: number;
  }[]> {
    const match: any = { model: { $exists: true, $ne: null } };
    if (since) {
      match.createdAt = { $gte: since };
    }

    const result = await RequestLog.aggregate([
      { $match: match },
      {
        $group: {
          _id: '$model',
          inputTokens: { $sum: { $ifNull: ['$inputTokens', 0] } },
          outputTokens: { $sum: { $ifNull: ['$outputTokens', 0] } },
          cacheWriteTokens: { $sum: { $ifNull: ['$cacheWriteTokens', 0] } },
          cacheHitTokens: { $sum: { $ifNull: ['$cacheHitTokens', 0] } },
          creditsBurned: { $sum: { $ifNull: ['$creditsCost', 0] } },
          requestCount: { $sum: 1 },
        },
      },
      {
        $addFields: {
          totalTokens: {
            $add: ['$inputTokens', '$outputTokens', '$cacheWriteTokens', '$cacheHitTokens']
          },
        },
      },
      { $sort: { totalTokens: -1 } },
    ]);

    return result.map((r) => ({
      model: r._id || 'unknown',
      inputTokens: r.inputTokens || 0,
      outputTokens: r.outputTokens || 0,
      cacheWriteTokens: r.cacheWriteTokens || 0,
      cacheHitTokens: r.cacheHitTokens || 0,
      totalTokens: r.totalTokens || 0,
      creditsBurned: r.creditsBurned || 0,
      requestCount: r.requestCount || 0,
    }));
  }

  async getLastActivityByUser(): Promise<Record<string, Date>> {
    const result = await RequestLog.aggregate([
      { $match: { userId: { $exists: true, $ne: null } } },
      { $sort: { createdAt: -1 } },
      { $group: { _id: '$userId', lastActivity: { $first: '$createdAt' } } },
    ]);
    const map: Record<string, Date> = {};
    result.forEach((r) => {
      if (r._id) map[r._id] = r.lastActivity;
    });
    return map;
  }

  async getRateLimitMetrics(since?: Date): Promise<{
    total429: number;
    userKey429: number;
    friendKey429: number;
  }> {
    const match: any = { statusCode: 429 };
    if (since) {
      match.createdAt = { $gte: since };
    }

    const result = await RequestLog.aggregate([
      { $match: match },
      {
        $group: {
          _id: {
            $cond: [
              { $and: [{ $ne: ['$friendKeyId', null] }, { $ne: ['$friendKeyId', ''] }] },
              'friendKey',
              'userKey'
            ]
          },
          count: { $sum: 1 }
        }
      }
    ]);

    let userKey429 = 0;
    let friendKey429 = 0;

    result.forEach((r) => {
      if (r._id === 'userKey') userKey429 = r.count;
      if (r._id === 'friendKey') friendKey429 = r.count;
    });

    return {
      total429: userKey429 + friendKey429,
      userKey429,
      friendKey429,
    };
  }
}

export const requestLogRepository = new RequestLogRepository();
