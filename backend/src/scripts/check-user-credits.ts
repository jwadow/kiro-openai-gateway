import mongoose from 'mongoose';
import dotenv from 'dotenv';

dotenv.config();

const MONGODB_URI = process.env.MONGODB_URI || '';
const MONGODB_DB_NAME = process.env.MONGODB_DB_NAME || 'fproxy';

async function checkUserCredits(username: string) {
  try {
    await mongoose.connect(MONGODB_URI, { dbName: MONGODB_DB_NAME });
    console.log('Connected to MongoDB');

    const db = mongoose.connection.db;
    if (!db) {
      throw new Error('Database connection not established');
    }

    // 1. Check user in usersNew
    console.log('\n========== USER INFO ==========');
    const user = await db.collection('usersNew').findOne({ _id: username } as any);
    if (user) {
      console.log('Username:', user._id);
      console.log('Credits:', user.credits);
      console.log('Credits Used:', user.creditsUsed);
      console.log('Ref Credits:', user.refCredits);
      console.log('Is Active:', user.isActive);
      console.log('Plan:', user.plan);
      console.log('Created At:', user.createdAt);
    } else {
      console.log('User not found!');
    }

    // 2. Check payments for this user
    console.log('\n========== PAYMENTS ==========');
    const payments = await db.collection('payments')
      .find({ userId: username })
      .sort({ createdAt: -1 })
      .limit(10)
      .toArray();

    if (payments.length > 0) {
      let totalPaid = 0;
      payments.forEach((p, i) => {
        console.log(`\n[${i + 1}] Payment ID: ${p._id}`);
        console.log('   Amount:', p.amount, p.currency || 'VND');
        console.log('   Credits Added:', p.creditsAdded);
        console.log('   Status:', p.status);
        console.log('   Date:', p.createdAt);
        if (p.status === 'completed') {
          totalPaid += p.creditsAdded || 0;
        }
      });
      console.log('\nTotal Credits from Payments:', totalPaid);
    } else {
      console.log('No payments found');
    }

    // 3. Check friend keys owned by this user
    console.log('\n========== FRIEND KEYS ==========');
    const friendKeys = await db.collection('friendkeys')
      .find({ ownerId: username })
      .toArray();

    if (friendKeys.length > 0) {
      friendKeys.forEach((fk, i) => {
        console.log(`\n[${i + 1}] Friend Key: ${String(fk._id).substring(0, 30)}...`);
        console.log('   Is Active:', fk.isActive);
        console.log('   Total Used USD:', fk.totalUsedUsd);
        console.log('   Requests Count:', fk.requestsCount);
        console.log('   Last Used:', fk.lastUsedAt);
        if (fk.modelLimits) {
          console.log('   Model Limits:');
          fk.modelLimits.forEach((ml: any) => {
            console.log(`     - ${ml.modelId}: $${ml.usedUsd?.toFixed(4) || 0} / $${ml.limitUsd}`);
          });
        }
      });
    } else {
      console.log('No friend keys found');
    }

    // 4. Check recent request logs
    console.log('\n========== RECENT REQUEST LOGS (Last 20) ==========');
    const logs = await db.collection('requestlogs')
      .find({ userId: username })
      .sort({ createdAt: -1 })
      .limit(20)
      .toArray();

    if (logs.length > 0) {
      let totalCost = 0;
      logs.forEach((log, i) => {
        console.log(`\n[${i + 1}] ${log.createdAt}`);
        console.log('   Model:', log.modelId);
        console.log('   Input:', log.inputTokens, '| Output:', log.outputTokens);
        console.log('   Cache Write:', log.cacheWriteTokens || 0, '| Cache Hit:', log.cacheHitTokens || 0);
        console.log('   Credits Cost: $', log.creditsCost?.toFixed(6) || 0);
        totalCost += log.creditsCost || 0;
      });
      console.log('\n--- Total from last 20 requests: $', totalCost.toFixed(4));
    } else {
      console.log('No request logs found');
    }

    // 5. Aggregate total credits used from all request logs
    console.log('\n========== TOTAL CREDITS FROM ALL LOGS ==========');
    const totalFromLogs = await db.collection('requestlogs').aggregate([
      { $match: { userId: username } },
      { $group: {
        _id: null,
        totalCost: { $sum: { $ifNull: ['$creditsCost', 0] } },
        totalRequests: { $sum: 1 }
      }}
    ]).toArray();

    if (totalFromLogs.length > 0) {
      console.log('Total Requests:', totalFromLogs[0].totalRequests);
      console.log('Total Credits Cost from Logs: $', totalFromLogs[0].totalCost?.toFixed(4));
    }

    // 6. Summary and Analysis
    console.log('\n========== ANALYSIS ==========');
    if (user) {
      const currentCredits = user.credits || 0;
      const creditsUsed = user.creditsUsed || 0;
      const totalPaid = payments.reduce((sum, p) => sum + (p.status === 'completed' ? (p.creditsAdded || 0) : 0), 0);
      const friendKeyUsage = friendKeys.reduce((sum, fk) => sum + (fk.totalUsedUsd || 0), 0);
      const logsTotal = totalFromLogs.length > 0 ? totalFromLogs[0].totalCost : 0;

      console.log('Expected Credits = Total Paid - Credits Used');
      console.log(`Expected: $${totalPaid} - $${creditsUsed.toFixed(4)} = $${(totalPaid - creditsUsed).toFixed(4)}`);
      console.log(`Actual Credits: $${currentCredits.toFixed(4)}`);
      console.log(`Difference: $${(currentCredits - (totalPaid - creditsUsed)).toFixed(4)}`);
      console.log('');
      console.log('Friend Key Total Usage: $', friendKeyUsage.toFixed(4));
      console.log('Request Logs Total: $', logsTotal?.toFixed(4));
      console.log('User creditsUsed field: $', creditsUsed.toFixed(4));

      if (Math.abs(logsTotal - creditsUsed) > 0.01) {
        console.log('\n⚠️  WARNING: creditsUsed does not match sum of request logs!');
        console.log('   This could indicate a bug in deduction logic.');
      }
    }

  } catch (error) {
    console.error('Error:', error);
  } finally {
    await mongoose.disconnect();
  }
}

// Run with username from command line
const username = process.argv[2] || 'longcachep';
console.log(`Checking credits for user: ${username}\n`);
checkUserCredits(username);
