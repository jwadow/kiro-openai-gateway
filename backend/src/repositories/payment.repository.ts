import { Payment, IPayment, PaymentStatus, generateOrderCode, PROFIT_VND_PER_USD, PROFIT_CUTOFF_DATE } from '../models/payment.model.js';

// Profit cutoff date for calculation (Vietnam timezone UTC+7)
const PROFIT_CUTOFF = new Date(PROFIT_CUTOFF_DATE);

export class PaymentRepository {
  async create(data: {
    userId: string;
    discordId?: string;
    username?: string;
    credits: number;
    amount: number;
  }): Promise<IPayment> {
    const orderCode = generateOrderCode(data.credits);
    const expiresAt = new Date(Date.now() + 15 * 60 * 1000); // 15 minutes

    const payment = await Payment.create({
      userId: data.userId,
      discordId: data.discordId,
      username: data.username,
      credits: data.credits,
      amount: data.amount,
      currency: 'VND',
      orderCode,
      paymentMethod: 'sepay',
      status: 'pending',
      expiresAt,
    });
    return payment.toObject();
  }

  async findById(id: string): Promise<IPayment | null> {
    return Payment.findById(id).lean();
  }

  async findByOrderCode(orderCode: string): Promise<IPayment | null> {
    return Payment.findOne({ orderCode }).lean();
  }

  async findPendingByOrderCodePattern(pattern: string): Promise<IPayment | null> {
    return Payment.findOne({
      orderCode: { $regex: pattern, $options: 'i' },
      status: 'pending',
    }).lean();
  }

  async updateStatus(
    id: string,
    status: PaymentStatus,
    transactionId?: string
  ): Promise<IPayment | null> {
    const update: any = { status };
    if (status === 'success') {
      update.completedAt = new Date();
    }
    if (transactionId) {
      update.sepayTransactionId = transactionId;
    }
    return Payment.findByIdAndUpdate(id, update, { new: true }).lean();
  }

  async markExpired(id: string): Promise<IPayment | null> {
    return Payment.findByIdAndUpdate(
      id,
      { status: 'expired' },
      { new: true }
    ).lean();
  }

  async findByUserId(userId: string, limit: number = 20): Promise<IPayment[]> {
    return Payment.find({ userId })
      .sort({ createdAt: -1 })
      .limit(limit)
      .lean();
  }

  async checkAndExpire(paymentId: string): Promise<IPayment | null> {
    const payment = await Payment.findById(paymentId).lean();
    if (!payment) return null;
    
    if (payment.status === 'pending' && new Date() > payment.expiresAt) {
      return this.markExpired(paymentId);
    }
    return payment;
  }

  async getAllPayments(options: {
    page?: number;
    limit?: number;
    status?: PaymentStatus;
    since?: Date;
    until?: Date;
  } = {}): Promise<{ payments: Array<IPayment & { profitVND?: number }>; total: number; page: number; totalPages: number }> {
    const { page = 1, limit = 20, status, since, until } = options;
    const skip = (page - 1) * limit;

    const query: any = {};
    if (status) {
      query.status = status;
    }
    if (since || until) {
      query.createdAt = {};
      if (since) query.createdAt.$gte = since;
      if (until) query.createdAt.$lte = until;
    }

    // Use aggregation to add profit calculation field
    const [payments, total] = await Promise.all([
      Payment.aggregate([
        { $match: query },
        { $sort: { createdAt: -1 } },
        { $skip: skip },
        { $limit: limit },
        {
          $addFields: {
            // Calculate profit only for successful payments completed after cutoff date
            // Profit = credits * PROFIT_VND_PER_USD
            profitVND: {
              $cond: [
                {
                  $and: [
                    { $eq: ['$status', 'success'] },
                    { $gte: ['$completedAt', PROFIT_CUTOFF] }
                  ]
                },
                { $multiply: ['$credits', PROFIT_VND_PER_USD] },
                0
              ]
            }
          }
        }
      ]),
      Payment.countDocuments(query),
    ]);

    return {
      payments,
      total,
      page,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getUserPaymentStats(userId: string): Promise<{
    totalCredits: number;
    totalVND: number;
    successCount: number;
    pendingCount: number;
    failedCount: number;
  }> {
    const [stats] = await Payment.aggregate([
      { $match: { userId } },
      {
        $group: {
          _id: null,
          totalCredits: {
            $sum: { $cond: [{ $eq: ['$status', 'success'] }, '$credits', 0] }
          },
          totalVND: {
            $sum: { $cond: [{ $eq: ['$status', 'success'] }, '$amount', 0] }
          },
          successCount: {
            $sum: { $cond: [{ $eq: ['$status', 'success'] }, 1, 0] }
          },
          pendingCount: {
            $sum: { $cond: [{ $eq: ['$status', 'pending'] }, 1, 0] }
          },
          failedCount: {
            $sum: { $cond: [{ $in: ['$status', ['failed', 'expired']] }, 1, 0] }
          },
        },
      },
    ]);

    return stats || { totalCredits: 0, totalVND: 0, successCount: 0, pendingCount: 0, failedCount: 0 };
  }

  async findByUserIdPaginated(
    userId: string,
    options: {
      page?: number;
      limit?: number;
      status?: PaymentStatus;
      from?: Date;
      to?: Date;
    } = {}
  ): Promise<{ payments: IPayment[]; total: number; page: number; totalPages: number }> {
    const { page = 1, limit = 20, status, from, to } = options;
    const skip = (page - 1) * limit;

    const query: any = { userId };
    if (status) {
      query.status = status;
    }
    if (from || to) {
      query.createdAt = {};
      if (from) query.createdAt.$gte = from;
      if (to) query.createdAt.$lte = to;
    }

    const [payments, total] = await Promise.all([
      Payment.find(query)
        .sort({ createdAt: -1 })
        .skip(skip)
        .limit(limit)
        .lean(),
      Payment.countDocuments(query),
    ]);

    return {
      payments,
      total,
      page,
      totalPages: Math.ceil(total / limit),
    };
  }

  async getPaymentStats(since?: Date, until?: Date): Promise<{
    totalAmount: number;
    successCount: number;
    pendingCount: number;
    failedCount: number;
    totalProfit: number;
  }> {
    const query: any = {};
    if (since || until) {
      query.createdAt = {};
      if (since) query.createdAt.$gte = since;
      if (until) query.createdAt.$lte = until;
    }

    const [stats] = await Payment.aggregate([
      { $match: query },
      {
        $group: {
          _id: null,
          totalAmount: {
            $sum: { $cond: [{ $eq: ['$status', 'success'] }, '$amount', 0] }
          },
          successCount: {
            $sum: { $cond: [{ $eq: ['$status', 'success'] }, 1, 0] }
          },
          pendingCount: {
            $sum: { $cond: [{ $eq: ['$status', 'pending'] }, 1, 0] }
          },
          failedCount: {
            $sum: { $cond: [{ $in: ['$status', ['failed', 'expired']] }, 1, 0] }
          },
          // Calculate profit only for successful payments completed after cutoff date
          // Profit = credits * PROFIT_VND_PER_USD
          totalProfit: {
            $sum: {
              $cond: [
                {
                  $and: [
                    { $eq: ['$status', 'success'] },
                    { $gte: ['$completedAt', PROFIT_CUTOFF] }
                  ]
                },
                { $multiply: ['$credits', PROFIT_VND_PER_USD] },
                0
              ]
            }
          },
        },
      },
    ]);

    return stats || { totalAmount: 0, successCount: 0, pendingCount: 0, failedCount: 0, totalProfit: 0 };
  }
}

export const paymentRepository = new PaymentRepository();
